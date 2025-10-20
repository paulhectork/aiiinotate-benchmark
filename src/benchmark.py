import requests
from typing import List, Tuple, Dict

from .generate import generate_all
from .adapter_core import AdapterCore


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
    return

def validate_adapter(adapter) -> None:
    if not issubclass(adapter, AdapterCore):
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
        self.n_annotation = 1000  # number of annotations per canvas.

    def step(self, step):
        try:
            self.step_current = step
            n_manifest, n_canvas = step
            list_manifest, list_annotationlist = generate_all(n_manifest, n_canvas, self.n_annotation)
            for manifest in list_manifest:
                self.adapter.insert_manifest(manifest)

        finally:
            self.step_current = None

    def benchmark(self):
        for step in self.steps:
            self.step(step)
