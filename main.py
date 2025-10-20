import argparse

from src.adapter_aiiinotate import AdapterAiiinotate
from src.adapter_sas import AdapterSas
from src.benchmark import Benchmark

parser = argparse.ArgumentParser(
    prog="AiiinotateBenchmark",
    description="benchmark for the aiiinotate IIIF annotation server"
)
parser.add_argument(
    "server",
    choices=["aiiinotate", "sas"],
    help="which annotation server to test"
)
parser.add_argument(
    "-e", "--endpoint",
    type=str,
    required=True,
    help="the endpoint on which the annotation server is listening (including http(s) scheme and port, if on localhost)"
)

if __name__ == "__main__":
    args = parser.parse_args()

    if args.server == "aiiinotate":
        adapter = AdapterAiiinotate(args.endpoint)
    else:
        adapter = AdapterSas(args.endpoint)

    Benchmark(adapter, [
        [1000, 1000],
        [1000, 10000],
        [10000, 10000],
        [10000, 100000],
        [100000, 100000],
        [1000000, 1000000],
    ])
