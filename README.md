# aiiinotate benchmark

A benchmark of the [aiiinotate](github.com/Aikon-platform/aiiinotate/) IIIF annotations server.

---

## Methodology

Read [`methodology.md`](https://github.com/paulhectork/aiiinotate-benchmark/blob/main/docs/methodology.md).

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

3. setup (creates a venv and sets up aiiinotate)

```bash
bash setup.sh
```

you're done:)

---

## Usage

benchmarks are done using a CLI. aiiinotate and SAS are benchmarked independently.

Run `uv run main.py --help` for a full list of options.

1. in one terminal, **start the annotation serveraiiinotate** (unecessary if benchmarking a remote instance that is aldready running)
    - for aiiinotate:
    ```bash
    bash run_aiiinotate.sh
    ```
    - for SAS:
    ```bash
    bash run_sas.sh
    ```

2. in another terminal, **run the benchmark**

```bash
# assuming aiiinotate runs on http:/localhost:4000
uv run main.py \                            # cli entrypoint
    aiiinotate \                            # which annotation server to benchmark
    --endpoint http://localhost:4000 \      # its endpoint
    --steps 4                               # how many steps to run
```

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
