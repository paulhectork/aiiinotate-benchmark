import json
import pathlib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

PATH_SRC = pathlib.Path(__file__).parent.resolve()
PATH_ROOT = PATH_SRC.parent.resolve()
PATH_DATA = pathlib.Path(PATH_ROOT / "data").resolve()
PATH_MANIFEST_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_manifest.jsonld"
PATH_ANNOTATION_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_annotation.jsonld"
PATH_CANVAS_2_TEMPLATE = PATH_DATA / "iiif_presentation_2_canvas.jsonld"
PATH_OUT = PATH_ROOT / "out"

def read_json(fp: Path) -> Dict:
    with open(fp, mode="r", encoding="utf-8") as fh:
        return json.load(fh)

def write_log(server_name:str, log: Dict) -> None:
    if not PATH_OUT.exists():
        PATH_OUT.mkdir()
    out_name = f"log_benchmark_{server_name}_{datetime.now().strftime(r'%Y-%m-%d-%H:%M:%S')}.json"
    with open(PATH_OUT / out_name, mode="w", encoding="utf-8") as fh:
        json.dump(log, fh, indent=2)
    return

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

def get_manifest_short_id(iiif_uri:str) -> str:
    """
    extract {identifier} from the following IIIF 2.x URIs:

    Collection 	             {scheme}://{host}/{prefix}/collection/{name}
    Manifest 	             {scheme}://{host}/{prefix}/{identifier}/manifest
    Sequence 	             {scheme}://{host}/{prefix}/{identifier}/sequence/{name}
    Canvas 	                 {scheme}://{host}/{prefix}/{identifier}/canvas/{name}
    Annotation (incl images) {scheme}://{host}/{prefix}/{identifier}/annotation/{name}
    AnnotationList           {scheme}://{host}/{prefix}/{identifier}/list/{name}
    Range 	                 {scheme}://{host}/{prefix}/{identifier}/range/{name}
    Layer 	                 {scheme}://{host}/{prefix}/{identifier}/layer/{name}
    Content 	             {scheme}://{host}/{prefix}/{identifier}/res/{name}.{format}
    """
    keywords = ["manifest", "manifest.json", "sequence", "canvas", "annotation", "list", "range", "layer", "res"]
    iiif_uri_arr = iiif_uri.split("/")
    id_short = ""
    for kw in keywords:
        if kw in iiif_uri_arr:
            id_short = iiif_uri_arr[ iiif_uri_arr.index(kw) -1 ]
            break
    if id_short == "":
        raise ValueError(f"could not extract a manifest short ID from '{iiif_uri}'")
    return id_short

def get_canvas_ids(manifest: Dict) -> List[Optional[str]]:
    return [ c["@id"] for c in manifest["sequences"][0]["canvases"] ]
