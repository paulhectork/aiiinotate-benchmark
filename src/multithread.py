"""
multithreading functions to insert data.
this module defines `multithread` (a decorator) and insert_*, functions that use this decorator to insert data in parrallel.
"""

from threading import Lock
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Tuple, Callable

from tqdm import tqdm

from .generate import generate_manifest


def multithread_wrapper(f, kwargs):
    """unpack kwargs and call the function."""
    return f(**kwargs)

def multithread(f) -> Callable:
    """decorator to multiprocess a function, without collecting anything. use for inserts"""
    def wrapper(**kwargs):
        """
        NOTE: the wrapped function must accept **kwargs and arguments to the wrapped function must be passed as kwargs

        **kwargs should contain:
        - n: int, number of documents (annotations or manifests) to insert
        - threads: int, number of threads to use
        - pbar_desc: str, description message for the tqdm progress bar
        - insert_func: Callable, function to perform the inserts (a member or a descendant of `AdapterCore`)
        - any other kwargs to pass to the wrapped funcion
        """
        # get the number of manifests to generate per thread
        threads = kwargs["threads"]
        n = kwargs["n"]
        kwargs["n"] = n // threads

        # create a tqdm progress bar. `lock` tracks the shared memory in all worker processses
        pbar_desc = kwargs["pbar_desc"]
        pbar = tqdm(total=n, desc=pbar_desc)
        lock = Lock()

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
def insert_manifests(
    insert_func: Callable,
    n: int,
    n_canvas: int,
    lock: Lock,
    pbar: tqdm,
    **kwargs
) -> Tuple[int,int]:
    """
    insert manifests in parallel threads

    :param insert_func: Callable - function to use for insert
    :param n: int - number of manifests to insert in one thread
    :param n_canvas: int - number of canvases per manifest
    :param loc: threading.Lock - for shared state
    :param pbar: tqdm.Tqdm - progress bar
    """
    error = 0
    success = 0
    for _ in range(n):
        r = insert_func(generate_manifest(n_canvas))
        # update the tqdm progress bar + track success and errors
        with lock:
            pbar.update(1)
        # record the number of successes and errors.
        if r == 0:
            error += 1
        else:
            success += 1
    return success, error
