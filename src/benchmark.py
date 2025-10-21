import requests
from typing import List, Tuple, Dict, Callable
from multiprocessing import Pool
from multiprocessing.dummy import Pool as ThreadPool
import threading

from tqdm import tqdm

from .generate import generate_manifests, generate_manifest
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
    if not all(
        i>=0 for step in steps for i in step
    ):
        raise err
    return

def validate_adapter(adapter) -> None:
    if not isinstance(adapter, AdapterCore):
        raise TypeError(f"validate_adapter: adapter '{adapter}' should inherit from 'AdapterCore'")
    return

def multithread_wrapper(f, kwargs):
    """unpack kwargs and call the function."""
    return f(**kwargs)

def multithread(f) -> Callable:
    """decorator to multiprocess a function, without collecting anything. use for inserts"""
    def wrapper(**kwargs):
        """
        NOTE: the wrapped function must accept **kwargs.

        **kwargs should contain:
        - n: int, number of documents (annotations or manifests) to insert
        - threads: int, number of threads to use
        - pbar_desc: str, description message for the tqdm progress bar
        - insert_func: Callable, function to perform the inserts
        - any other kwargs to pass to the wrapped funcion
        """
        # get the number of manifests to generate per thread
        threads = kwargs["threads"]
        n = kwargs["n"]
        kwargs["n"] = n // threads
        pbar_desc = kwargs["pbar_desc"]

        # create a tqdm progress bar. `lock` tracks the shared memory in all worker processses
        pbar = tqdm(total=n, desc=pbar_desc)
        lock = threading.Lock()

        # build pool_kwargs, the arguments that will be passed to each worker process.
        pool_kwargs = []
        for _ in range(threads):
            kw = kwargs.copy()
            kw["pbar"] = pbar
            kw["lock"] = lock
            pool_kwargs.append((f, kw))

        # we pass to `pool`
        # 1. a function that, for each thread, applies the kwargs `kw` to `f`
        # 2. an array of (f, kw), with `f` the function to be executed by each thread and `kw` the kwargs passed to each thread.
        with ThreadPool(threads) as pool:
            #NOTE: each thread should return [int,int]: number of successful inserts and number of errors.
            r = pool.starmap(multithread_wrapper, pool_kwargs)
            success = sum(el[0] for el in r)
            error = sum(el[1] for el in r)
        pbar.close()
        print(f"SUCCESS: {success}, ERROR: {error}")
    return wrapper

@multithread
def insert_manifests(**kwargs) -> Tuple[int,int]:
    """
    **kwargs should contain:
    - insert_func: Callable, function to use for insert
    - n: int, number of manifesats to insert in one thread
    - n_canvas: int, number of canvases per manifest
    - loc: threading.Lock, for shared state
    - pbar: tqdm.Tqdm, progress bar
    """
    insert_func = kwargs["insert_func"]
    n_manifest = int(kwargs["n"])
    n_canvas = int(kwargs["n_canvas"])
    error = 0
    success = 0
    for _ in range(n_manifest):
        r = insert_func(generate_manifest(n_canvas))
        # update the tqdm progress bar + track success and errors
        with kwargs["lock"]:
            kwargs["pbar"].update(1)
        if r == 0:
            error += 1
        else:
            success += 1
    return success, error

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
            insert_manifests(
                insert_func=self.adapter.insert_manifest,
                n=n_manifest,
                threads=self.threads,
                pbar_desc=f"inserting {n_manifest} manifests with {n_canvas} canvases (threads={self.threads})",
                n_manifest=n_manifest,
                n_canvas=n_canvas,
            )
        finally:
            self.step_current = None

    def run(self):
        for step in self.steps:
            self.step(step)
