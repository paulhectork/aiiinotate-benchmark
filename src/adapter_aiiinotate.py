from typing import Dict, List, Tuple

import requests

from .adapter_core import AdapterCore
from .utils import pprint


class AdapterAiiinotate(AdapterCore):
    def __init__(self, endpoint):
        super().__init__(endpoint)
        return

    def insert_manifest(self, manifest: Dict) -> int:
        """insert a single manifest"""
        r = requests.post(
            f"{self.endpoint}/manifests/2/create",
            json=manifest
        )
        r_data = r.json()
        # returns 1 if something has been inserted, 0 otherwise.
        return (
            1
            if "insertedCount" in r_data.keys()
            and r_data["insertedCount"] > 0
            else 0
        )

    def insert_annotation_list(self, annotation_list: Dict):
        """insert an AnnotationList"""
        raise NotImplementedError("AdapterCore.insert_annotation_list")

    # TODO delete ?
    def get_manifest(self):
        """read a single manifest"""
        raise NotImplementedError("AdapterCore.get_manifest")

    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        r = requests.get(f"{self.endpoint}/manifests/2")
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

