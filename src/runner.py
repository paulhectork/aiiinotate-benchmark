from src.adapter_aiiinotate import AdapterAiiinotate
from src.adapter_sas import AdapterSas
from src.benchmark import Benchmark


def runner(server: str, endpoint: str) -> None:
    if server == "aiiinotate":
        adapter = AdapterAiiinotate(endpoint)
    else:
        adapter = AdapterSas(endpoint)

    # n_manifest: is multiplie by 10 at each step
    # n_canvas: 3 different # of canvases per manifest: 100, 1000, 10000
    Benchmark(adapter, [
        [100, 100],
        [100, 1000],
        [100, 10000],

        # [1000, 100],
        # [1000, 1000],
        # [1000, 10000],

        # [10000, 100],
        # [10000, 1000],
        # [10000, 10000],

        # [100000, 100],
        # [100000, 1000],
        # [100000, 10000],

        # [1000000, 100],
        # [1000000, 1000],
        # [1000000, 10000],
    ]).run()
