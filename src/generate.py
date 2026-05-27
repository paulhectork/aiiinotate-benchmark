from typing import List, Dict, Tuple, Generator
from uuid import uuid4

import random
import string

from src.utils import json_read, pprint, get_manifest_short_id, orjson_deepcopy
from src.constants import  PATH_CANVAS_2_TEMPLATE, PATH_MANIFEST_2_TEMPLATE, PATH_ANNOTATION_2_TEMPLATE


# NOTE: a big insert bottleneck when inserting annotations is having to fetch the manifest in order to extract the canVasIdx
# fetching a manifest through HTTP is both
# - non-determistic: execution time is entierly out of our control
# - not dependent on the database size (fetching a manifest when your db has 100M manifests will take the same time as when it's empty)
# in turn, we put manifest @ids on a closed localhost port. this means:
# - that HTTP fetches fail almost instantly => more deterministic
# - that benchmarked insert times are much faster than actual insert times.
URI_ROOT = "https://localhost"

annotation_2_template = json_read(PATH_ANNOTATION_2_TEMPLATE)
manifest_2_template = json_read(PATH_MANIFEST_2_TEMPLATE)
canvas_2_template = json_read(PATH_CANVAS_2_TEMPLATE)

def generate_random_string(length):
    ## Generate random string with ASCII letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def mkstr():
    """generate a random, (pseudo-) unique value."""
    # return generate_random_string(15)  # NOTE: ~12 it/s
    return str(uuid4())  # NOTE: ~25 it/s

def make_manifest_uri(short_id: str) -> str:
    return f"{URI_ROOT}/{short_id}/manifest.json"

def generate_annotation(short_id: str, id_canvas:str) -> Dict:
    annotation = orjson_deepcopy(annotation_2_template)
    annotation["@id"] = f"{URI_ROOT}/{short_id}/annotation/id_{mkstr()}"
    annotation["on"] = f"{id_canvas}#xywh=5,0,1824,2161"
    return annotation

def generate_annotation_list(id_canvas, n_annotations:int) -> Dict:
    """generate an annotationlist on canvas `id_canvas` with `n` annotations"""
    # AnnotationList URI: {scheme}://{host}/{prefix}/{identifier}/list/{name}
    short_id = get_manifest_short_id(id_canvas)
    return {
        "@context": "http://iiif.io/api/presentation/2/context.json",
        "@type": "sc:AnnotationList",
        "@id": f"{URI_ROOT}/{short_id}/list/l_{uuid4()}",
        "resources": [
            generate_annotation(short_id, id_canvas)
            for _ in range(n_annotations)
        ]
    }

def generate_canvas(id_manifest:str) -> Dict:
    canvas = orjson_deepcopy(canvas_2_template)
    folio = f"f_{mkstr()}"
    id_canvas = id_manifest.replace("/manifest.json", "") + f"/canvas/{folio}"
    id_img = f"{id_canvas}/full/full/0/native.jpg"
    canvas["@id"] = id_canvas
    canvas["images"][0]["@id"] = id_img
    canvas["images"][0]["resource"]["service"]["@id"] = id_canvas
    return canvas

def generate_canvases(id_manifest:str, n_canvas=1000) -> List[Dict]:
    return [
        generate_canvas(id_manifest) for _ in range(n_canvas)
    ]

def generate_manifest(n_canvas:int=1000) -> Dict:
    manifest = orjson_deepcopy(manifest_2_template)
    id_manifest = make_manifest_uri(mkstr())
    manifest["@id"] = id_manifest
    manifest["sequences"][0]["canvases"] = generate_canvases(id_manifest, n_canvas)
    return manifest

def generate_manifest_index(n_canvas:int=1000) -> Dict:
    """generate a manifest index as it is stored in aiiinotate"""
    short_id = mkstr()
    id_manifest = make_manifest_uri(short_id)
    return {
        "@id": id_manifest,
        "manifestShortId": short_id,
        "@type": "sc:Manifest",
        "canvasIds": generate_canvases(id_manifest)
    }

def generate_annotations(list_id_canvas:List[str]) -> Generator[Dict, List[int], None]:
    """
    generator creating 1 annotation per id_canvas in `list_id_canvas`
    """
    for id_canvas in list_id_canvas:
        short_id = get_manifest_short_id(id_canvas)
        yield generate_annotation(short_id, id_canvas)
    return

def generate_manifests(n_manifest:int=1000, n_canvas:int=1000) -> Generator[Dict, Tuple[int,int], None]:
    """
    generator creating `n_manifest` manifests with `n_canvas` canvases each
    """
    for _ in range(n_manifest):
        yield generate_manifest(n_canvas)
    return

def generate_manifest_indexes(n_manifest: int=1000, n_canvas:int=1000) -> Generator[Dict, Tuple[int,int], None]:
    for _ in range(n_manifest):
        yield generate_manifest_index(n_canvas)
    return

def generate_annotation_lists(list_id_canvas: List[str], n_annotation:int=100) -> Generator[Dict, Tuple[List[str], int], None]:
    """
    generator creating 1 annotation list per id_canvas in `list_id_canvas`, with `n_annotation` annotations each
    """
    for id_canvas in list_id_canvas:
        yield generate_annotation_list(id_canvas, n_annotation)
    return
