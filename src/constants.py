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
# list of [n_manifest, n_canvas, n_annotations]
# max #ann = 10K (to be realistic)

# canvas-ot-annotation ratio (in 0..1 rangw): insert annotations on 10% of canvases
# on one production instance of aiiinotate, RATIO is closer to 0.4. see notes below.
RATIO = 0.1

# steps of the benchmark, defined as a list of
# ```
# (n_manifest, n_canvases_per_manifest)
# ```
#
# the table below summarizes the number of manifests, canvases and annotations in the
# entire database at each step. the formulas used to get the values are:
# ```
# >>> total_canvases    = n_manifest * n_annotations
# >>> total_annotations = n_manifest * n_annotations * RATIO
# ```
#
#    manifests   canvases/manifest   total canvases    annotations
# ----------------------------------------------------------------
#            1             100                  100             10
#            1           1,000                1,000            100
#           10           1,000               10,000          1,000
#          100           1,000              100,000         10,000
#        1,000           1,000            1,000,000        100,000
#       10,000           1,000           10,000,000      1,000,000
#      100,000           1,000          100,000,000     10,000,000
#    1,000,000           1,000        1,000,000,000    100,000,000
#
# we have MUCH more canvases than annotations in the DB: annotations and
# images are on a small subset of all the pages of a document. depending on RATIO,
# this can vary (canvas-to-annotation ratio = 1/RATIO).
#
# to verify the actual RATIO on a production database,
# 1. get the total number of canvas with the query:
# ```
# >>> db.manifests2.aggregate([ {
# ...   $group: {
# ...       _id: null,
# ...       n_canvas_total: { $sum: { $size: "$canvasIds" }
# ...   }
# ... }]);
# ```
# 2. get the total number of annotations with:
# ```
# >>> db.annotations2.countDocuments();
# ```
# 3. get the actual ratio with:
# ```
# >>> RATIO = n_annotations / n_canvas_total
# ```
STEPS = [
    (1,           100),   #       1   ×   100 × 0.1 =          10
    (1,         1_000),   #       1   × 1_000 × 0.1 =         100
    (10,        1_000),   #      10   × 1_000 × 0.1 =       1_000
    (100,       1_000),   #     100   × 1_000 × 0.1 =      10_000
    (1_000,     1_000),   #   1_000   × 1_000 × 0.1 =     100_000
    (10_000,    1_000),   #  10_000   × 1_000 × 0.1 =   1_000_000
    (100_000,   1_000),   # 100_000   × 1_000 × 0.1 =  10_000_000
    (1_000_000, 1_000),   # 1_000_000 × 1_000 × 0.1 = 100_000_000
]

# default nyumber of benchmark steps to run
N_STEPS_DEFAULT = 3

# default number of threads to use
THREADS_DEFAULT = 20