import json
import pathlib
from pathlib import Path
from typing import Dict, List

PATH_SRC = pathlib.Path(__file__).parent.resolve()
PATH_ROOT = PATH_SRC.parent.resolve()
PATH_DATA = pathlib.Path(PATH_ROOT / "data").resolve()
PATH_MANIFEST_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_manifest.jsonld"
PATH_ANNOTATION_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_annotation.jsonld"
PATH_CANVAS_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_canvas.jsonld"

def read_json(fp: Path) -> Dict:
    with open(fp, mode="r", encoding="utf-8") as fh:
        return json.load(fh)

def pprint(jsonlike: Dict|List) -> None:
    print(json.dumps(jsonlike, indent=2))