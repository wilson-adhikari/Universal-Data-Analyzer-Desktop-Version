"""Headless end-to-end smoke test: load CSV -> clean -> summary -> every chart -> export."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest  # noqa: E402

from core.controller import Controller  # noqa: E402
from reporting.export_plots import PlotExporter  # noqa: E402

CHART_TYPES = ["line", "bar", "scatter", "histogram", "box", "violin", "kde"]


@pytest.fixture(scope="module")
def csv_path(tmp_path_factory):
    p = tmp_path_factory.mktemp("data") / "sample.csv"
    p.write_text("g,x,y\na,1,2.5\nb,2,\na,3,4.1\nb,,5.0\nc,5,6.2\nc,6,7.0\n")
    return str(p)


def test_main_window_builds():
    from PySide6.QtWidgets import QApplication
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])  # noqa: F841
    assert MainWindow() is not None


@pytest.mark.parametrize("chart_type", CHART_TYPES)
def test_pipeline_and_export(csv_path, chart_type, tmp_path):
    results = Controller().run(csv_path, [chart_type], ["mean"], "x", "y", "csv")

    assert len(results) == 1
    ct, df_clean, summary, (fig, _ax) = results[0]
    assert ct == chart_type
    assert df_clean[["x", "y"]].isna().sum().sum() == 0  # mean strategy cleaned the numeric columns
    assert {"x", "y"} <= set(summary.index)

    for ext, export in [
        ("png", PlotExporter.export_plot_to_png),
        ("jpg", PlotExporter.export_plot_to_jpeg),
        ("pdf", PlotExporter.export_plot_to_pdf),
    ]:
        out = tmp_path / f"{chart_type}.{ext}"
        export(fig, str(out))
        assert out.stat().st_size > 0


@pytest.mark.xfail(reason="D3: export_plot_to_svg missing", raises=AttributeError, strict=True)
def test_svg_export(csv_path, tmp_path):
    fig = Controller().run(csv_path, ["line"], ["mean"], "x", "y", "csv")[0][3][0]
    PlotExporter.export_plot_to_svg(fig, str(tmp_path / "line.svg"))
