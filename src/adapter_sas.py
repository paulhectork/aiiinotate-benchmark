from typing import Dict, List, Tuple, Optional

import requests

from .adapter_core import AdapterCore
from .utils import get_canvas_ids, get_manifest_short_id

class AdapterSas(AdapterCore):
    def __init__(self, endpoint):
        super().__init__(endpoint)
        return

    @property
    def server_name(self):
        return "SimpleAnnotationServer"

    def insert_manifest(self, manifest: Dict) -> List[Optional[str]]:
        """insert a single manifest"""
        r = requests.post(
            f"{self.endpoint}/manifests",
            json=manifest
        )
        r_json = r.json()  # { loaded: <manifestId> }
        return (
            get_canvas_ids(manifest)
            if "loaded" in r_json.keys()
            and len(r_json["loaded"]) > 1
            else []
        )

    def insert_annotation(self, annotation:Dict):
        r = requests.post(
            f"{self.endpoint}/annotation/create",
            json=annotation
        )
        return 1 if "@id" in r.json().keys() else 0

    #NOTE: for some obscure reason, SAS can take A LOT of time to send a response
    def insert_annotation_list(self, annotation_list: Dict):
        """
        insert an AnnotationList
        in SAS, you can only create annotations from an annotation list through an HTML page... annotations must be inserted manually
        => we use self.insert_annotations to insert annotations one by one.
        """
        r_all = []
        for annotation in annotation_list["resources"]:
            r_all.append(self.insert_annotation(annotation))
        return 1 if len(set(r_all)) == 1 and r_all[0] == 1 else 0

    def get_manifest(self):
        """read a single manifest"""


    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        r = requests.get(f"{self.endpoint}/manifests")
        return r.json()

    def get_annotation_list(self, id_canvas: str):
        """read annotations into an annotationList ('search' route ?)"""
        r = requests.get(f"{self.endpoint}/annotation/search?uri=${id_canvas}")
        assert r.status_code == 200
        return r.json()

    # NOTE: this functionnality is not implemented by SAS
    def delete_manifest(self, id_manifest: str):
        """delete an annotation"""
        raise NotImplementedError("AdapterSas.delete_manifest")

    def delete_annotation(self, id_annotation: str):
        """delete an annotation"""
        r = requests.delete(f"{self.endpoint}/annotation/destroy?uri={id_annotation}")
        print(r.status_code)
        print(r.json())

    def delete_annotations_for_canvas(self, id_canvas:str):
        annotation_list = self.get_annotation_list(id_canvas)
        list_id_annotation = [
            a["@id"] for a in annotation_list["resources"]
        ]
        for id_annotation in list_id_annotation:
            self.delete_annotation(id_annotation)
        return

    def delete_annotations_for_manifest(self, id_manifest:str):
        id_manifest = get_manifest_short_id(id_manifest)
        r = requests.get(f"{self.endpoint}/search-api/${id_manifest}/search")
        annotation_list = r.json()
        for annotation in annotation_list["resources"]:
            self.delete_annotation(annotation["@id"])

    def update_annotation(self, id_annotation):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_annotation")

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_manifest")

