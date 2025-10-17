from typing import List, Dict
from uuid import uuid4

from .utils import PATH_CANVAS_2_TEMPLATE, PATH_MANIFEST_2_TEMPLATE, PATH_ANNOTATION_2_TEMPLATE, read_json, pprint


# NOTE: since we generate fake "@id"s the benchmark for aiiinotate won't be truthful
# a big insert bottleneck is having to fetch manifest @ids for each inserted annotation.

annotation_2_template = read_json(PATH_ANNOTATION_2_TEMPLATE)
manifest_2_template = read_json(PATH_MANIFEST_2_TEMPLATE)
canvas_2_template = read_json(PATH_CANVAS_2_TEMPLATE)

def generate_annotation(n:int=1000) -> List[Dict]:
    list_annotation = []
    for _ in range(n):
        annotation = annotation_2_template
        annotation["@id"] = f"http://aikon.enpc.fr/sas/annotation/id_{uuid4()}"
        annotation["on"] = f"https://aikon.enpc.fr/aikon/iiif/v2/{uuid4()}/canvas/c_${uuid4()}.json#xywh=5,0,1824,2161"
        list_annotation.append(annotation)
    return list_annotation

def generate_canvas(canvas: Dict) -> Dict:
    folio = f"f_{uuid4()}"
    canvas_id = "/".join(canvas["@id"].split("/")[:-1]) + f"/{folio}"
    img_id = f"https://gallica.bnf.fr/iiif/ark:/12148/{uuid4()}/{folio}/full/full/0/native.jpg"
    canvas["@id"] = canvas_id
    canvas["images"][0]["@id"] = img_id
    canvas["images"][0]["resource"]["service"]["@id"] = canvas_id
    return canvas

def generate_sequence(n=1000) -> List[Dict]:
    return [
        generate_canvas(canvas_2_template) for i in range(n)
    ]

def generate_manifest(n:int=1000) -> List[Dict]:
    list_manifest = []
    for _ in range(n):
        manifest = manifest_2_template
        manifest["@id"] = "https://gallica.bnf.fr/iiif/ark:/12148/btv1b8490076p/manifest.json";
        list_manifest.append(manifest)
    return list_manifest

x = generate_annotation(100000)
pprint(x)
print(len(x))