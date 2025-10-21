from typing import List, Dict, Tuple, Generator
from uuid import uuid4
import random
import string

from tqdm import tqdm

from .utils import PATH_CANVAS_2_TEMPLATE, PATH_MANIFEST_2_TEMPLATE, PATH_ANNOTATION_2_TEMPLATE, read_json, pprint


# NOTE: since we generate fake "@id"s the benchmark for aiiinotate won't be truthful
# a big insert bottleneck is having to fetch manifest @ids for each inserted annotation.

annotation_2_template = read_json(PATH_ANNOTATION_2_TEMPLATE)
manifest_2_template = read_json(PATH_MANIFEST_2_TEMPLATE)
canvas_2_template = read_json(PATH_CANVAS_2_TEMPLATE)


def generate_random_string(length):
    ## Generate random string with ASCII letters and digits
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def mkstr():
    """generate a random, (pseudo-) unique value."""
    # return generate_random_string(15)  # NOTE: ~12 it/s
    return uuid4()  # NOTE: ~25 it/s


def generate_annotation(id_canvas:str) -> Dict:
    annotation = annotation_2_template
    annotation["@id"] = f"http://aikon.enpc.fr/sas/annotation/id_{mkstr()}"
    annotation["on"] = id_canvas
    return annotation

def generate_annotation_list(id_canvas, n_annotations:int) -> Dict:
    """generate an annotationlist on canvas `id_canvas` with `n` annotations"""
    #TODO
    return {}

def generate_canvas(id_manifest:str) -> Dict:
    canvas = canvas_2_template
    folio = f"f_{mkstr()}"
    id_canvas = id_manifest.replace("/manifest.json", "") + f"/{folio}"
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
    manifest = manifest_2_template
    id_manifest = f"https://gallica.bnf.fr/iiif/ark:/12148/{mkstr()}/manifest.json"
    manifest["@id"] = id_manifest
    manifest["sequences"][0]["canvases"] = generate_canvases(id_manifest, n_canvas)
    return manifest

def generate_manifests(n_manifest:int=1000, n_canvas:int=1000) -> Generator[Dict, Tuple[int,int], None]:
    # for _ in tqdm(range(n_manifest), desc=f"generating {n_manifest} manifests with {n_canvas} canvases"):
    for _ in range(n_manifest):
        yield generate_manifest(n_canvas)
    return

# TODO: find a way to pass list_id_canvas or change code.
def generate_annotation_lists(list_id_canvas: List[str], n_annotation:int=100) -> Generator[Dict, Tuple[List[str], int], None]:
    for id_canvas in tqdm(list_id_canvas, desc=f"generating {len(list_id_canvas)} annotation lists with {n_annotation} annotations each"):
        yield generate_annotation_list(id_canvas, n_annotation)
    return
