# Repository Audit — Universal Data Analyzer Desktop

- **Repository:** https://github.com/wilson-adhikari/Universal-Data-Analyzer-Desktop-Version
- **Commit audited:** `2ab5f92` (7 commits total, all uploads via GitHub web UI)
- **Audit date:** 2026-11-05
- **Method:** static reading of every source file. The app was **not executed**: pandas, PySide6 and the other dependencies are not installed on the audit machine. Every behaviour claim below is from code reading, not from a run.

## Structure

```
README.md, LICENSE (MIT), .gitignore
Universal Data Analyzer exe/        <- all code lives in a folder with spaces in its name
  main.py                           entry point -> ui.main_window.main()
  core/controller.py                orchestrator (load -> clean -> stats -> plots)
  ui/                               PySide6 window, QThread worker, multi-select combo
  ingestion/                        CSV, Excel, SQL loaders, schema detector
  cleaning/                         missing values, duplicates, outliers, type casting
  eda/                              summary stats, correlations, distributions, groups
  insights/                         text insights, threshold calculator
  visualization/                    plot factory, chart selector
  reporting/                        plot export, data export, HTML report builder
  utils/                            exceptions, helpers, validators
  requirements.txt
```

~2,400 lines of Python. 35 `__pycache__/*.pyc` files are committed, including a stale `worler.cpython-313.pyc` (typo of `worker`).

## Runtime flow (what the user can actually reach)

1. Pick file type (csv / excel / sql) → choose a file, or type a connection string and table name.
2. Tick one or more missing-value strategies and chart types → Run Analysis.
3. `Worker` (QThread) calls `Controller.run`: load → `schema_detector.detect_schema` (result discarded) → `validator.validate_dataframe` (result discarded) → **first** strategy only → `SummaryStats.get_summary` → one matplotlib figure per chart type.
4. Tabs show the summary text, the cleaned DataFrame, and one tab per chart.
5. Export Current Plot → PNG / JPEG / PDF / SVG.

X/Y column selectors are only filled **after** the first run, so the first run always plots column 0 against the next column.

## Dependencies

`requirements.txt` lists 19 packages. Only these are imported by reachable code: pandas, numpy, matplotlib, seaborn, scipy, sqlalchemy, openpyxl (via pandas), PySide6.

Listed but unused in the desktop app: `streamlit`, `scikit-learn`, `pydantic`, `jinja2`, `reportlab`, `weasyprint`, `python-dotenv`. Dev tools (`pytest`, `pytest-cov`, `black`, `flake8`) are mixed into runtime requirements. `weasyprint` needs native GTK libraries on Windows and commonly fails to install, which blocks `pip install -r requirements.txt` for no benefit.

Version pins are floors only (`pandas>=2.2`). A fresh install today pulls pandas 3.x, which breaks forward/backward fill (see TECHNICAL_DEBT D2).

## Build, packaging, CI

- No `pyproject.toml`, no installer, no PyInstaller spec, despite the folder being named "exe".
- No CI configuration.
- No tests of any kind.

## Security

- SQL connection strings (with passwords) are typed into a plain `QLineEdit`; not persisted. Acceptable for a local tool; not masked on screen.
- `pd.read_sql_table` with a user-typed table name: no injection vector beyond what the user's own credentials allow.
- No network calls, telemetry, or secrets in the repo.

## Licensing / IP (PCD §4.6)

- MIT licence, copyright holder to be confirmed against the company entity before commercial sale. MIT allows commercial use, but the company cannot relicense contributions it doesn't own. Git history shows a single author.
- README contains `[web:262]`-style citation artefacts from an AI chat tool. These should be removed before public release.
- Dependencies: PySide6 is LGPLv3. That is fine for a dynamically linked desktop app but needs a notice and replaceable-library compliance when frozen into an exe.

## Documentation accuracy

- README install step `cd Universal Data Analyzer exe` fails because the path has spaces and isn't quoted.
- README says SVG export works "if enabled in your matplotlib backend". In fact it fails every time (D3).
- README correctly discloses the first-strategy-only behaviour.
