import functools
from typing import Callable

import click

from src.benchmark import benchmark_runner
from src.constants import STEPS, N_STEPS_DEFAULT, THREADS_DEFAULT

def common_options(func: Callable) -> Callable:
    """
    add options shared by different CLI commands
    """
    @click.option(
        "-n", "--nowrite",
        type=click.BOOL,
        is_flag=True,
        default=False,
        help="do not write the benchmark report or visualization to file"
    )
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

@click.group()
def cli():
    """
    a benchmark and scalability test of IIIF Annotation servers, and especially aiiinotate
    """

@cli.command
@click.argument(
    "server",
    type=click.STRING,
    required=True,
    help="the annotation server to test"
)
@click.option(
    "-e", "--endpoint",
    type=click.STRING,
    help="the endpoint on which the annotation server is listening (including http(s) scheme and port, if needed)"
)
@click.option(
    "-s", "--steps",
    type=int,
    required=False,
    default=N_STEPS_DEFAULT,
    help=f"number of step groups to run (in range (1..{len(STEPS)+1}))"
)
@click.option(
    "-t", "--threads",
    type=int,
    required=False,
    default=THREADS_DEFAULT,
    help=f"number of threads to use when populating database (default={THREADS_DEFAULT})"
)
@click.option(
    "-n", "--nowrite",
    type=click.BOOL,
    is_flag=True,
    default=False,
    help="do not write the benchmark report to file"
)
def benchmark(
    server: str,
    endpoint: str,
    steps: int,
    threads: int,
    nowrite: bool,
):
    """
    run a benchmark
    """
    benchmark_runner(
        server=server,
        endpoint=endpoint,
        n_steps=steps,
        threads=threads,
        nowrite=nowrite
    )

