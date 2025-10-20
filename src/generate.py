from typing import List, Dict, Tuple
from uuid import uuid4

from .utils import PATH_CANVAS_2_TEMPLATE, PATH_MANIFEST_2_TEMPLATE, PATH_ANNOTATION_2_TEMPLATE, read_json, pprint


# NOTE: since we generate fake "@id"s the benchmark for aiiinotate won't be truthful
# a big insert bottleneck is having to fetch manifest @ids for each inserted annotation.

annotation_2_template = read_json(PATH_ANNOTATION_2_TEMPLATE)
manifest_2_template = read_json(PATH_MANIFEST_2_TEMPLATE)
canvas_2_template = read_json(PATH_CANVAS_2_TEMPLATE)

def generate_annotation(id_canvas:str) -> Dict:
    annotation = annotation_2_template
    annotation["@id"] = f"http://aikon.enpc.fr/sas/annotation/id_{uuid4()}"
    annotation["on"] = id_canvas
    return annotation

def generate_annotationlist(id_canvas, n_annotations:int) -> Dict:
    """generate an annotationlist on canvas `id_canvas` with `n` annotations"""
    # f"https://aikon.enpc.fr/aikon/iiif/v2/{uuid4()}/canvas/c_${uuid4()}.json#xywh=5,0,1824,2161"
    return {}

def generate_canvas() -> Dict:
    canvas = canvas_2_template
    folio = f"f_{uuid4()}"
    id_canvas = "/".join(canvas["@id"].split("/")[:-1]) + f"/{folio}"
    id_img = f"https://gallica.bnf.fr/iiif/ark:/12148/{uuid4()}/{folio}/full/full/0/native.jpg"
    canvas["@id"] = id_canvas
    canvas["images"][0]["@id"] = id_img
    canvas["images"][0]["resource"]["service"]["@id"] = id_canvas
    return canvas

def generate_canvas_list(n_canvas=1000) -> List[Dict]:
    return [
        generate_canvas() for _ in range(n_canvas)
    ]
def generate_manifest(n_canvas:int=1000) -> Dict:
    manifest = manifest_2_template
    manifest["@id"] = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8490076p/manifest.json"
    manifest["sequence"]["canvases"] = generate_canvas_list(n_canvas)
    return manifest

def generate_manifest_list(n_manifest:int=1000, n_canvas:int=1000) -> List[Dict]:
    return [
        generate_manifest(n_canvas) for _ in range(n_manifest)
    ]

def generate_all(n_manifest:int=1000, n_canvas:int=1000, n_annotation:int=100) -> Tuple[List[Dict], List[Dict]]:
    """
    :param n_manifest: number of manifests to generate
    :param n_canvas: number of canvases / manifest
    :param n_annotation: number of annotations / canvas
    """
    list_manifest = []
    list_annotationlist = []

    if n_manifest > 0:
        list_manifest = generate_manifest_list(n_manifest, n_canvas)

    if (n_annotation > 0):
        id_canvas_list = [
            canvas["@id"] for manifest in list_manifest
            for canvas in manifest["sequence"][0]
        ]
        list_annotationlist = [
            generate_annotationlist(id_canvas, n_annotation)
            for id_canvas in id_canvas_list
        ]
    return list_manifest, list_annotationlist

