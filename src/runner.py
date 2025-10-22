from src.adapter_aiiinotate import AdapterAiiinotate
from src.adapter_sas import AdapterSas
from src.benchmark import Benchmark


def runner(server: str, endpoint: str) -> None:
    if server == "aiiinotate":
        adapter = AdapterAiiinotate(endpoint)
    else:
        adapter = AdapterSas(endpoint)

    Benchmark(adapter, [
        [100, 100],
        [1000, 1000],
        # [1000, 10000],
        # [10000, 10000],
        # [10000, 100000],
        # [100000, 100000],
        # [1000000, 1000000],
    ]).run()
