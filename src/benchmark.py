import shutil
import random
from itertools import chain
from datetime import datetime
from typing import List, Tuple, Dict
from timeit import default_timer as timer

from .utils import pprint, write_log
from .adapter_sas import AdapterSas
from .adapter_aiiinotate import AdapterAiiinotate
from .adapter_core import AdapterCore, validate_endpoint
from .multithread import mt_insert_manifests, mt_insert_annotations, mt_delete
from .constants import STEPS_GROUP, STEPS_FLAT, STEPS_GROUP_RANGE, RATIO_DEFAULT, N_STEPS_DEFAULT


def validate_n_steps(n_steps: int):
    if (
        (not isinstance(n_steps, int))
        or n_steps < STEPS_GROUP_RANGE[0]
        or n_steps > STEPS_GROUP_RANGE[1]
    ):
        raise ValueError(f"validate_n_steps: 'steps' must be an integer, with steps <= {len(STEPS_GROUP)}, got '{n_steps}'" )

def validate_server(server:str) -> None:
    if server not in ["aiiinotate", "sas"]:
        raise TypeError(f"validate_adapter: server '{server}' must be one of ['aiiinotate', 'sas']")
    return

def validate_ratio(r) -> None:
    if r is not None:
        if not isinstance(r, float) or not (r>0 and r<=1):
            raise ValueError(f"validate_ratio: ratio must be a float in range 0..1, got '{r}' (type {type('r')})")
    return

class Benchmark:
    def __init__(
        self,
        endpoint: str,
        # adapter: AdapterCore,
        server: str,
        n_steps: int = N_STEPS_DEFAULT,
        # steps: List[List[int]] | List[Tuple[int,int]],
        ratio: float|None = RATIO_DEFAULT,
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

        adapter: AdapterCore
        if server == "aiiinotate":
            adapter = AdapterAiiinotate(endpoint)
        else:
            adapter = AdapterSas(endpoint)

        # STEPS_GROUP is used to count steps in the CLI, STEPS_FLAT is actually used for the benchmark
        # => select the values in STEPS_FLAT based on `n_steps`
        steps: list = STEPS_FLAT[:3*n_steps]

        self.adapter = adapter
        self.steps = steps
        self.ratio = ratio if ratio is not None else RATIO_DEFAULT  # ratio of canvases that will have annotations. 0.01 = 1 in 100 canvases in a manifest will have annotations.

        self.n_annotation = 1000  # number of annotations per canvas.
        self.n_iterations = 50  # number of iterations for read benchmarking: we will run read queries `n` times and then get the average time for a single query.
        self.threads = 20

        self.step_current = None
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

    def inserts(self):
        """
        insert annotations and annotation lists
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
        d_insert_manifest = e-s
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
        d_insert_annotation = e-s
        # NOTE: there's always an error in SAS insertions, so the check below fails.
        # assert len(list_id_canvas_sample) == len(list_id_canvas_annotations)
        return d_insert_manifest, d_insert_annotation, list_id_canvas_full, list_id_canvas_annotations

    def read(self, list_id_canvas:List[str]):
        """
        this is actually what we're really interested in: read time benchmarking.

        :param list_id_canvas: canvases containing annotations
        """
        list_id_canvas = random.sample(list_id_canvas, self.n_iterations)
        list_annotation_list = []

        d_read_annotation = None

        s = timer()
        for id_canvas in list_id_canvas:
            annotation_list = self.adapter.get_annotation_list(id_canvas)
            assert "resources" in annotation_list and len(annotation_list["resources"]) > 0
            list_annotation_list.append(annotation_list)
        e = timer()
        d_read_annotation_list = (e - s) / self.n_iterations

        if self.adapter.server_name == "Aiiinotate":
            # list of randomly selected annotation @ids.
            list_id_annotation = [
                random.choice(random.choice(list_annotation_list)["resources"])["@id"]
                for _ in range(self.n_iterations)
            ]
            s = timer()
            for id_annotation in list_id_annotation:
                annotation = self.adapter.get_annotation(id_annotation)  # pyright: ignore
                assert "@id" in annotation.keys() and annotation["@id"] == id_annotation
            e = timer()
            d_read_annotation = (e-s) / self.n_iterations

        return d_read_annotation_list, d_read_annotation

    def purge(self, list_id_canvas_annotations: List[str] = []):
        """
        at the end of a step, delete all contents from a db.
        """
        list_id_manifest = self.adapter.get_id_manifest_list()
        if self.adapter.server_name == "Aiiinotate":
            self.adapter.purge()
            # mt_delete(
            #     data=list_id_manifest,
            #     func=self.adapter.delete_annotations_for_manifest,
            #     threads=self.threads,
            #     pbar_desc=f"deleting all annotations from {len(list_id_manifest)} manifests (threads={self.threads})"
            # )
            # mt_delete(
            #     data=list_id_manifest,
            #     func=self.adapter.delete_manifest,
            #     threads=self.threads,
            #     pbar_desc=f"deleting {len(list_id_manifest)} manifests (threads={self.threads})"
            # )
        else:
            self.adapter.purge()
            # #NOTE: with SAS, we can't delete manifests, so we just delete annotations.
            # if len(list_id_canvas_annotations):
            #     mt_delete(
            #         data=list_id_canvas_annotations,
            #         func=self.adapter.delete_annotations_for_canvas,  # pyright: ignore
            #         threads=self.threads,
            #         pbar_desc=f"deleting all annotations from {len(list_id_canvas_annotations)} canvases (threads={self.threads})"
            #     )
            # # actually this might always be faster than `list_id_canvas_annotations`.
            # else:
            #     mt_delete(
            #         data=list_id_manifest,
            #         func=self.adapter.delete_annotations_for_manifest,
            #         threads=self.threads,
            #         pbar_desc=f"deleting all annotations from {len(list_id_manifest)} manifests (threads={self.threads})"
            #     )
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
        log = {
            "step": step_dict,
            "duration_insert_manifest": None,
            "duration_insert_annotation": None,
            "duration_read_annotation_list": None,
        }

        t_width = shutil.get_terminal_size((80,20))[0]
        banner_start = f"\nSTART STEP #{idx_step}: {step_dict}\n{'*' * t_width}\n"
        banner_end = f"{'*' * t_width}\n"
        print(banner_start)

        try:
            d_insert_manifest, d_insert_annotation, list_id_canvas_full, list_id_canvas_annotations = self.inserts()
            log["duration_insert_manifest"] = d_insert_manifest
            log["duration_insert_annotation"] = d_insert_annotation
            d_read_annotation_list, d_read_annotation = self.read(list_id_canvas_annotations)
            log["duration_read_annotation_list"] = d_read_annotation_list
            if d_read_annotation is not None:
                log["duration_read_annotation"] = d_read_annotation

        finally:
            self.purge(list_id_canvas_annotations)
            self.step_current = None
            self.log["results"].append(log)
            print(f"\nSTEP #{idx_step} RESULTS:")
            pprint(log)
            print("")

        print(banner_end)
        return

    def run(self):
        timestamp = datetime.now().strftime(r'%Y-%m-%d-%H:%M:%S')
        write = lambda: write_log(self.adapter.server_name, len(self.steps), timestamp, self.log)
        print("Global benchmark parameters:")
        pprint(self.log)
        try:
            for i, step in enumerate(self.steps):
                self.step(i, step)  # pyright: ignore
                write()
        finally:
                write()
        return

