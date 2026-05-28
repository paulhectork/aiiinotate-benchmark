from typing import Dict, List, Callable, Optional, BinaryIO
from urllib.parse import quote_plus
from uuid import uuid4
from pathlib import Path
import subprocess
import os

import requests
from dotenv import load_dotenv

from src.adapter_core import AdapterCore
from src.utils import pprint, get_manifest_short_id, get_canvas_ids, json_dumps, run_bash
from src.mongosh import run_mongosh_command




class AdapterAiiinotate(AdapterCore):
    def __init__(self, endpoint):
        super().__init__(endpoint)
        return

    @property
    def server_name(self):
        return "aiiinotate"

    def insert_manifest(self, manifest: Dict) -> List[Optional[str]]:
        """insert a single manifest"""
        r = requests.post(
            f"{self.endpoint}/manifests/2/create",
            json=manifest
        )
        r_data = r.json()
        # returns list of canvas ids if the manifest has been inserted, `[]` otherwise.
        return (
            get_canvas_ids(manifest)
            if "insertedCount" in r_data.keys()
            and r_data["insertedCount"] > 0
            else []
        )

    def insert_annotation(self, annotation:Dict):
        """insert a single annotation"""
        r = requests.post(
            f"{self.endpoint}/annotations/2/create",
            json=annotation
        )
        r_json = r.json()
        if "insertedIds" in r_json and len(r_json["insertedIds"]):
            return 1
        else:
            return 0

    def insert_annotation_list(self, annotation_list: Dict):
        """insert an AnnotationList"""
        r = requests.post(
            f"{self.endpoint}/annotations/2/createMany",
            json=annotation_list
        )
        r_json = r.json()
        if "insertedIds" in r_json and len(r_json["insertedIds"]):
            return 1
        else:
            return 0

    # TODO delete ?
    def get_manifest(self):
        """read a single manifest"""
        raise NotImplementedError("AdapterCore.get_manifest")

    def get_annotation(self, id_annotation:str):
        r = requests.get(id_annotation)
        assert r.status_code == 200
        return r.json()

    def get_manifest_collection(self) -> Dict:
        """return the collection of manifests"""
        r = requests.get(f"{self.endpoint}/manifests/2")
        return r.json()

    def get_annotation_list(self, id_canvas:str):
        """read annotations into an annotationList ('search' route ?)"""
        r = requests.get(f"{self.endpoint}/annotations/2/search?canvasUri={quote_plus(id_canvas)}")
        assert r.status_code == 200
        return r.json()

    def delete_manifest(self, id_manifest: str):
        """delete a manifest"""
        r = requests.delete(f"{self.endpoint}/manifests/2/delete?uri={quote_plus(id_manifest)}")
        return 1 if r.json()["deletedCount"] > 0 else 0

    def delete_annotation(self, id_annotation: str):
        """delete an annotation"""
        r = requests.delete(f"{self.endpoint}/annotations/2/delete?uri={id_annotation}")
        return 1 if r.json()["deletedCount"] > 0 else 0

    def delete_annotations_for_manifest(self, id_manifest: str):
        """
        :param id_manifest: the manifest's "@id"
        """
        id_manifest = get_manifest_short_id(id_manifest)
        r = requests.delete(f"{self.endpoint}/annotations/2/delete?manifestShortId={quote_plus(id_manifest)}")
        return 1 if r.json()["deletedCount"] > 0 else 0

    def update_annotation(self, annotation: Dict):
        r = requests.post(
            f"{self.endpoint}/annotations/2/update",
            json=annotation
        )
        return 1 if r.json()["modifiedCount"] > 1 else 0

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterCore.update_manifest")

    def purge(self):
        """
        delete all contents from database
        # NOTE: this works with a local mongosh database on linux, without users or passwords.
        # NOTE: this is totally not safe and should only be used in trusted environments and not in prod.
        """
        all_filter = "{}"
        collections = ["annotations2", "manifests2"]
        for collection in collections:
            run_mongosh_command(f"db.getCollection(\"{collection}\").deleteMany({all_filter});")
        return

