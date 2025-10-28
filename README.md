# aiiinotate benchmark

A benchmark of the [aiiinotate](github.com/Aikon-platform/aiiinotate/) IIIF annotations server.

---

## Setup

1. clone the repo

```bash
git clone https://github.com/paulhectork/aiiinotate-benchmark.git
```

2. create `.env.aiiinotate` based on `.env.aiiinotate.template` 
    - for the moment, there is only manual edition. 
    - no need for the database or anything to exist
    - do not use a pre-existing database ! this will insert tons of data.

3. setup (creates a venv and sets up aiiinotate)

```bash
bash setup.sh
```

you're done:)

---

## Usage

benchmarks are done using a CLI. aiiinotate and SAS are benchmarked independently.

Run `python main.py --help` for a full list of options.

### Aiiinotate

1. in one terminal, **start aiiinotate** (unecessary if benchmarking a remote aiiinotate instance that is aldready running)

```bash
bash run_aiiinotate.sh
```

2. in another terminal, **run the benchmark**

```bash
# assuming aiiinotate runs on http:/localhost:4000
source venv/bin/activate
python main.py \
    aiiinotate \
    -e http://localhost:4000 \
    -n 3 \
    -r 0.01
```

### SAS

1. in one terminal, **start SAS** (same, skip this step if working with a remote or aldready running instance). SAS's default port is `8888`.

```bash
bash run_sas.sh
```

2. in another terminal, **run the benchmark**

```bash
# assuming sas runs on http://localhost:8888
source venv/bin/activate
python main.py \
    sas \
    -e http://localhost:8888 \
    -n 3
    -r 0.01
```

---

## Methodology

The benchmark is organized in several steps. Each step consists of:

1. inserting manifests
2. inserting annotations
3. running benchmarks
4. purging the database.

Each step increases the number of manifests or annotations: `100 -> 10000 -> 10000` manifests, `100 -> 1000 -> 10000` annotations.

### Inserting dummy data

Steps `1.` and `2.` are done by generating and inserting fake manifests, annotation lists and annotations (see `src/generate.py`). To speed the process, insertions are parrallelized using multithreading with `Benchmark.threads` threads (usually, 20 threads).

Number of annotations inserted per canvas is constant (see `Benchark.n_canvas`), usually 1000: when a anvas has annotations, we insert 1000 annotations on the canvas.

Note that **insert times are purely indicative**. They are included as part of the benchmark results, but to time real insert times on Aiiinotate, we would need to use manifests that exist and can be accessed through HTTP.

### Benchmarks

Step `3.` is single threaded. All processes are repeated `Benchmark.n_iterations` times (usually 50 times) and benchmark times are averaged for all operations (`(start-end) / n_iterations`). The benchmarks are:

- reading all annotations for a single canvas in a single manifests (which demands to scan all annotations to find their target canvas)
- reading a single annotation (which demands to scan all annotation's `@id`)
- writing a single annotation
- writing an annotation list
- updating a single annotation
- deleting a single annotation

If a functionnality is not implemented by an annotation server, either the step is skipped or we implement a process that is equivalent using available routes (for example, inserting an annotation list on SAS is done by inserting all annotations individually).

### Purging

Step `4.` deletes all database contents to start the next step with a fresh database. With Aiiinotate, this is done using `mongosh` commands in a Bash subprocess.

---

## Results

Results are written to a JSON file in `out/`. They are written at the end of each step and if an unhandled exception happens, so you always have results even when not completing the entire benchmark. Here's how to read-them:

```js
{
  // global info
  "server_name": "<name of the annotations server benchmarked>",
  "n_steps": "<total number of steps in the benchmark>",
  "threads": "<number of threads used for inserts>".
  "n_iterations": "<number of iterations for read-time benchmarks>",
  "ratio_canvas_with_annotations": "<ratio of canvases with annotations to canvases without annotations, on a scale of 0..1>",
  "time_unit": "seconds",
  "results": [
    // info on a single step
    {
      "step": {
        "index": "<step number>",
        "n_manifest": "<number of manifests inserted at this step>",
        "n_canvas": "<number of canvases inserted at this step>",
        "n_annotations": "<total number of annotations inserted at this step>",
        "n_annotation_per_canvas": "<number of annotations inserted per canvas with annotations>",
      },
      "duration_insert_manifest": "<time taken to insert all manifests in all threads>",
      "duration_insert_annotation": "<time taken to insert all annotations in all threads>",
      "duration_read_annotation_list": "<average time to read an annotation list>",
      "duration_read_annotation": "<average time to read a single annotation>",
    }
  ]
}
```
