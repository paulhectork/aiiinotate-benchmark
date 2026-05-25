import argparse

from src.runner import runner
from src.constants import STEPS, N_STEPS_DEFAULT, THREADS_DEFAULT

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
    default=N_STEPS_DEFAULT,
    help="the endpoint on which the annotation server is listening (including http(s) scheme and port, if on localhost)"
)
parser.add_argument(
    "-s", "--steps",
    type=int,
    required=False,
    help=f"number of step groups to run (in range (1..{len(STEPS)+1}))"
)
parser.add_argument(
    "-t", "--threads",
    type=int,
    required=False,
    default=THREADS_DEFAULT,
    help=f"number of threads to use when populating database (default={THREADS_DEFAULT})"
)
parser.add_argument(
    "-n", "--nowrite",
    action="store_true",
    default=False,
    help="do not write the benchmark report to file"
)

if __name__ == "__main__":
    args = parser.parse_args()
    runner(
        server=args.server,
        endpoint=args.endpoint,
        n_steps=args.steps,
        threads=args.threads,
        nowrite=args.nowrite
    )