from json import JSONDecodeError
from typing import Dict, List, Tuple, Optional
from urllib.parse import quote_plus
import subprocess

import requests

from .constants import PATH_ROOT
from .adapter_core import AdapterCore
from .utils import get_canvas_ids, get_manifest_short_id
from .multithread import mt_delete


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
        try:
            r_json = r.json()
            return 1 if "@id" in r_json.keys() else 0
        except JSONDecodeError:
            return 0

    #NOTE: for some obscure reason (multithreading?), SAS can take A LOT of time to send a response
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
        """read anno  tations into an annotationList ('search' route ?)"""
        r = requests.get(f"{self.endpoint}/annotation/search?uri={quote_plus(id_canvas)}")
        assert r.status_code == 200
        return r.json()

    # NOTE: this functionnality is not implemented by SAS
    def delete_manifest(self, id_manifest: str):
        """delete an annotation"""
        raise NotImplementedError("AdapterSas.delete_manifest")

    def delete_annotation(self, id_annotation: str):
        """delete an annotation"""
        r = requests.delete(f"{self.endpoint}/annotation/destroy?uri={quote_plus(id_annotation)}")
        if r.status_code == 204:
            return 1
        else:
            return 0

    def delete_annotations_for_canvas(self, id_canvas:str):
        annotation_list = self.get_annotation_list(id_canvas)
        list_id_annotation = [
            a["@id"] for a in annotation_list["resources"]
        ]
        r_all = []
        for id_annotation in list_id_annotation:
            r_all.append(self.delete_annotation(id_annotation))
        return 1 if len(set(r_all)) == 1 and r_all[0] == 1 else 0

    def delete_annotations_for_manifest(self, id_manifest:str):
        id_manifest = get_manifest_short_id(id_manifest)
        r = requests.get(f"{self.endpoint}/search-api/{quote_plus(id_manifest)}/search")
        annotation_list = r.json()
        r_all = []
        for annotation in annotation_list["resources"]:
            r_all.append(self.delete_annotation(annotation["@id"]))
        return 1 if len(set(r_all)) == 1 and r_all[0] == 1 else 0

    def update_annotation(self, id_annotation):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_annotation")

    def update_manifest(self, id_manifest):
        """update an annotation"""
        raise NotImplementedError("AdapterSas.update_manifest")

    def purge_hard(self):
        """
        delete all contents from database.

        NOTE: this is unused: after this, the SAS app should be restarted, which doesn't fit our use case (restart once every function has run)

        NOTE: after doing this, the SAS app becomes unusable.
        NOTE: this does not affect the indexation of manifests (written to memory and not to file ?)
        """
        path_sas_data = PATH_ROOT / "SimpleAnnotationServer" / "data"
        if not path_sas_data.exists():
            raise FileNotFoundError(f"AdapterSas.purge: data directory not found and cannot be purged, at '{path_sas_data}'")
        subprocess.run(f"rm -r \"{path_sas_data}\"", shell=True)
        return

    def purge(self, threads:int):  #pyright: ignore
        """
        delete all contents from the database using
        """
        #NOTE: with SAS, we can't delete manifests, so we just delete annotations.
        list_id_manifest = self.get_id_manifest_list()
        mt_delete(
            data=list_id_manifest,
            func=self.delete_annotations_for_manifest,
            threads=threads,
            pbar_desc=f"deleting all annotations from {len(list_id_manifest)} manifests (threads={threads})"
        )
        return



