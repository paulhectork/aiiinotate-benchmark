import re
from typing import Dict, List, Tuple

import requests


def validate_endpoint(endpoint: str) -> str:
    endpoint = re.sub("/$", "", endpoint)  # delete trailing "/"
    try:
        requests.get(endpoint)
    except requests.exceptions.ConnectionError:
        raise ValueError(f"validate_endpoint: failed to connect to endpoint: '{endpoint}'")
    return endpoint


class AdapterCore:

    def __init__(self, endpoint):
        """
        :param endpoint: full endpoint (including the service: 'http://' and port, if on localhost)
        """
        self.endpoint = validate_endpoint(endpoint)
        return

    @property
    def server_name(self):
        raise NotImplementedError("AdapterCore.server_name")

    def insert_manifest(self, manifest: Dict):
        """insert a single manifest"""
        raise NotImplementedError("AdapterCore.insert_manifest")

    def insert_annotation_list(self, annotation_list: Dict):
        """insert an AnnotationList"""
        raise NotImplementedError("AdapterCore.insert_annotation_list")

    def get_manifest(self):
        """read a single manifest"""
        raise NotImplementedError("AdapterCore.get_manifest")

    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        raise NotImplementedError("AdapterCore.get_manifest_collection")

    def get_id_manifest_list(self) -> List[str]:
        coll = self.get_manifest_collection()
        return [
            m["@id"] for m in coll["members"]
            if m["@type"] == "sc:Manifest"
        ]

    def get_annotation_list(self, id_canvas: str):
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



