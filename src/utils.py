from pathlib import Path
from typing import Dict, List, Optional

import orjson

from src.constants import PATH_OUT

def orjson_deepcopy(d: dict) -> dict:
    """optimized alternative of copy.deepcopy"""
    return orjson.loads(orjson.dumps(d))

def bytes_to_str(b: bytes) -> str:
    return b.decode("utf-8")

def json_parse(d: str|bytes) -> Dict:
    """parse a string to a Dict"""
    return orjson.loads(d)

def json_dumps(d: dict|list) -> bytes:
    return orjson.dumps(d, option=orjson.OPT_INDENT_2)

def json_read(fp: Path) -> Dict:
    with open(fp, mode="rb") as fh:
        return json_parse(fh.read())

def json_write(fp: str|Path, d: dict) -> None:
    with open(fp, mode="wb") as fh:
        d_str = json_dumps(d)
        fh.write(d_str)

def write_report(basename: str, report: Dict) -> None:
    if not PATH_OUT.exists():
        PATH_OUT.mkdir()
    with open(PATH_OUT / f"{basename}.json", mode="wb") as fh:
        report_bytes = orjson.dumps(report, option=orjson.OPT_INDENT_2)
        fh.write(report_bytes)
    return

def pprint(jsonlike: Dict|List, maxlen=-1) -> None:
    """
    pretty-print a json-like object, and optionnally print only 'maxlen' lines.

    :param jsonlike: object to print
    :param maxlen: maximum number of lines to print, or -1 to print all
    """
    s = bytes_to_str(orjson.dumps(jsonlike, option=orjson.OPT_INDENT_2))  # pyright: ignore
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
