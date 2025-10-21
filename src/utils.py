import json
import pathlib
from pathlib import Path
from typing import Dict, List, Optional

PATH_SRC = pathlib.Path(__file__).parent.resolve()
PATH_ROOT = PATH_SRC.parent.resolve()
PATH_DATA = pathlib.Path(PATH_ROOT / "data").resolve()
PATH_MANIFEST_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_manifest.jsonld"
PATH_ANNOTATION_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_annotation.jsonld"
PATH_CANVAS_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_canvas.jsonld"

def read_json(fp: Path) -> Dict:
    with open(fp, mode="r", encoding="utf-8") as fh:
        return json.load(fh)

def pprint(jsonlike: Dict|List, maxlen=-1) -> None:
    """
    pretty-print a json-like object, and optionnally print only 'maxlen' lines.

    :param jsonlike: object to print
    :param maxlen: maximum number of lines to print, or -1 to print all
    """
    s = json.dumps(jsonlike, indent=2)
    s_lines = s.split("\n")
    s_len = len(s_lines)
    if (maxlen != -1 and maxlen < s_len):
        s_keep = round(maxlen/2)  # numbr of start/end lines to keep in `s`
        s_lines = s_lines[:s_keep] + [f"\n... {s_len - maxlen} LINES OMITTED (TOTAL={s_len} lines) ...\n"] + s_lines[-s_keep:]
        s = "\n".join(s_lines)
    print(s)

def get_manifest_short_id(id_manifest:str) -> str:
    # manifest URI pattern: {scheme}://{host}/{prefix}/{identifier}/manifest
    # => get 'identifier'
    return id_manifest.split("/")[-2]


def get_canvas_ids(manifest: Dict) -> List[Optional[str]]:
    return [ c["@id"] for c in manifest["sequences"][0]["canvases"] ]
