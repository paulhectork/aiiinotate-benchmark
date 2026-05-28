from pathlib import Path
from uuid import uuid4
from typing import BinaryIO, Callable, Literal

from tqdm import tqdm

from src.utils import run_bash, json_dumps
from src.constants import DB_NAME, MONGODB_HOST, MONGODB_PORT
from src.generate import generate_manifest_indexes, generate_annotation_lists


def run_mongosh_command(command: str):
    bash_command = f"mongosh {DB_NAME} --eval '{command}'"
    run_bash(bash_command)
    return


def mongoshimport(collection: str, fp_data: str | Path):
    command = f"""
        mongoimport --host {MONGODB_HOST} \
            --port {MONGODB_PORT} \
            --db {DB_NAME} \
            --collection {collection} \
            --file {fp_data} \
            --jsonArray \
    """
    run_bash(command)

FREQ_WRITE = 1000
FREQ_IMPORT = 10_000

def make_new_file() -> tuple[Path, BinaryIO]:
    fp = Path(f"/tmp/mongoimport-{uuid4()}.json")
    fh = open(fp, mode="ab")
    return fp, fh

def to_file(fh: BinaryIO, buffer: list, first_write: bool, close: bool) -> None:
    """
    append the contents of the array `buffer` to a JSON file.
    requires to manually-jsonify buffer and ensure consistency in multiple writes
    """
    # open JSON array if the file `fh` is still empty
    if first_write:
        fh.write(b"[")
    # append to `fh` the contents of the `buffer` array
    if buffer:
        # add separator from elements saved in previous calls to to_file
        if not first_write:
            fh.write(b",")
        fh.write(b",".join([json_dumps(d) for d in buffer]))
    # we are done with this file. close it.
    if close:
        fh.write(b"]")  # close JSON array
        fh.close()
    return None


def flush_and_import(
    collection: Literal["manifests2","annotations2"],
    fh: BinaryIO,
    fp: Path,
    buffer: list,
    first_write: bool
) -> None:
    """
    write any remaining buffer, close the array, import, and delete the file
    """
    close = True
    to_file(fh, buffer, first_write, close)
    try:
        mongoshimport(collection, fp)
    finally:
        fp.unlink()


def mongoshimport_main(
    generator: Callable,
    dtype=Literal["annotation","manifest"]
):
    """
    optimized database insertion using `mongoimport`.
    given `generator`, a callable that creates JSON objects (manifest indexes or annotations),
    - generate N objects.
    - each `FREQ_WRITE`, write those objects as JSON to a temp file
    - each `FREQ_IMPORT`,
        - read all written objects from the temp file
        - import them using mongoimport
        - delete the old temp file and recreate a new one.
    - at the end, write the remaining JSON objects to the mongo db.
    """

    if dtype not in ["annotation", "manifest"]:
        raise ValueError(f"mongoshimport_main: invalid value for dtype: {dtype}")
    if dtype == "annotation":
        collection = "annotations2"
    else:
        collection = "manifests2"

    def inner(**kwargs):
        list_id_canvas = kwargs.get("list_id_canvas", [])
        n_annotation_per_canvas = kwargs.get("n_annotation", None)
        n_manifest = kwargs.get("n_manifest", None)
        if len(list_id_canvas) == 0 and n_manifest is None:
            raise ValueError("mongoshimport_main must have 'list_id_canvas' or 'n_manifest' in its kwargs.")
        if len(list_id_canvas) < 1000 and (n_manifest is None or n_manifest < 1000):
            raise ValueError(f"mongoshimport_manifests must be used with `n_manifest` >= 1000 or `len(list_id_canvas)` >= 1000.")

        if dtype == "manifest":
            total = n_manifest
        else:
            total = len(list_id_canvas)

        list_out = []

        fp, fh = make_new_file()
        list_buffer = []
        first_write = True  # tracks whether anything has been written to the current file

        for i, data in tqdm(
            enumerate(generator(**kwargs)),
            desc=f"importing {dtype if dtype=='manifest' else 'annotation list'}s via mongoimport",
            total=total
        ):
            i += 1
            if dtype == "annotation":
                data = data["resources"]
                list_buffer += data

            else:
                list_buffer.append(data)

            if i % FREQ_IMPORT == 0:
                print(f"importing {FREQ_IMPORT} entries at it. #{i}")
                # write to file, import, empty buffer, create new file
                flush_and_import(collection, fh, fp, list_buffer, first_write)
                # reinitialise before next write/import cycle
                list_buffer = []
                fp, fh = make_new_file()
                first_write = True  # reset for the new file

            elif i % FREQ_WRITE == 0:
                # write to file, empty buffer, but DON'T use new file
                to_file(fh, list_buffer, first_write=first_write, close=False)
                list_buffer = []  # empty buffer
                first_write = False

            if dtype == "manifest":
                list_out += data["canvasIds"]

        # final import for any remaining data
        # if..else to avoid import if there's nothing to import
        # (causes JSON-formatting errors)
        if not first_write or list_buffer:
            flush_and_import(collection, fh, fp, list_buffer, first_write)
        else:
            fh.close()
            fp.unlink()

        return list_out

    return inner

from src.generate import generate_annotation_lists, generate_manifests
def mongoshimport_annotations(**kwargs):
    return mongoshimport_main(generate_annotation_lists, "annotation")(**kwargs)

def mongoshimport_manifests(**kwargs):
    return mongoshimport_main(generate_manifest_indexes, "manifest")(**kwargs)



# def mongoshimport_manifests(n_manifest: int, n_canvas: int):
#     if n_manifest < 1000:
#         raise ValueError(f"mongoshimport_manifests must be used with n_manifest >= 1000, got n_manifest={n_manifest}")
#
#     fp = Path(f"/tmp/annotation-{uuid4()}.json")
#     FREQ_WRITE = 1000
#     FREQ_IMPORT = 100_000
#     list_id_canvas = []
#
#     fh = open(fp, mode="ab")
#     fh.write(b"[")
#     list_buffer = []
#     for i, data in enumerate(generate_manifest_indexes(n_manifest, n_canvas)):
#         i += 1
#         list_buffer.append(data)
#
#         if i % FREQ_WRITE == 0:
#             print(f"writing {len(list_buffer)} entries, it #{i}")
#             # if previous items have been written, append a "," separator
#             if i > 1000:
#                 fh.write(b",")
#             fh.write(b",".join([json_dumps(d) for d in list_buffer]))
#             list_buffer = []
#
#         list_id_canvas += data["canvasIds"]
#     # finally, close the array and then the file
#     fh.write(b"]")
#     fh.close()
#     try:
#         mongoshimport("manifests2", fp)
#     finally:
#         fp.unlink()
#     return list_id_canvas
