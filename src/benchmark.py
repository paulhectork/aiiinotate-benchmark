import shutil
import random
from itertools import chain
from datetime import datetime
from typing import List, Tuple, Dict
from timeit import default_timer as timer

from .utils import pprint, write_log, get_manifest_short_id
from .adapter_sas import AdapterSas
from .adapter_aiiinotate import AdapterAiiinotate
from .adapter_core import AdapterCore, validate_endpoint
from .multithread import mt_insert_manifests, mt_insert_annotations, mt_delete
from .constants import STEPS_GROUP, STEPS_FLAT, STEPS_GROUP_RANGE, RATIO_DEFAULT, N_STEPS_DEFAULT, THREADS_DEFAULT
from .generate import generate_annotations, generate_annotation_lists, generate_manifests


def validate_threads(threads: int|None):
    if not isinstance(threads, int) or threads < 1:
        raise ValueError(f"validate_threads: 'threads' but be an integer >= 1, got {threads} (type {type(threads)})")

def validate_n_steps(n_steps: int):
    if (
        (not isinstance(n_steps, int))
        or n_steps < STEPS_GROUP_RANGE[0]
        or n_steps > STEPS_GROUP_RANGE[1]
    ):
        raise ValueError(f"validate_n_steps: 'steps' must be an integer, with steps in {STEPS_GROUP_RANGE}, got '{n_steps}'" )

def validate_server(server:str) -> None:
    if server not in ["aiiinotate", "sas"]:
        raise TypeError(f"validate_adapter: server '{server}' must be one of ['aiiinotate', 'sas']")
    return

def validate_ratio(r) -> None:
    if r is not None:
        if not isinstance(r, float) or not (r>0 and r<=1):
            raise ValueError(f"validate_ratio: ratio must be a float in range 0..1, got '{r}' (type {type('r')})")
    return

def validate_nowrite(nowrite) -> None:
    if not isinstance(nowrite, bool):
        raise TypeError(f"validate_nowrite: 'nowrite' must be bool, got {nowrite} (type={type(nowrite)})")

class Benchmark:
    def __init__(
        self,
        endpoint: str,
        server: str,
        n_steps: int = N_STEPS_DEFAULT,
        ratio: float|None = RATIO_DEFAULT,
        threads: int|None = THREADS_DEFAULT,
        nowrite: bool = False,
    ):
        """
        :param steps: steps of the benchmark, i.e [ (<step 1: number of manifests>, <step 1  number of canvases / manifest>), (<step 2: # manifests>, <step 2 # canvases / manifest>), ... ]
        :param adapter: an adapter inheriting from 'AdapterCore'
        :param ratio: ratio of canvases with annotations / canvases without annotations
        """
        validate_ratio(ratio)
        validate_n_steps(n_steps)
        validate_server(server)
        validate_endpoint(endpoint)
        validate_threads(threads)
        validate_nowrite(nowrite)

        adapter: AdapterCore
        if server == "aiiinotate":
            adapter = AdapterAiiinotate(endpoint)
        else:
            adapter = AdapterSas(endpoint)

        # STEPS_GROUP is used to count steps in the CLI, STEPS_FLAT is actually used for the benchmark
        # => select the values in STEPS_FLAT based on `n_steps`
        #n_steps += 1
        steps: list = STEPS_FLAT[:3*n_steps]

        self.adapter = adapter
        self.steps = steps
        self.ratio = ratio if ratio is not None else RATIO_DEFAULT  # ratio of canvases that will have annotations. 0.01 = 1 in 100 canvases in a manifest will have annotations.
        self.threads = threads
        self.nowrite = nowrite

        self.n_annotation = 1000  # number of annotations per canvas.
        self.n_iterations = 50  # number of iterations for read benchmarking: we will run read queries `n` times and then get the average time for a single query.

        self.step_current = {}
        self.log = {
            "server_name": self.adapter.server_name,
            "n_steps": 3 * n_steps,
            "threads": self.threads,
            "n_iterations": self.n_iterations,
            "ratio_canvas_with_annotations": self.ratio,
            "time_unit": "seconds",
            "results": []
        }

    def step_to_dict(self, idx_step: int, step: Tuple[int,int]) -> Dict:
        n_canvas, n_manifest = step
        return {
            "index": idx_step,
            "n_manifest": step[0],
            "n_canvas": step[1],
            "n_annotations": self.n_annotation * round(n_canvas * self.ratio) * n_manifest,
            "n_annotation_per_canvas": self.n_annotation,
        }

    def sample_for_iteration(self, list_:List) -> List:
        """
        sample a list to randomly select `self.n_iterations` values, or return the whole list if it's smaller than `self.n_iterations`.
        """
        #NOTE: THIS WILL BREAK THE BENCHMARKS if using it in benchmarks that are running several iterations, if `self.n_iterations > len(list_)`: average calculation will be broken !
        return random.sample(list_, min(self.n_iterations, len(list_)))

    def populate(self):
        """
        before starting the benchmark, insert annotations and annotation lists to the server.
        NOTE: this isn't really a step of the benchmark as much as it is a preparatory step, but we log times just in case.
            in more detail: in Aiiinotate, a big insert bottleneck is to fetch the manifest for each annotation's target, index the manifest and get annotation's canvas index, which we can't replicate.
        """
        n_manifest = self.step_current["n_manifest"]  # pyright:ignore
        n_canvas = self.step_current["n_canvas"]  # pyright:ignore

        # insert manifests
        s = timer()
        # `mt_insert_manifests` returns a list of all canvas IDs of all the manifests inserted.
        list_id_canvas = mt_insert_manifests(
            func=self.adapter.insert_manifest,
            n=n_manifest,
            threads=self.threads,
            pbar_desc=f"inserting {n_manifest} manifests with {n_canvas} canvases (threads={self.threads})",
            n_manifest=n_manifest,
            n_canvas=n_canvas,
        )
        e = timer()
        d_populate_manifest = e-s
        assert len(list_id_canvas) != 0

        # insert annotations
        # first, we randomly sample `list_id_canvas` to select the canvases on which we'll work.
        # NOTE: list_id_canvas MUST be sampled here (and not in a worker thread) to avoid the same canvas to be sampled twice in separate threads
        list_id_canvas_full = list_id_canvas
        list_id_canvas_sample = random.sample(
            list_id_canvas,
            round(len(list_id_canvas) * self.ratio)
        )
        s = timer()
        # `mt_insert_annotations` returns the list of canvas IDs on which annotations were inserted (should be the same as `list_id_canvas_sampled`)
        list_id_canvas_annotations = mt_insert_annotations(
            func=self.adapter.insert_annotation_list,
            data=list_id_canvas_sample,
            n_annotation=self.n_annotation,
            threads=self.threads,
            pbar_desc=f"inserting {self.n_annotation * len(list_id_canvas_sample)} annotations on {len(list_id_canvas_sample)} canvases (threads={self.threads})"
        )
        e = timer()
        d_populate_annotation = e-s
        # NOTE: there's always an error in SAS insertions, so the check below fails.
        # assert len(list_id_canvas_sample) == len(list_id_canvas_annotations)
        return d_populate_manifest, d_populate_annotation, list_id_canvas_full, list_id_canvas_annotations

    def get_annotations_for_canvases(self, list_id_canvas: List[str]):
        """
        get all annotations on canvases whose @ids are in `list_id_canvas`
        """
        list_annotations = []
        for id_canvas in list_id_canvas:
            # SAS returns Annotation[], while aiiinotate returns an AnnotationList.
            annotations_data = self.adapter.get_annotation_list(id_canvas)
            if self.adapter.server_name == "Aiiinotate":
                list_annotations.extend(annotations_data["resources"])
            else:
                list_annotations.extend(annotations_data)
        return list_annotations


    def read(self, list_id_canvas:List[str]):
        """
        read time benchmarks

        :param list_id_canvas: canvases containing annotations
        """
        list_id_canvas = self.sample_for_iteration(list_id_canvas)

        s = timer()
        list_annotations = self.get_annotations_for_canvases(list_id_canvas)
        e = timer()
        d_read_annotation_list = (e-s) / self.n_iterations

        d_read_annotation = None
        if self.adapter.server_name == "Aiiinotate":
            # list of randomly selected annotation @ids.
            list_id_annotation = [
                random.choice(list_annotations)["@id"]
                for _ in range(self.n_iterations)
            ]
            s = timer()
            for id_annotation in list_id_annotation:
                annotation = self.adapter.get_annotation(id_annotation)  # pyright: ignore
                assert "@id" in annotation.keys() and annotation["@id"] == id_annotation
            e = timer()
            d_read_annotation = (e-s) / self.n_iterations

        return d_read_annotation_list, d_read_annotation

    def write(self) -> Tuple[float, float, float|None]:
        """
        write time benchmarks
        """
        list_id_canvas = []
        generator_manifest = generate_manifests(self.n_iterations, self.step_current["n_canvas"])
        s = timer()
        for manifest in generator_manifest:
            canvases = self.adapter.insert_manifest(manifest)
            list_id_canvas.extend(canvases)
        e = timer()
        d_write_manifest = (e-s) / self.n_iterations

        generator_annotation = generate_annotations(random.sample(list_id_canvas, self.n_iterations))
        s = timer()
        for annotation in generator_annotation:
            self.adapter.insert_annotation(annotation)
        e = timer()
        d_write_annotation = (e-s) / self.n_iterations

        d_write_annotation_list = None
        if self.adapter.server_name == "Aiiinotate":
            generator_annotation_list = generate_annotation_lists(
                self.sample_for_iteration(list_id_canvas),
                self.n_annotation
            )
            s = timer()
            for annotation_list in generator_annotation_list:
                self.adapter.insert_annotation_list(annotation_list)
            e = timer()
            d_write_annotation_list = (e-s) / self.n_iterations

        return d_write_manifest, d_write_annotation, d_write_annotation_list

    def update(self, list_id_canvas: List[str]):
        """
        update time benchmarks
        """
        list_id_canvas = self.sample_for_iteration(list_id_canvas)
        # we must convert the generator to a list in order to access its contents twice
        list_annotation = [
            annotation for annotation in generate_annotations(list_id_canvas)
        ]
        for annotation in list_annotation:
            self.adapter.insert_annotation(annotation)
        s = timer()
        for annotation in list_annotation:
            print("hello !!!!!!!!!!!!!!!")
            print(annotation)
            self.adapter.update_annotation(annotation)
        e = timer()
        d_update_annotation = (e-s) / self.n_iterations

        return d_update_annotation


    def purge(self):
        """
        at the end of a step, delete all contents from a db.
        """
        if self.adapter.server_name == "Aiiinotate":
            self.adapter.purge()  # pyright: ignore
        else:
            self.adapter.purge(self.threads)  # pyright: ignore
        return

    def step(self, idx_step:int, step: Tuple[int,int]):
        """
        run a single step.

        :param idx_step: position of steps within `self.steps`
        :param step: [n_manifest, n_canvas]
        """
        list_id_canvas_annotations = []
        step_dict = self.step_to_dict(idx_step, step)
        self.step_current = step_dict
        log = {}
        log["step"] = step_dict

        t_width = shutil.get_terminal_size((80,20))[0]
        banner_start = f"\nSTART STEP #{idx_step}: {step_dict}\n{'*' * t_width}\n"
        banner_end = f"{'*' * t_width}\n"
        print(banner_start)

        try:
            d_populate_manifest, d_populate_annotation, list_id_canvas_full, list_id_canvas_annotations = self.populate()
            log["duration_populate_manifest"] = d_populate_manifest
            log["duration_populate_annotation"] = d_populate_annotation

            d_read_annotation_list, d_read_annotation = self.read(list_id_canvas_annotations)
            log["duration_read_annotation_list"] = d_read_annotation_list
            if d_read_annotation is not None:
                log["duration_read_annotation"] = d_read_annotation

            d_write_manifest, d_write_annotation, d_write_annotation_list = self.write()
            log["duration_write_manifest"] = d_write_manifest
            log["duration_write_annotation"] = d_write_annotation
            if d_write_annotation_list is not None:
                log["duration_write_annotation_list"] = d_write_annotation_list

            d_update_annotation = self.update(list_id_canvas_annotations)
            log["duration_update_annotation"] = d_update_annotation

        finally:
            self.purge()
            self.step_current = {}
            self.log["results"].append(log)
            print(f"\nSTEP #{idx_step} RESULTS:")
            pprint(log)
            print("")

        print(banner_end)
        return

    def run(self):
        def write():
            if not self.nowrite:
                write_log(self.adapter.server_name, len(self.steps), timestamp, self.log)
            return

        timestamp = datetime.now().strftime(r'%Y-%m-%d-%H:%M:%S')
        print("Global benchmark parameters:")
        pprint(self.log)
        try:
            for i, step in enumerate(self.steps):
                self.step(i, step)  # pyright: ignore
                write()
        finally:
                write()
        return

