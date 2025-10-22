"""
multithreading functions to insert data.
this module defines `multithread` (a decorator) and mt_* functions that use this decorator to parallelize.
all multithreaded functions are grouped here for efficiency.
"""

from threading import Lock
from multiprocessing.pool import ThreadPool
from typing import Dict, List, Tuple, Callable, Optional
import random

from tqdm import tqdm

from .generate import generate_annotation_list, generate_manifest


def multithread_wrapper(f, kwargs):
    """unpack kwargs and call the function."""
    return f(**kwargs)

def multithread(func) -> Callable:
    """decorator to multiprocess a function, without collecting anything. use for inserts"""

    def wrapper(**kwargs) -> List[Optional[str]]:
        """
        NOTE: the wrapped function must accept **kwargs and arguments to the wrapped function must be passed as kwargs

        **kwargs should contain:
        - either:
            - n: int, number of documents (annotations or manifests) to insert
            - data: List, a list of items that will be divided among threads and passed to worker processes.
            => to insert manifests, we only need to know `n` (number of manifests). to insert annotations, we need to know the @ids of manifests on which to insert annotations.
        - threads: int, number of threads to use
        - pbar_desc: str, description message for the tqdm progress bar
        - func: Callable, function to perform the inserts (a member or a descendant of `AdapterCore`)
        - any other kwargs to pass to the wrapped funcion

        **kwargs can optionnally contain:
        """
        if not any(k in kwargs.keys() for k in ["n", "data"]):
            raise ValueError(f"'n' or 'data' must be defined in 'kwargs' ! got {kwargs}")

        threads = kwargs["threads"]

        # split `data` into even sized sub-lists to pass to each process.
        if "data" in kwargs.keys():
            if not isinstance(kwargs["data"], list):
                raise TypeError(f"kwargs['data'] must be a list ! got '{type(kwargs['data'])}'")
            data = kwargs["data"]
            n = len(data)
            n_per_thread = n // threads  # number of items to process in each thread

            # make a nested list of length `threads`, each sub-list with the same number of items
            # https://stackoverflow.com/a/2231685
            data: List[List] = [
                data[i:i+n_per_thread] for i in range(0, n, n_per_thread)
            ]
            # since `n_per_threads` is rounded, it may leave stuff out
            # => there can be an extra item in `data` with leftovers that could not be split evenly
            # => append everything extra to the 1st item in data.
            if len(data) > threads:
                # all items whose index is > `threads` is left over
                for leftover in data[threads:]:
                    data[0].extend(leftover)
                data = data[:threads]  # keep only the last items.
            # data_shape = [ len(d) for d in data ]
            # print(f">>> n={n} threads={threads} len(data)={len(data)} data_shape={data_shape}")
            assert len(data) == threads
            assert sum(len(d) for d in data) == n
            kwargs["data"] = data
            kwargs["n"] = n_per_thread

        # get the number of entries to process per thread
        else:
            n = kwargs["n"]
            n_per_thread = n // threads
            kwargs["n"] = n_per_thread

        # create a tqdm progress bar. `lock` tracks the shared memory in all worker processses
        pbar_desc = kwargs["pbar_desc"]
        pbar = tqdm(total=n, desc=pbar_desc)
        lock = Lock()

        # build pool_kwargs, the arguments that will be passed to each worker process.
        pool_kwargs = []
        for i in range(threads):
            kw = kwargs.copy()
            kw["pbar"] = pbar
            kw["lock"] = lock
            # extract the `data` sublist to pass to `f`.
            if "data" in kwargs.keys():
                kw["data"] = kwargs["data"][i]
            pool_kwargs.append((func, kw))

        # we pass to `pool`
        # 1. a function that, for each thread, applies the kwargs `kw` to `f`
        # 2. an array of (f, kw), with `f` the function to be executed by each thread and `kw` the kwargs passed to each thread.
        list_id = []
        success = 0
        error = 0
        with ThreadPool(threads) as pool:
            #NOTE: each thread should return [int,int, Optional[List[str]]]:
            # - number of successful inserts,
            # - number of errors,
            # - optional list of inserted data (i.e., inserted canvas IDs when inserting manifests)
            r = pool.starmap(multithread_wrapper, pool_kwargs)
            # group results: r contains 1 item / thread => combine
            for el in r:
                success += el[0]
                error += el[1]
                if len(el) == 3:
                    list_id += el[2]

        pbar.close()
        print(f"SUCCESS: {success}, ERROR: {error}")
        return list_id

    return wrapper

@multithread
def mt_insert_manifests(
    func: Callable,
    n: int,
    n_canvas: int,
    lock: Lock,
    pbar: tqdm,
    **kwargs
) -> Tuple[int,int, List[str]]:
    """
    insert manifests in parallel threads

    :param func: Callable - function to use for insert
    :param n: int - number of manifests to insert in one thread
    :param n_canvas: int - number of canvases per manifest
    :param loc: threading.Lock - for shared state
    :param pbar: tqdm.Tqdm - progress bar

    :returns:
        int, int, List[str]
        - # of successes in this thread
        - # of errors in this thread
        - all inserted ids in this thread
    """
    error = 0
    success = 0
    list_id_canvas = []
    for _ in range(n):
        # _list_id_canvas = id of all canvases in the manifest inserted
        _list_id_canvas = func(generate_manifest(n_canvas))
        # update the tqdm progress bar + track success and errors
        with lock:
            pbar.update(1)
        # record the number of successes and errors.
        if len(_list_id_canvas) == 0:
            error += 1
        else:
            success += 1
            list_id_canvas += _list_id_canvas
    return success, error, list_id_canvas

@multithread
def mt_insert_annotations(
    func: Callable,
    data: List[str],
    n_annotation: int,
    lock: Lock,
    pbar: tqdm,
    **kwargs
):
    """
    'data' contains canvas IDs. insert 'n_annotation' per canvas whose id is in 'data'.

    :func: function to insert an annotation list on one canvas_id
    :data: list of canvas ids inserted by `mt_insert_manifests`
    :n_annotation: number of annotations / canvas
    :lock: for shared memory
    :pbar: the process bar, to update it in the parent process.

    :returns:
        int, int, List[str]
        - # of successes in this thread
        - # of errors in this thread
        - all the canvas IDs on which annotations were inserted
    """
    success = 0
    error = 0

    list_id_canvas = data
    list_id_canvas_out = []
    for id_canvas in list_id_canvas:
        r = func(generate_annotation_list(
            id_canvas, n_annotation
        ))
        # update tqdm
        with lock:
            pbar.update(1)
        # track errors and successes
        if r == 1:
            success += 1
            list_id_canvas_out.append(id_canvas)
        else:
            error += 1

    return success, error, list_id_canvas_out

@multithread
def mt_delete(
    data: List[str],
    func: Callable,
    lock: Lock,
    pbar: tqdm,
    **kwargs
) -> Tuple[int,int]:
    """
    delete data (annotations or manifests)

    :param data: iterable with the IDs to delete (can be annotations "@id", manifest "@id"... depending on what `func` needs)
    :param func: function to delete data
    :param lock: for shared memory
    :param pbar: the process bar, to update it in the parent process.
    """
    success = 0
    error = 0
    for _id in data:
        r = func(_id)
        with lock:
            pbar.update(1)
        if r==1:
            success += 1
        else:
            error += 0
    return success, error



