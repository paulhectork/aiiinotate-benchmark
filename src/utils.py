import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
import orjson

from src.constants import PATH_OUT, PATH_ROOT, MONGODB_HOST, MONGODB_PORT, DB_NAME


def orjson_deepcopy(d: dict) -> dict:
    """optimized alternative of copy.deepcopy"""
    return orjson.loads(orjson.dumps(d))

def bytes_to_str(b: bytes) -> str:
    return b.decode("utf-8")

# # NOTE unused
# def sanitize_surrogates(obj):
#     """avoid orjson parsing errors when writing JSON objs to file."""
#     if isinstance(obj, str):
#         return obj.encode("utf-8", errors="replace").decode("utf-8")
#     elif isinstance(obj, dict):
#         return {k: sanitize_surrogates(v) for k, v in obj.items()}
#     elif isinstance(obj, list):
#         return [sanitize_surrogates(i) for i in obj]
#     return obj

def json_parse(d: str|bytes) -> Dict:
    """parse a string to a Dict"""
    if isinstance(d, str):
        d = d.encode("utf-8")
    return orjson.loads(d)

def json_dumps(d: dict|list, indent=True) -> bytes:
    if indent:
        d_b = orjson.dumps(d, option=orjson.OPT_INDENT_2 if indent else None)
    else:
        d_b = orjson.dumps(d)
    return d_b.decode("utf-8").encode("utf-8")

def json_read(fp: Path) -> Dict:
    with open(fp, mode="rb") as fh:
        import json
        return json.load(fh)
        # return json_parse(fh.read())

def json_write(fp: str|Path, d: dict, indent=True) -> None:
    with open(fp, mode="wb") as fh:
        d_str = json_dumps(d, indent)
        fh.write(d_str)

def write_report(basename: str, report: Dict) -> None:
    if not PATH_OUT.exists():
        PATH_OUT.mkdir()
    json_write(PATH_OUT / f"{basename}.json", report, True)
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


def run_bash(bash_command: str) -> None:
    result = subprocess.run(bash_command, shell=True)
    if result.returncode != 0:
        print("> run_bash: bash command:", str)
        print("> run_bash: subprocess stout:", result.stdout)
        print("> run_bash: subprocess stderr:", result.stderr)
        raise subprocess.SubprocessError(f"run_bash exited with non 0 status code for command {bash_command}")
