import re
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib import rc

from src.utils import PATH_OUT, json_read


report_file_regex = re.compile(r"report_benchmark_[A-Za-z]+_([\d\-\:]+)_\d+steps.json")
def get_latest_report_file() -> Path:
    """get the most recent report file and return its Path"""
    report_files = []
    for f in PATH_OUT.iterdir():
        match = report_file_regex.match(f.name)
        if f.is_file() and match:
            report_files.append((f, match[1]))

    if not len(report_files):
        raise FileNotFoundError("get_latest_report_file: found no file matching report pattern. are you sure you have ran a report and saved its results ?")

    # sort by datetime asc and select the most recent file
    report_files = sorted(
        report_files,
        key=lambda tup: datetime.strptime(tup[1], r"%Y-%m-%d-%H:%M:%S")
    )
    return report_files[-1][0]

def maybe_drop_step_1(report: dict):
    if len(report["results"]) > 2:
        report["results"] = report["results"][1:]
        return report
    return report

def get_x(report: dict, fancy: bool) -> list:
    to_string = lambda n: f"{n:,}"
    return [
        to_string(step["step"]["n_annotation"])
        if fancy else step["step"]["n_annotation"]
        for step in report["results"]
    ]


def get_y(report: dict, key: str) -> list[float]:
    return [
        step[key] for step in report["results"]
    ]


def init_fig(report: dict):
    font_size_title = 34
    font_size_axis = 30
    font_size_text = 24
    # NOTE: rcParams must be updated before creating fig
    plt.rcParams.update({
        "text.usetex": True,
        "font.family": "serif",
        "font.size": font_size_text,
        "legend.edgecolor": "black",
        "legend.loc": "upper right",
        "legend.fancybox": False,
        "legend.shadow": False,
        "legend.framealpha": 0,
        "legend.edgecolor": "black",
    })
    plt.ioff()

    fig = plt.figure()
    ax = plt.subplot()
    fig.set_figheight(10)
    fig.set_figwidth(20)
    ax.yaxis.set_label_coords(-0.06,0.5)
    ax.xaxis.set_label_coords(0.5,-0.06)

    # fig.suptitle("Benchmark results", size=font_size_title, position=(0.5,0.95))
    plt.xlabel(r"\textnumero{} of annotations in database", size=font_size_axis)
    plt.ylabel(f"Avg. execution time / operation (in {report['time_unit']})", size=font_size_axis)
    return fig, ax


def make_plot(report: dict, basename: str, annotations_only: bool, to_file: bool) -> None:
    report = maybe_drop_step_1(report)
    x = get_x(report, True)
    y_data = [
        ( "timing_read_annotation_list", "Read anno. list", ),
        ( "timing_read_annotation", "Read anno." ),
        ( "timing_write_annotation_list", "Write anno. list" ),
        ( "timing_write_annotation", "Write anno." ),
        ( "timing_update_annotation", "Update anno." ),
        ( "timing_delete_annotation", "Delete anno." )
    ]
    if not annotations_only:
        y_data.append(( "timing_write_manifest", "Write manifest" ))
    y_data = [
        ( get_y(report, el[0]), el[1] )
        for el in y_data
    ]

    fig, ax = init_fig(report)
    for el in y_data:
        ax.plot(x, el[0], "-o", label=el[1])

    # style bbox. necessary to be here
    ax.legend(bbox_to_anchor=(1.23,1))

    if to_file:
        plt.savefig(PATH_OUT / f"{basename}.png", transparent=False, bbox_inches="tight")
    else:
        plt.show()
    return


def make_visualization(report_file: str|Path, annotations_only: bool, nowrite: bool):
    try:
        if report_file == "latest":
            report_file = get_latest_report_file()
        else:
            report_file = Path(report_file)
        report = json_read(Path(report_file))
    except FileNotFoundError:
        print("report file not found and could not be visualized. if you used `latest`, make sure you have ran a benchmark before. otherwise, make sure you specified the correct path to the benchmark report file.")
        exit(1)

    make_plot(report, report_file.name.replace(".json", ""), annotations_only=annotations_only, to_file=not nowrite)
