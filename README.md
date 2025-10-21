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

### aiiinotate

1. in one terminal, **start aiiinotate** (unecessary if benchmarking a remote aiiinotate instance that is aldready running)

```bash
bash run_aiiinotate.sh
```

2. in another terminal, **run the benchmark**

```bash
source venv/bin/activate
python main.py aiiinotate -e http://localhost:4000  # assuming aiiinotate runs on http:/localhost:4000
```

### SAS

1. in one terminal, **start SAS** (same, sip this step if working with a remote, aldready running instance). SAS's default port is `8888`.

```bash
bash run_sas.sh
```

2. in another terminal, **run the benchmark**

```bash
python main.py sas -e http://localhost:8888  # assuming sas runs on http://localhost:8888
```

---


