import matplotlib.pyplot as plt
import numpy as np

from src.utils import PATH_OUT, read_json

def get_x(report: dict) -> list:
    to_string = lambda t: f"n_man: {t[0]}, n_ann: {t[1]}"
    return [
        to_string((
            step["step"]["n_manifest"],
            step["step"]["n_annotation"]
        ))
        # step["step"]["n_annotation"]
        for step in report["results"]
    ]

def get_y(report: dict, key: str) -> list[float]:
    return [
        step[key] for step in report["results"]
    ]

def visualize(report: dict) -> None:
    x = get_x(report)
    y_data = [
        (
            "timing_read_annotation_list",
            "Read anno. list",
        ),
        (
            "timing_read_annotation",
            "Read anno."
        ),
        (
            "timing_write_manifest",
            "Write manifest"
        ),
        (
            "timing_write_annotation_list",
            "Write anno. list"
        ),
        (
            "timing_write_annotation",
            "Write anno."
        ),
        (
            "timing_update_annotation",
            "Update anno."
        ),
        (
            "timing_delete_annotation",
            "Delete anno."
        )
    ]
    y_data = [
        (
            get_y(report, el[0]),
            el[1]
        )
        for el in y_data
    ]

    fig, ax = plt.subplots()
    plt.style.use("_mpl-gallery")
    plt.ioff()

    plt.xlabel("database contents")
    plt.ylabel(f"average execution time in {report['time_unit']}")

    for el in y_data:
        ax.plot(x, el[0], label=el[1])
    ax.legend()

    plt.show()
