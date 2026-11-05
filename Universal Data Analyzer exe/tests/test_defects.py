"""Regression tests for audit defects D3-D7 (docs/audit/TECHNICAL_DEBT.md)."""
import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pandas as pd  # noqa: E402
import pytest  # noqa: E402

from cleaning.missing_values import MissingValueHandler  # noqa: E402
from core.controller import Controller  # noqa: E402
from reporting.export_plots import PlotExporter  # noqa: E402
from utils.exceptions import DataLoadingException  # noqa: E402


@pytest.fixture
def csv_path(tmp_path):
    p = tmp_path / "sample.csv"
    p.write_text("g,x,y,empty\na,1,2.5,\nb,2,,\na,3,4.1,\nc,5,6.2,\n")
    return str(p)


def test_d3_svg_export_writes_svg(csv_path, tmp_path):
    fig = Controller().run(csv_path, ["line"], ["mean"], "x", "y", "csv")[0][3][0]
    out = tmp_path / "line.svg"
    PlotExporter.export_plot_to_svg(fig, str(out))
    assert out.read_text(encoding="utf-8").lstrip().startswith(("<?xml", "<svg"))


def test_d4_sql_error_is_reported_not_swallowed(tmp_path):
    db = tmp_path / "data.db"
    pd.DataFrame({"a": [1]}).to_sql("real_table", f"sqlite:///{db}", index=False)
    with pytest.raises(DataLoadingException, match="missing_table"):
        Controller().run("", ["line"], ["drop"], "a", None, "sql", f"sqlite:///{db}", "missing_table")


def test_d4_sql_happy_path_still_loads(tmp_path):
    db = tmp_path / "data.db"
    pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]}).to_sql("t", f"sqlite:///{db}", index=False)
    results = Controller().run("", ["scatter"], ["drop"], "a", "b", "sql", f"sqlite:///{db}", "t")
    assert len(results[0][1]) == 3


def test_d5_validation_issues_are_kept_for_the_ui(csv_path):
    c = Controller()
    c.run(csv_path, ["line"], ["mean"], "x", "y", "csv")
    assert any("empty" in issue and "only NaN" in issue for issue in c.last_issues)


def test_d7_constant_fill_keeps_text_columns_text():
    df = pd.DataFrame({"num": [1.0, None], "txt": ["a", None]})
    out = MissingValueHandler().handle(df, "constant")
    assert out["num"].tolist() == [1.0, 0.0]
    assert out["txt"].tolist() == ["a", "Unknown"]


def test_d6_column_pickers_fill_on_file_load(csv_path, monkeypatch):
    from PySide6.QtWidgets import QApplication, QFileDialog
    from ui.main_window import MainWindow

    app = QApplication.instance() or QApplication([])  # noqa: F841
    monkeypatch.setattr(QFileDialog, "getOpenFileName", lambda *a, **k: (csv_path, ""))
    w = MainWindow()
    w.select_file()
    xs = [w.x_col_selector.itemText(i) for i in range(w.x_col_selector.count())]
    assert xs == ["g", "x", "y", "empty"]
    w.x_col_selector.setCurrentText("y")
    w._set_columns(["g", "x", "y", "empty"])  # a later refresh keeps the user's choice
    assert w.x_col_selector.currentText() == "y"
