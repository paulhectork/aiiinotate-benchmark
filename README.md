# aiiinotate benchmark

A benchmark of the [aiiinotate](github.com/Aikon-platform/aiiinotate/) IIIF annotations server.

---

## Requirements

The benchmark requires `uv`, aiiinotate requires `node` and `mongodb`.

- [installing uv](https://docs.astral.sh/uv/getting-started/installation/)
- [installing node](https://nodejs.org/en/download) (MacOS/Linux installation script can be found [here](https://github.com/Aikon-platform/aiiinotate/blob/main/scripts/setup_node.sh))
- [installing mongodb](https://www.mongodb.com/docs/manual/installation/) (MacOS/Linux installation script can be found [here](https://github.com/Aikon-platform/aiiinotate/blob/main/scripts/setup_mongodb.sh))

---

## Setup

1. clone the repo

```bash
git clone https://github.com/paulhectork/aiiinotate-benchmark.git
```

2. create `.env.aiiinotate` based on `.env.aiiinotate.template` 
    - no need for the database or anything to exist
    - do not use a pre-existing database ! this will insert tons of data.

3. setup (sets up aiiinotate)

```bash
bash setup.sh
```

You're done:)

---

## Usage

### Benchmarks

Benchmarks are done using a CLI. aiiinotate and SAS are benchmarked independently.

Run `uv run main.py --help` for a full list of options.

1. in one terminal, **start the annotation server** (unecessary if benchmarking a remote instance that is aldready running)
    - for **aiiinotate**:
    ```bash
    bash run_aiiinotate.sh
    ```
    - for **SAS**:
    ```bash
    bash run_sas.sh
    ```

2. in another terminal, **run the benchmark**

```bash
# assuming aiiinotate runs on http:/localhost:4000
uv run main.py benchmark \                  # cli entrypoint
    aiiinotate \                            # which annotation server to benchmark
    --endpoint http://localhost:4000 \      # its endpoint
    --steps 4                               # how many steps to run
    --nowrite?                              # optional: don't write the database results to file 
```

### Visualization

Visualization is used to plot a benchmark report. To visualize, you must have saved a benchmark report to a file.

```bash
# if `latest`, the most recent saved benchmark is visualized
# otherwise, provide the path to the benchmark to visualize
# if `--nowrite`, show the visualization without saving it
uv run main.py visualize latest|path/to/report --nowrite?
```

---

## Methodology

The benchmark executes **the same operations across different annotation servers** (currently, SAS is partially implemented, aiiinotate fully implemented). 

A benchmark
- **consists of multiple steps** (up to 8). 
- each step **repeats the same CRUD operations** on an annotation server 
- **the database grows larger at each step** (up to 100M annotations, if the annotation server handles it). 

Each step consists of 3 phases:
- **populate phase**: insert data in the database accross multiple threads (up to 100M annotations)
- **benchmark phase**: time various CRUD operations. Each CRUD operation is repeated several times over a single thread, and the average time to execute each operation once is stored.
- **purge phase**: delete the contents of the entire database.

Read [`methodology.md`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/docs/methodology.md) for more info.

---

## Results

Results are written to a JSON file in `out/`. They are written at the end of each step and if an unhandled exception happens, so you always have results even when not completing the entire benchmark. 

Here's how to read-them. Note that:

- **timings in the populate phase** are for an entire operation across all threads (i.e., the time it took to insert 100K annotations over 20 threads)
- **timings in the benchmark phase** are the average time to execute a single operation (the operatio is executed 50 time in a row, we calculate the average) and are obtained in a single thread.

```py
{
  # the name of the benchmarked annotation server
  "server_name": "aiiinotate",
  # the total number of steps executed
  "n_steps": 4,
  # how many concurent threads are used in the populate phase
  "n_threads": 20,
  # how many iterations are used for each operation in the benchmark phase
  "n_iterations": 50,
  # how many annotations are inserted on a canvas, if this canvas has annotations
  "n_annotation_per_canvas": 100,
  # number of annotations / number of canvases
  "ratio_annotation_to_canvas": 0.1,
  # results are expressed in seconds
  "time_unit": "seconds",
  # results for each step
  "results": [
    # step 1
    {
      # step parameters
      "step": {
        # step number
        "index": 1,
        # number of manifests inserted in the populate phase
        "n_manifest": 1,
        # number of annotations inserted in the populate phase
        "n_annotations": 10,
        # number of canvases throughout all manifests
        "n_canvas_total": 100,
        # number of canvases in each manifest
        "n_canvas_per_manifest": 100,
        # number of canvases on which there will be annotations
        "n_canvas_with_annotations_per_manifest": 1
      },
      # execution times
      # populate: time it took to insert all manifests (in multiple threads)
      "duration_populate_manifest": 0.014824203000898706,
      # populate: time it took to insert all annotations (in multiple threads)
      "duration_populate_annotation": 0.25701393200142775,
      # benchmark: average time to read an annotation list (all annos on a canvas)
      "duration_read_annotation_list": 9.945913996489252e-05,
      # benchmark: average time to read a single annotation
      "duration_read_annotation": 0.001169423339961213,
      # benchmark: average time to write a single manifest to DB
      "duration_write_manifest": 0.0038403833199845395,
      # benchmark: averag time to write a single annotation to DB
      "duration_write_annotation": 0.05096443005997571,
      # benchmark: average time to write a single annotation list with 100 annos to DB
      "duration_write_annotation_list": 0.04751963112001249,
      # benchmark: average time it took to update a single annotation
      "duration_update_annotation": 0.004386051359979319,
      # benchmark: average time it took to delete a single annotation
      "duration_delete_annotation": 0.00034402311997837386
    },
    # the other steps will have the same structure
  ]
}
```
