import random
from typing import List, Tuple, Dict
from timeit import default_timer as timer

import requests

from .utils import pprint
from .adapter_core import AdapterCore
from .multithread import mt_insert_manifests, mt_insert_annotations


def validate_steps(steps) -> None:
    err = TypeError(f"validate_steps: 'steps' must be 'List[Tuple[int,int]]' or List[List[int]], will only positive values, got {steps}")
    if not isinstance(steps, list):
        raise err
    if not all(
        isinstance(step, list) or isinstance(step, tuple)
        for step in steps
    ):
        raise err
    if not all(
        isinstance(i, int) for step in steps for i in step
    ):
        raise err
    if not all(
        i>=0 for step in steps for i in step
    ):
        raise err
    return

def validate_adapter(adapter) -> None:
    if not isinstance(adapter, AdapterCore):
        raise TypeError(f"validate_adapter: adapter '{adapter}' should inherit from 'AdapterCore'")
    return

class Benchmark:
    def __init__(self, adapter: AdapterCore, steps: List[List[int]] | List[Tuple[int,int]]):
        """
        :param steps: steps of the benchmark, i.e [ (<step 1: number of manifests>, <step 1  number of canvases / manifest>), (<step 2: # manifests>, <step 2 # canvases / manifest>), ... ]
        :param adapter: an adapter inheriting from 'AdapterCore'
        """
        validate_steps(steps)
        validate_adapter(adapter)
        self.adapter = adapter
        self.steps = steps
        self.step_current = None
        self.threads = 20
        self.ratio = 0.01  # ratio of canvases that will have annotations. 0.01 = 1 in 100 canvases in a manifest will have annotations.
        self.n_annotation = 1000  # number of annotations per canvas.
        self.log = {
            "server_name": self.adapter.server_name,
            "time_unit": "s",
            "results": []
        }

    def step_to_dict(self, step: List[int]) -> Dict:
        n_canvas, n_manifest = step
        return {
            "n_manifest": step[0],
            "n_canvas": step[1],
            "n_annotations": self.n_annotation * round(n_canvas * self.ratio) * n_manifest,
        }

    def inserts(self):
        """
        insert annotations and annotation lists
        NOTE: this isn't really a step of the benchmark as much as it is a preparatory step, but we log times just in case.
            in more detail: in Aiiinotate, a big insert bottleneck is to fetch the manifest for each annotation's target, index the manifest and get annotation's canvas index, which we can't replicate.
        """
        n_manifest, n_canvas = self.step_current["data"]  # pyright:ignore

        # insert manifests
        s = timer()
        # `mt_insert_manifests` returns a list of all canvas IDs of all the manifests inserted.
        id_canvas_list = mt_insert_manifests(
            func_insert=self.adapter.insert_manifest,
            n=n_manifest,
            threads=self.threads,
            pbar_desc=f"inserting {n_manifest} manifests with {n_canvas} canvases (threads={self.threads})",
            n_manifest=n_manifest,
            n_canvas=n_canvas,
        )
        e = timer()
        d_insert_manifest = e-s
        assert len(id_canvas_list) != 0

        # insert annotations.
        # first, we randomly sample `id_canvas_list` to select the canvases on which we'll work.
        # NOTE: id_canvas_list MUST be sampled here (and not in a worker thread) to avoid the same canvas to be sampled twice in separate threads
        id_canvas_list_full = id_canvas_list
        id_canvas_list_sample = random.sample(
            id_canvas_list,
            round(len(id_canvas_list) * self.ratio)
        )
        s = timer()
        # `mt_insert_annotations` returns the list of canvas IDs on which annotations were inserted (should be the same as `id_canvas_list_sampled`)
        id_canvas_list_annotations = mt_insert_annotations(
            func_insert=self.adapter.insert_annotation_list,
            data=id_canvas_list,
            n_annotation=self.n_annotation,
            threads=self.threads,
            pbar_desc=f"inserting {self.n_annotation * len(id_canvas_list)} annotations on {len(id_canvas_list)} canvases (threads={self.threads})"
        )
        assert len(id_canvas_list_sample) == len(id_canvas_list_annotations)
        e = timer()
        d_insert_annotation = e-s

        return d_insert_manifest, d_insert_annotation, id_canvas_list_full, id_canvas_list_annotations


    def step(self, idx_step:int, step):
        log = {
            "step": self.step_to_dict(step),
            "duration_insert_manifest": None,
            "duration_insert_annotation": None,
        }
        try:
            self.step_current = { "index": idx_step, "data": step }
            d_insert_manifest, d_insert_annotation, id_canvas_list_full, id_canvas_list_annotations = self.inserts()
            log["duration_insert_manifest"] = d_insert_manifest
            log["duration_insert_annotation"] = d_insert_annotation

        finally:
            self.step_current = None
            self.log["results"].append(log)
            pprint(log)
        return

    def run(self):
        for i, step in enumerate(self.steps):
            self.step(i, step)
