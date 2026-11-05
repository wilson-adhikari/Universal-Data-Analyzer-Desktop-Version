# Rebuild Plan — Universal Data Analyzer Desktop

Principle (PCD §4.5): keep the existing modular structure, which is sound. Fix defects, then connect the modules that are already written but unreachable, and only after that add new features. No rewrite.

## M0 — Make it runnable and testable (prerequisite)

- Split `requirements.txt` into runtime (pandas, numpy, matplotlib, seaborn, scipy, sqlalchemy, openpyxl, PySide6) and `requirements-dev.txt` (pytest). Pin `pandas<4`.
- Add `.pyc` / `__pycache__` to `.gitignore` and remove the committed ones.
- Rename `Universal Data Analyzer exe/` to `uda_desktop/` (or add `pyproject.toml` with a console entry point) so imports don't depend on the working directory.
- Add a pytest suite with small CSV fixtures, covering the controller, cleaning and plot factory headlessly (`MPLBACKEND=Agg`).

## M1 — Fix defects D1–D7

| ID | Fix |
|---|---|
| D1 | **Done.** Owner chose option A (apply in order). Fixed order: forward_fill → backward_fill → mean → median → constant → drop; the UI lists them in that order. Tests: `tests/test_missing_values.py`. |
| D2 | **Done.** Uses `ffill()` / `bfill()`. |
| D3 | Add `PlotExporter.export_plot_to_svg`. |
| D4 | Raise `DataLoadingException` with the driver's message. |
| D5 | Show validator issues as a warning before plotting. |
| D6 | Read the header (`nrows=0`) on file load and populate the X/Y selectors right away. |
| D7 | Add a constant-value input; apply it only to columns whose type matches. |

Each fix gets a regression test. Exit criterion: all tests pass on pandas 2.2 and 3.x.

## M2 — Expose existing modules (no new algorithms)

Duplicate report and removal, outlier report (merge `outliers.py` and `thresholds.py`), type report, correlation heatmap, text insights, HTML report export, cleaned-data export (CSV/Excel), Excel sheet picker, CSV separator detection.

## M3 — PCD §3.1 product improvements (after M1/M2 ship)

Data-quality profile tab, reusable cleaning configs (JSON), chart recommendation via `chart_selector.py`, project/workspace save and load, PyInstaller build in CI. Local ML (scikit-learn) and premium gating come last, and only once the licensing service exists (PCD §7).

## Breaking changes

- The folder rename in M0 changes the launch command. Document it in the README.
- D1 option A changes cleaning output for users who ticked several strategies. That's intended, but it goes in the changelog.

## Open questions for the owner

1. ~~D1~~: resolved, apply in order.
2. Confirm the copyright holder in `LICENSE` before any commercial distribution.
