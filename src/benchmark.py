import random
from typing import List, Tuple, Dict

import requests

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

    def step(self, step):
        try:
            self.step_current = step
            n_manifest, n_canvas = step

            # insert manifests
            id_canvas_list = mt_insert_manifests(
                func_insert=self.adapter.insert_manifest,
                n=n_manifest,
                threads=self.threads,
                pbar_desc=f"inserting {n_manifest} manifests with {n_canvas} canvases (threads={self.threads})",
                n_manifest=n_manifest,
                n_canvas=n_canvas,
            )
            assert len(id_canvas_list) != 0

            # insert annotations.
            # first, we randomly sample `id_canvas_list` to select the canvases on which we'll work.
            # NOTE: id_canvas_list MUST be sampled here (and not in a worker thread) to avoid the same canvas to be sampled twice in separate threads
            id_canvas_list = random.sample(
                id_canvas_list,
                round(len(id_canvas_list) * self.ratio)
            )
            mt_insert_annotations(
                func_insert=self.adapter.insert_annotation_list,
                data=id_canvas_list,
                n_annotation=self.n_annotation,
                threads=self.threads,
                pbar_desc=f"inserting {self.n_annotation * len(id_canvas_list)} annotations on {len(id_canvas_list)} canvases (threads={self.threads})"
            )

        finally:
            self.step_current = None

    def run(self):
        for step in self.steps:
            self.step(step)
