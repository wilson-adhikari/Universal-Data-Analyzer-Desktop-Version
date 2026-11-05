# Technical Debt — Universal Data Analyzer Desktop

Ordered by user impact. File paths are relative to `Universal Data Analyzer exe/`.

## Defects (user-visible)

| ID | Issue | Location | Impact |
|---|---|---|---|
| D1 | **FIXED 2026-11-05.** Only the first selected missing-value strategy was applied | `Controller.run` → now `MissingValueHandler.handle_many` | Was: wrong cleaning result vs what the UI shows |
| D2 | **FIXED 2026-11-05.** `fillna(method=...)` was removed in pandas 3.0 (confirmed: `TypeError` on pandas 3.1.1) | `MissingValueHandler.handle` | Was: forward/backward fill crashed on a fresh install |
| D3 | SVG export calls a method that doesn't exist | `ui/main_window.py:303` → `reporting/export_plots.py` | SVG export always fails |
| D4 | SQL loader swallows exceptions and returns an empty frame | `ingestion/sql_loader.py` `load_sql_table` except block | Bad credentials show up as "dataset is empty" |
| D5 | Validator result is discarded | `Controller.run` (`validate_dataframe` call) | All-NaN or duplicate-name columns go unreported |
| D6 | X/Y selectors are only populated after the first run | `ui/main_window.py:241-247` | The first run can't target the columns the user wants |
| D7 | "Constant" strategy hard-codes `0`, including for text columns | `MissingValueHandler.handle` (`constant` branch) | Puts `0` into text fields |

## Structural debt

- **Almost no tests.** Only `tests/test_missing_values.py` (5 tests, added with the D1/D2 fix). Everything else is unguarded. Run from `Universal Data Analyzer exe/` with `python -m pytest tests`.
- **Dead wiring:** 12 components are created in `Controller.__init__`, and 11 of them are never used.
- **Duplicate logic:** IQR/z-score outliers exist in both `cleaning/outliers.py` and `insights/thresholds.py`.
- **`requirements.txt` is bloated:** 7 unused runtime packages; `weasyprint` can break installs on Windows; dev tools are mixed in; no upper bounds.
- **Committed build artefacts:** 35 `.pyc` files, including a stale `worler` file.
- **Folder name with spaces** (`Universal Data Analyzer exe`) breaks the README commands and is awkward for packaging and CI.
- **Imports rely on the current working directory:** modules import `from ingestion...`, so the app only runs when launched from inside that folder.
- **Not packaged:** no `pyproject.toml`, no PyInstaller spec, no versioning.
- **Bare `except:`** in `cleaning/type_casting.py` auto-detect.
- **Summary is shown as `str(DataFrame)`** in a text widget rather than as a table.
