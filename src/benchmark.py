from typing import List, Tuple, Dict

import requests

from .adapter_core import AdapterCore
from .multithread import insert_manifests


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
        self.n_annotation = 1000  # number of annotations per canvas.

    def step(self, step):
        try:
            self.step_current = step
            n_manifest, n_canvas = step

            # insert dummy manifests
            insert_manifests(
                insert_func=self.adapter.insert_manifest,
                n=n_manifest,
                threads=self.threads,
                pbar_desc=f"inserting {n_manifest} manifests with {n_canvas} canvases (threads={self.threads})",
                n_manifest=n_manifest,
                n_canvas=n_canvas,
            )

            # get the @ids of canvases on which we want to insert annotations

        finally:
            self.step_current = None

    def run(self):
        for step in self.steps:
            self.step(step)
