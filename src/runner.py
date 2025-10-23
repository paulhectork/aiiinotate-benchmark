from .adapter_aiiinotate import AdapterAiiinotate
from .adapter_sas import AdapterSas
from .benchmark import Benchmark
from .utils import N_STEPS_DEFAULT, RATIO_DEFAULT


def runner(
    server: str,
    endpoint: str,
    n_steps: int = N_STEPS_DEFAULT,
    ratio: float|None = RATIO_DEFAULT
) -> None:
    Benchmark(
        server=server,
        endpoint=endpoint,
        n_steps=n_steps,
        ratio=ratio
    ).run()
