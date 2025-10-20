class AdapterCore:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        return

    def benchmark():
        # steps:
        # 1.000 manifests / 10.000 anno, (10/canvas)
        # 10.000 manifests / 1.000 canvases / 100.000 anno.
        # 100.000 manifests / 1.000.000 anno.
        # 1.000.000 manifests / 10.000.000 anno.
        # annotations are randomly inserted, with a rate of ??? annotations / canvas.
        # NOTE: for now, each manifest will contain 1000 annotations.

        steps = [
            [1000, 10000],
            [10000, 100000],
            [100000, 1000000],
            [1000000, 10000000],
        ]
        for ( n_manifest, n_annotation ) in steps:
            ...