# Benchmark methodology


## Overview

The benchmark is divided in steps, with a database that grows from a step to another. Steps are defined in [`constants.py`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/src/constants.py) and benchmark in [`benchmark.py`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/src/benchmark.py).

Each step follows the same pipeline, and each step begins with a blank database:
- **populate**: in an empty database, insert "starting" data: a certain number of manifests and annotations.
- **run the benchmarks** (create/read/update/delete).
- **purge**: remove all data from the database.

---

## Defining steps

Steps are defined in [`src/constants`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/src/constants.py) as a list of `(n_manifest, n_canvas_per_manifest)` tuple.

```py
STEPS = [
    (1,           100),
    (1,         1_000),
    (10,        1_000),
    (100,       1_000),
    (1_000,     1_000),
    (10_000,    1_000),
    (100_000,   1_000),
    (1_000_000, 1_000),
]
```

The actual number of annotations inserted at each step is defined by `RATIO`: the annotation-to-canvas ratio. 

```python
RATIO = 0.1
```

It is set to $$0.1$$, meaning we will insert 10% as many annotations as there are canvases in all manifests. Note that, in a production instance of aiiinotate, this ratio is actually closer to $$0.4$$.

The steps can be summarized by the table:

```
   manifests   canvases/manifest   total canvases    annotations
----------------------------------------------------------------
           1                 100              100             10
           1               1,000            1,000            100
          10               1,000           10,000          1,000
         100               1,000          100,000         10,000
       1,000               1,000        1,000,000        100,000
      10,000               1,000       10,000,000      1,000,000
     100,000               1,000      100,000,000     10,000,000
   1,000,000               1,000    1,000,000,000    100,000,000
```

To make the annotation server **sweat**, we don't insert 1 annotation par canvas, but 100 annotations per canvas. This is useful when timing read and write times for annotation lists: the annotation server will have more data to process, which corresponds better to real world use cases.

```py
N_ANNOTATIONS_PER_CANVAS = 100
```

In a step, if we need to insert $$1000$$ annotations, they will be inserted on $$\frac{1000}{100}=10$$ canvases.

If the total number of annotations to insert during a step is lower than `N_ANNOTATIONS_PER_CANVAS`, then `N_ANNOTATIONS_PER_CANVAS` is overwritten all annotations to insert will be inserted in a single canvas (i.e., 10 annotations are inserted on a single canvas at the 1st step).

In summary, for each step:

```py
total_canvases = n_manifests * n_canvas_per_manifest
total_annotations = total_canvases * ratio
number_of_canvases_with_annotations = total_annotations / N_ANNOTATIONS_PER_CANVAS
```

---

## Running a step

### 1. Populate

This is not part of the benchmark itself. Starting from an empty database, using the step definition defined above, we insert:

- `n_manifest` manifests, with `n_annotation` canvases each (i.e., $$1000$$ manifests, each with $$1000$$ canvases)
- from all inserted manifests, we select `number_of_canvases_with_annotations` canvases. On each, we insert `N_ANNOTATIONS_PER_CANVAS` canvases (i.e., at step 4, we insert $$100$$ annotations on $$\frac{10000}{100}=100$$ canvases).

To save time, the populate step is multithreaded (see [`multithread.py`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/src/multithread.py)): inserts are split over $$20$$ threads and done in a `ThreadPool`. This also has the advantage to test how well an annotation server handles concurrent clients. Number of threads can be changed in the CLI with the `-t --threads` argument.

### 2. Benchmarks

The benchmark step consists of different CRUD operations on the annotation server. They are executed in a single thread, through HTTP requests, and the average execution time of each query is saved.

Some of the operations are:
- insert an annotation
- insert an AnnotationList with `N_ANNOTATIONS_PER_CANVAS` annotations
- read all annotations on a canvas
- read a single annotation on a canvas
- update a single annotation
- delete a single annotation

Each of these operations is iterated several times, and we store the average execution time for a single query. The number of iterations is hard-coded:

```py
N_ITERATIONS = 50
```

The logic to average execution time is as follows (pseudocode):

```py
from timeit import default_timer as timer
s = timer()
for _ in enumerate(N_ITERATIONS):
    execute_query()
e = time()
average_execution_time = (e-s) / N_ITERATIONS
```

Benchmarks are executed in a single thread for timings to be more accurate.

The database size changes when running the benchmarks:
- ~ $$5000$$ annotations are inserted
- $$50$$ manifests are inserted

For clarity, for each step, the number of annotations/manifests/canvases that are stored correspond to **the numbers at the end of the `populate` step, not at the end of running the benchmark**: this is the actual database size that we start with.

### 3. Purge

At the end of a step, the entire database is purged. For the next step, we'll start with a blank database.
