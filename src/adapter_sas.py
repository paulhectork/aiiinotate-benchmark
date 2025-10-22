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

    def get_annotation_list(self):
        """read annotations into an annotationList ('search' route ?)"""
        raise NotImplementedError("AdapterSas.get_annotation_list")

    def delete_manifest(self, id_manifest: str):
        """delete an annotation"""
        raise NotImplementedError("AdapterSas.delete_manifest")

    def delete_annotation(self, id_annotation: str):
        """delete an annotation"""
        r = requests.delete(f"{self.endpoint}/annotation/destroy?uri={id_annotation}")
        print(r.status_code)
        print(r.json())

    def update_annotation(self, id_annotation):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_annotation")

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_manifest")

