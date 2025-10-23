import argparse

from src.runner import runner

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
parser.add_argument(
    "-r", "--ratio",
    type=float,
    required=False,
    help="ratio of canvases with annotations to canvases without annotations (in range 0..1)"
)

if __name__ == "__main__":
    args = parser.parse_args()
    runner(args.server, args.endpoint, args.ratio)