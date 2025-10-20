from typing import List, Dict, Tuple
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

def generate_canvas() -> Dict:
    canvas = canvas_2_template
    folio = f"f_{mkstr()}"
    id_canvas = "/".join(canvas["@id"].split("/")[:-1]) + f"/{folio}"
    id_img = f"https://gallica.bnf.fr/iiif/ark:/12148/{mkstr()}/{folio}/full/full/0/native.jpg"
    canvas["@id"] = id_canvas
    canvas["images"][0]["@id"] = id_img
    canvas["images"][0]["resource"]["service"]["@id"] = id_canvas
    return canvas

def generate_canvases(n_canvas=1000) -> List[Dict]:
    return [
        generate_canvas() for _ in range(n_canvas)
    ]

def generate_manifest(n_canvas:int=1000) -> Dict:
    manifest = manifest_2_template
    manifest["@id"] = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8490076p/manifest.json"
    manifest["sequences"][0]["canvases"] = generate_canvases(n_canvas)
    return manifest

def generate_manifests(n_manifest:int=1000, n_canvas:int=1000) -> List[Dict]:
    list_manifest = []
    for _ in tqdm(range(n_manifest), desc=f"generating {n_manifest} manifests with {n_canvas} canvases"):
        list_manifest.append(generate_manifest(n_canvas))
    return list_manifest

def generate_annotation_lists(list_id_canvas: List[str], n_annotation:int=100) -> List[Dict]:
    list_annotation_list = []
    for id_canvas in tqdm(list_id_canvas, desc=f"generating {len(list_id_canvas)} annotation lists with {n_annotation} annotations each"):
        list_annotation_list.append(generate_annotation_list(id_canvas, n_annotation))
    return list_annotation_list

def generate_all(n_manifest:int=1000, n_canvas:int=1000, n_annotation:int=100) -> Tuple[List[Dict], List[Dict]]:
    """
    :param n_manifest: number of manifests to generate
    :param n_canvas: number of canvases / manifest
    :param n_annotation: number of annotations / canvas
    """
    list_manifest = []
    list_annotation_list = []

    if n_manifest > 0:
        list_manifest = generate_manifests(n_manifest, n_canvas)

    if (n_annotation > 0):
        list_id_canvas = [
            canvas["@id"]
            for manifest in list_manifest
            for canvas in manifest["sequences"][0]["canvases"]
        ]
        list_annotation_list = generate_annotation_lists(list_id_canvas, n_annotation)
    return list_manifest, list_annotation_list

