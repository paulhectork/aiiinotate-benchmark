from src.benchmark import Benchmark
from src.constants import N_STEPS_DEFAULT, THREADS_DEFAULT


def runner(
    server: str,
    endpoint: str,
    n_steps: int = N_STEPS_DEFAULT,
    threads: int|None = THREADS_DEFAULT,
    nowrite: bool = False,
) -> None:
    Benchmark(
        server=server,
        endpoint=endpoint,
        n_steps=n_steps,
        threads=threads,
        nowrite=nowrite
    ).run()
