from typing import Dict, List, Tuple, Optional

import requests

from .adapter_core import AdapterCore
from .utils import get_canvas_ids

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

    def insert_annotation_list(self, annotation_list: Dict):
        """insert an AnnotationList"""
        r = requests.post(
            f"{self.endpoint}/annotation/populate",
            json=annotation_list
        )
        print(r.status_code)
        print(r.text)
        raise NotImplementedError()

    # TODO delete ?
    def get_manifest(self):
        """read a single manifest"""
        raise NotImplementedError("AdapterSas.get_manifest")

    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        r = requests.get(f"{self.endpoint}/manifests")
        return r.json()

    def get_annotation_list(self, id_canvas: str):
        """read annotations into an annotationList ('search' route ?)"""
        r = requests.get(f"{self.endpoint}/annotation/search?uri=${id_canvas}")
        assert r.status_code == 200
        return r.json()

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

    def update_annotation(self, id_annotation):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_annotation")

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_manifest")

