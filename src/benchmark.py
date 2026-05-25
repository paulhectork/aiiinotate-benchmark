import shutil
import random
from itertools import chain
from datetime import datetime
from typing import List, Tuple, Dict
from timeit import default_timer as timer

from tqdm import tqdm

from src.utils import pprint, write_report, get_manifest_short_id
from src.adapter_sas import AdapterSas
from src.adapter_aiiinotate import AdapterAiiinotate
from src.adapter_core import AdapterCore, validate_endpoint
from src.multithread import mt_insert_manifests, mt_insert_annotations, mt_delete
from src.constants import STEPS, N_ITERATIONS, N_STEPS_DEFAULT, N_ANNOTATIONS_PER_CANVAS, THREADS_DEFAULT, RATIO
from src.generate import generate_annotations, generate_annotation_lists, generate_manifests, mkstr
from src.visualize import visualize

def validate_threads(threads: int|None):
    if not isinstance(threads, int) or threads < 1:
        raise ValueError(f"validate_threads: 'threads' but be an integer >= 1, got {threads} (type {type(threads)})")

def validate_n_steps(n_steps: int):
    min_ = 1
    max_ = len(STEPS)
    if (
        (not isinstance(n_steps, int))
        or n_steps < min_
        or n_steps > max_
    ):
        raise ValueError(f"validate_n_steps: 'steps' must be an integer, with steps in ({min_}, {max_}), got '{n_steps}'")

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
        threads: int|None = THREADS_DEFAULT,
        nowrite: bool = False,
    ):
        """
        view CLI help for info on the arguments.
        """
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

        steps = STEPS[:n_steps]

        self.adapter = adapter
        self.server_name = self.adapter.server_name
        self.server_is_aiiinotate = self.server_name == "aiiinotate"
        self.steps = steps
        self.threads = threads
        self.nowrite = nowrite

        self.ratio = RATIO  # annotation-to-canvas ratio
        self.n_annotation_per_canvas = N_ANNOTATIONS_PER_CANVAS  # number of annotations per canvas, if a canvas has annotations
        self.n_iterations = N_ITERATIONS  # number of iterations for read benchmarking: we will run read queries n times and then get the average time for a single query.

        self.step_current = {}
        self.report = {
            "server_name": self.server_name,
            "n_steps": n_steps,
            "n_threads": self.threads,
            "n_iterations": self.n_iterations,
            "n_annotation_per_canvas": self.n_annotation_per_canvas,
            "ratio_annotation_to_canvas": self.ratio,
            "time_unit": "seconds",
            "results": []
        }

    def step_to_dict(self, idx_step: int, step: Tuple[int,int]) -> Dict:
        n_manifest = step[0]
        n_canvas_per_manifest = step[1]
        n_annotation = int(n_manifest * n_canvas_per_manifest * self.ratio)
        n_canvas_total = n_manifest * n_canvas_per_manifest
        # if there are less annotations to insert than self.n_annotation_per_canvas,
        # just insert all annotations on a single canvas.
        n_canvas_with_annotations_per_manifest = (
            round(n_annotation / self.n_annotation_per_canvas)
            if n_annotation >= self.n_annotation_per_canvas
            else 1
        )
        return {
            "index": idx_step,
            "n_manifest": n_manifest,  # number of inserted manifests
            "n_annotation": n_annotation,  # number of annotation in total
            "n_canvas_total": n_canvas_total,  # number of canvases in total
            "n_canvas_per_manifest": n_canvas_per_manifest,  # number of canvases in each manifest
            "n_canvas_with_annotations_per_manifest": n_canvas_with_annotations_per_manifest,  # number of canvases that actually have annotations on them
        }

    def sample_for_iteration(self, list_:List) -> List:
        """
        sample a list to randomly select `self.n_iterations` values, or return the whole list if it's smaller than `self.n_iterations`.
        """
        #NOTE: THIS WILL BREAK THE BENCHMARKS if using it in benchmarks that are running several iterations, if `self.n_iterations > len(list_)`: average calculation will be broken !
        return random.sample(list_, min(self.n_iterations, len(list_)))

    def warmup(self):
        """
        before running the benchmark, insert a bunch of annotations to the
        AS to warm it up, then delete them.
        """
        n_manifest = 10_000
        n_canvas_per_manifest = 1000
        n_annotation = 100_000
        n_canvas_with_annotations_per_manifest = int(100_000 / self.n_annotation_per_canvas)

        list_id_canvas = mt_insert_manifests(
            func=self.adapter.insert_manifest,
            n=n_manifest,
            threads=self.threads,
            pbar_desc=f"warmup: inserting {n_manifest} manifests (threads={self.threads})",
            n_manifest=n_manifest,
            n_canvas=n_canvas_per_manifest,
        )
        list_id_canvas_sample = random.sample(
            list_id_canvas,
            n_canvas_with_annotations_per_manifest
        )
        mt_insert_annotations(
            func=self.adapter.insert_annotation_list,
            data=list_id_canvas_sample,
            n_annotation=self.n_annotation_per_canvas,
            threads=self.threads,
            pbar_desc=f"inserting {n_annotation} annotations on {len(list_id_canvas_sample)} canvases (threads={self.threads})"
        )
        self.purge()
        return self

    def populate(self):
        """
        before starting the benchmark, bulk insert annotations and annotation lists to the server.
        this isn't really a step of the benchmark, it is a preparatory step, but we report times just in case.
        in more detail: in Aiiinotate, a big insert bottleneck is to fetch the manifest for each annotation's
        target, index the manifest and get annotation's canvas index. we can't replicate this here, so the
        populate time is indicative.
        """
        n_manifest = self.step_current["n_manifest"]
        n_canvas_per_manifest = self.step_current["n_canvas_per_manifest"]
        n_annotation = self.step_current["n_annotation"]
        n_canvas_with_annotations_per_manifest = self.step_current["n_canvas_with_annotations_per_manifest"]

        # if the total number of annotations to be inserted at this step is lower than
        # self.n_annotation_per_canvas, then insert all annotations on a single canvas.
        # in this case,
        # - n_canvas_with_annotations_per_manifest = 1 (see `self.step_to_dict`)
        # - n_annotation_per_canvas = n_anotation (total number of annotations)
        step_n_annotation_per_canvas = (
            self.n_annotation_per_canvas
            if n_annotation >= self.n_annotation_per_canvas
            else n_annotation
        )

        # insert manifests
        s = timer()
        # `mt_insert_manifests` returns a list of all canvas IDs of all the manifests inserted.
        list_id_canvas = mt_insert_manifests(
            func=self.adapter.insert_manifest,
            n=n_manifest,
            threads=self.threads,
            pbar_desc=f"inserting {n_manifest} manifests with {n_canvas_per_manifest} canvases each (threads={self.threads})",
            n_manifest=n_manifest,
            n_canvas=n_canvas_per_manifest,
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
            n_canvas_with_annotations_per_manifest
        )
        s = timer()
        # `mt_insert_annotations` returns the list of canvas IDs on which annotations were inserted (should be the same as `list_id_canvas_sampled`)
        list_id_canvas_annotations = mt_insert_annotations(
            func=self.adapter.insert_annotation_list,
            data=list_id_canvas_sample,
            n_annotation=step_n_annotation_per_canvas,
            threads=self.threads,
            pbar_desc=f"inserting {n_annotation} annotations on {len(list_id_canvas_sample)} canvases (threads={self.threads})"
        )

        e = timer()
        d_populate_annotation = e-s
        # there's always an error in SAS insertions, so only enable this check for aiiinotate.
        if self.server_is_aiiinotate:
            assert len(list_id_canvas_sample) == len(list_id_canvas_annotations)
        return d_populate_manifest, d_populate_annotation, list_id_canvas_full, list_id_canvas_annotations

    def get_annotations_for_canvases(self, list_id_canvas: List[str], is_benchmark: bool = False):
        """
        get all annotations on canvases whose @ids are in `list_id_canvas`
        """
        list_annotations = []
        desc = (
            f"benchmark: read, {len(list_id_canvas)} annotation lists"
            if is_benchmark
            else f"reading annotation lists for {len(list_id_canvas)} canvases"
        )
        for id_canvas in tqdm(
            list_id_canvas,
            total=len(list_id_canvas),
            desc=desc
        ):
            # SAS returns Annotation[], while aiiinotate returns an AnnotationList.
            annotations_data = self.adapter.get_annotation_list(id_canvas)
            if self.server_is_aiiinotate:
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

        # 1. read annotations on a canvas
        s = timer()
        list_annotations = self.get_annotations_for_canvases(list_id_canvas, True)
        e = timer()
        d_read_annotation_list = (e-s) / self.n_iterations

        # 2. read a single annotation
        d_read_annotation = None
        # SAS can't fetch a single anno by its @id => only enable for aiiinotate
        if self.server_is_aiiinotate:
            # list of randomly selected annotation @ids.
            list_id_annotation = [
                random.choice(list_annotations)["@id"]
                for _ in range(self.n_iterations)
            ]
            s = timer()
            for id_annotation in tqdm(
                list_id_annotation,
                total=len(list_id_annotation),
                desc=f"benchmark: read, {len(list_id_annotation)} annotations"
            ):
                annotation = self.adapter.get_annotation(id_annotation)  # pyright: ignore
                assert "@id" in annotation.keys() and annotation["@id"] == id_annotation
            e = timer()
            d_read_annotation = (e-s) / self.n_iterations

        # TODO 3. IIIF SEARCH API

        return d_read_annotation_list, d_read_annotation

    def write(self) -> Tuple[float, float, float|None]:
        """
        write time benchmarks
        """
        # 1. insert manifests
        list_id_canvas = []
        generator_manifest = generate_manifests(self.n_iterations, self.step_current["n_canvas_per_manifest"])
        s = timer()
        for manifest in generator_manifest:
            canvases = self.adapter.insert_manifest(manifest)
            list_id_canvas.extend(canvases)
        e = timer()
        d_write_manifest = (e-s) / self.n_iterations

        # 2. create 1 annotation
        generator_annotation = generate_annotations(random.sample(list_id_canvas, self.n_iterations))
        s = timer()
        for annotation in tqdm(
            generator_annotation,
            total=self.n_iterations,
            desc=f"benchmark: write, {self.n_iterations} annotations"
        ):
            self.adapter.insert_annotation(annotation)
        e = timer()
        d_write_annotation = (e-s) / self.n_iterations

        # 3. create many annotations
        d_write_annotation_list = None
        generator_annotation_list = generate_annotation_lists(
            self.sample_for_iteration(list_id_canvas),
            self.n_annotation_per_canvas
        )
        s = timer()
        for annotation_list in tqdm(
            generator_annotation_list,
            total=self.n_iterations,
            desc=f"benchmark: write, {self.n_iterations} annotation lists"
        ):
            self.adapter.insert_annotation_list(annotation_list)
        e = timer()
        d_write_annotation_list = (e-s) / self.n_iterations

        return d_write_manifest, d_write_annotation, d_write_annotation_list

    def update(self, list_id_canvas: List[str]):
        """
        update time benchmarks
        """
        # update 1 annotation
        list_id_canvas = self.sample_for_iteration(list_id_canvas)
        list_annotation = self.get_annotations_for_canvases(list_id_canvas, False)
        list_annotation = self.sample_for_iteration(list_annotation)
        s = timer()
        for annotation in tqdm(
            list_annotation,
            total=len(list_annotation),
            desc=f"benchmark: updates, {len(list_annotation)} annotations"
        ):
            r = sorted(random.sample(range(0,1000), 4))  # 4 random numbers in range 0..1000
            annotation["on"][0]["selector"]["value"] = f"xywh={r[0]},{r[1]},{r[2]},{r[3]}"
            self.adapter.update_annotation(annotation)
        e = timer()
        d_update_annotation = (e-s) / self.n_iterations

        return d_update_annotation

    def delete(self, list_id_canvas: List[str]):
        list_id_canvas = self.sample_for_iteration(list_id_canvas)
        list_annotation = self.get_annotations_for_canvases(list_id_canvas, False)
        list_annotation = self.sample_for_iteration(list_annotation)

        # delete 1 annotation
        s = timer()
        for annotation in tqdm(
            list_annotation,
            total=len(list_annotation),
            desc=f"benchmark: delete, {len(list_annotation)} annotations"
        ):
            id_annotation = annotation["@id"]
            self.adapter.delete_annotation(id_annotation)
        e = timer()

        return (e-s) / self.n_iterations

    def purge(self):
        """
        at the end of a step, delete all contents from a db.
        """
        if self.server_is_aiiinotate:
            self.adapter.purge()  # pyright: ignore
        else:
            self.adapter.purge(self.threads)  # pyright: ignore
        return

    def step(self, idx_step:int, step: Tuple[int,int]):
        """
        run a single step.

        :param idx_step: position of steps within `self.steps`
        :param step: [n_manifest, n_canvas_per_manifest]
        """
        list_id_canvas_annotations = []
        step_dict = self.step_to_dict(idx_step, step)
        self.step_current = step_dict
        report = {}
        report["step"] = step_dict

        t_width = shutil.get_terminal_size((80,20))[0]
        banner_start = f"\nSTART STEP #{idx_step}: {step_dict}\n{'~' * t_width}\n"
        banner_end = f"{'~' * t_width}\n"
        print(banner_start)

        try:
            d_populate_manifest, d_populate_annotation, list_id_canvas_full, list_id_canvas_annotations = self.populate()
            report["timing_populate_manifest"] = d_populate_manifest
            report["timing_populate_annotation"] = d_populate_annotation

            d_read_annotation_list, d_read_annotation = self.read(list_id_canvas_annotations)
            report["timing_read_annotation_list"] = d_read_annotation_list
            if d_read_annotation is not None:
                report["timing_read_annotation"] = d_read_annotation

            d_write_manifest, d_write_annotation, d_write_annotation_list = self.write()
            report["timing_write_manifest"] = d_write_manifest
            report["timing_write_annotation"] = d_write_annotation
            if d_write_annotation_list is not None:
                report["timing_write_annotation_list"] = d_write_annotation_list

            d_update_annotation = self.update(list_id_canvas_annotations)
            report["timing_update_annotation"] = d_update_annotation

            d_delete_annotation = self.delete(list_id_canvas_annotations)
            report["timing_delete_annotation"] = d_delete_annotation

        finally:
            self.purge()
            self.step_current = {}
            self.report["results"].append(report)
            print(f"\nSTEP #{idx_step} RESULTS:")
            pprint(report)
            print("")

        print(banner_end)
        return

    def run(self):
        def write():
            if not self.nowrite:
                write_report(self.server_name, len(self.steps), timestamp, self.report)
            return

        timestamp = datetime.now().strftime(r'%Y-%m-%d-%H:%M:%S')
        print("Global benchmark parameters:")
        pprint(self.report)

        self.warmup()
        try:
            for i, step in enumerate(self.steps):
                i += 1
                self.step(i, step)  # pyright: ignore
                write()
        finally:
                write()
                visualize(self.report)
        return

