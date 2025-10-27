from pathlib import Path
from itertools import chain


PATH_SRC = Path(__file__).parent.resolve()
PATH_ROOT = PATH_SRC.parent.resolve()
PATH_DATA = Path(PATH_ROOT / "data").resolve()
PATH_MANIFEST_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_manifest.jsonld"
PATH_ANNOTATION_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_annotation.jsonld"
PATH_CANVAS_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_canvas.jsonld"
PATH_OUT = PATH_ROOT / "out"

#NOTE: on the cli-side, seps are organised in grops: STEPS_GROUPS (1 group / number of manifests).
# in the code-side, steps are not grouped: see STEPS_FLAT.
# list of list of [n_canvas, n_manifest]
STEPS_GROUP = [
    [
        [10, 10],
        [10,100],
        [10,100],
    ],
    [
        [100, 100],
        [100, 1000],
        [100, 10000],
    ],
    [
        [1000, 100],
        [1000, 1000],
        [1000, 10000],
    ],
    [
        [10000, 100],
        [10000, 1000],
        [10000, 10000],
    ],
    [
        [100000, 100],
        [100000, 1000],
        [100000, 10000],
    ],
    [
        [1000000, 100],
        [1000000, 1000],
        [1000000, 10000],
    ]
]

# used to define n_steps in cli
STEPS_GROUP_RANGE = [1, len(STEPS_GROUP)]

# flattened variant of the above, that will actually be used.
STEPS_FLAT = list(chain.from_iterable(STEPS_GROUP))

# number of step groups to run in the benchmark
N_STEPS_DEFAULT = 2

# default number of threads to use
THREADS_DEFAULT = 20

# canvases with annotations / canvases without annotations
RATIO_DEFAULT= 0.01
