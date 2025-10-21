from typing import Dict, List, Tuple, Optional

import requests

from .adapter_core import AdapterCore
from .utils import get_canvas_ids

class AdapterSas(AdapterCore):
    def __init__(self, endpoint):
        super().__init__(endpoint)
        return

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
        raise NotImplementedError("AdapterCore.get_manifest")

    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        r = requests.get(f"{self.endpoint}/manifests")
        return r.json()

    def get_annotation_list(self):
        """read annotations into an annotationList ('search' route ?)"""
        raise NotImplementedError("AdapterCore.get_annotation_list")

    def delete_manifest(self, id_manifest: str):
        """delete an annotation"""
        raise NotImplementedError("AdapterCore.delete_manifest")

    def delete_annotation(self, id_annotation: str):
        """delete an annotation"""
        raise NotImplementedError("AdapterCore.delete_annotation")

    def update_annotation(self, id_annotation):
        """update an annotation"""
        raise NotImplementedError("AdapterCore.update_annotation")

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterCore.update_manifest")

