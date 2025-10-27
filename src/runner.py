from .benchmark import Benchmark
from .constants import N_STEPS_DEFAULT, RATIO_DEFAULT, THREADS_DEFAULT


def runner(
    server: str,
    endpoint: str,
    n_steps: int = N_STEPS_DEFAULT,
    ratio: float|None = RATIO_DEFAULT,
    threads: int|None = THREADS_DEFAULT,
    nowrite: bool = False,
) -> None:
    Benchmark(
        server=server,
        endpoint=endpoint,
        n_steps=n_steps,
        ratio=ratio,
        threads=threads,
        nowrite=nowrite
    ).run()
