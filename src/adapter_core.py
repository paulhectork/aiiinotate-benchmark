from typing import Dict, List, Tuple


class AdapterCore:
    def __init__(self, endpoint):
        self.endpoint = endpoint
        return

    def insert_manifest(self, manifest: Dict):
        """insert a single manifest"""
        raise NotImplementedError("AdapterCore.insert_manifest")

    def insert_annotation_list(self, annotation_list: Dict):
        """insert an AnnotationList"""
        raise NotImplementedError("AdapterCore.insert_annotation_list")

    # TODO delete ?
    def read_manifest(self):
        """read a single manifest"""
        raise NotImplementedError("AdapterCore.read_manifest")

    def read_annotation_list(self):
        """read annotations into an annotationList ('search' route ?)"""
        raise NotImplementedError("AdapterCore.read_annotation_list")

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

