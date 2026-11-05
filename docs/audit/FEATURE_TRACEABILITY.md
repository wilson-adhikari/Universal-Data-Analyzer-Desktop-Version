# Feature Traceability — Universal Data Analyzer Desktop

Status key (PCD §4.4): Fully implemented / Partially implemented / Not implemented / Broken / Experimental / Unverified.

Nothing has been run (see REPOSITORY_AUDIT). "Fully implemented" means the code path is complete and reachable from the UI, **not** that it was tested. Every row is therefore also *Unverified at runtime* until the test suite in REBUILD_PLAN M1 exists.

| Declared feature (README / PCD) | Code location | Status | Evidence | Decision |
|---|---|---|---|---|
| CSV ingestion | `ingestion/csv_loader.py` | Fully implemented | `pd.read_csv`, utf-8 only; `detect_separator` exists but is never called | Preserve; wire separator detection |
| Excel ingestion | `ingestion/excel_loader.py` | Partially implemented | First sheet only; `list_sheets` / `load_all_sheets` unused | Preserve; add sheet picker |
| SQL table ingestion | `ingestion/sql_loader.py` | Broken (error path) | Exceptions are printed and an empty DataFrame returned, so the user sees "Loaded dataset is empty" instead of the real error | Fix: raise `DataLoadingException` |
| Data preview | `ui/main_window.py` DataFrame View tab | Fully implemented | | Preserve |
| Missing-value: drop | `cleaning/missing_values.py` | Fully implemented | | Preserve |
| Missing-value: mean / median | same | Fully implemented | Numeric columns only; text NaNs left in place silently | Preserve; report untouched columns |
| Missing-value: forward / backward fill | same | Fully implemented (fixed 2026-11-05, tested on pandas 3.1.1) | Now uses `ffill()` / `bfill()` | Preserve |
| Missing-value: constant | same | Partially implemented | Always fills `0`, including text columns; no UI to set the value | Fix: user-supplied value |
| Multiple missing-value strategies | `MissingValueHandler.handle_many` | Fully implemented (fixed 2026-11-05, tested) | Selected strategies run in fixed order: forward_fill → backward_fill → mean → median → constant → drop | Owner chose "apply in order" |
| Data validation | `utils/validators.py` | Partially implemented | Called, but its `(ok, issues)` return is ignored, so issues never reach the user | Fix: surface issues |
| Schema detection | `ingestion/schema_detector.py` | Partially implemented | Called on every load; result discarded | Preserve; show in UI |
| Summary statistics | `eda/summary_stats.py` | Fully implemented | Numeric only; shown as raw `str(DataFrame)` | Preserve; render as table |
| Line / bar / scatter / histogram / box / violin / KDE charts | `visualization/plot_factory.py` | Fully implemented | All 7 branches present | Preserve |
| Export PNG / JPEG / PDF | `reporting/export_plots.py` | Fully implemented | | Preserve |
| Export SVG | `ui/main_window.py:303` | Broken | Calls `PlotExporter.export_plot_to_svg`, which does not exist, so "Export Failed" always appears | Fix: add the method |
| Duplicate detection | `cleaning/duplicates.py` | Not reachable | Instantiated in controller, never called | Wire into UI (M2) |
| Outlier detection | `cleaning/outliers.py`, `insights/thresholds.py` | Not reachable | Two overlapping implementations | Merge, then wire (M2) |
| Type casting / auto-detect | `cleaning/type_casting.py` | Not reachable | | Wire (M2) |
| Correlation analysis | `eda/correlations.py` | Not reachable | | Wire (M2) |
| Distribution / Q-Q / group analysis | `eda/distributions.py`, `eda/group_analysis.py` | Not reachable | | Wire selectively (M2) |
| Text insights | `insights/text_generator.py` | Not reachable | | Wire (M2) |
| Report generation (HTML) | `reporting/report_builder.py` | Not reachable | | Wire (M2) |
| Processed-data export | `reporting/export_data.py` | Not reachable | | Wire (M2) |
| Chart recommendation | `visualization/chart_selector.py` | Not reachable | | Wire (M3) |
| EDA (PCD list) | — | Partially implemented | Only summary stats + charts reachable | — |
| Advanced profiling, reusable cleaning configs, local ML, projects/workspaces, automated tests (PCD §3.1 improvements) | — | Not implemented | `scikit-learn` listed, never imported | New work, post-audit |

**Summary:** of 13 README-declared capabilities, 9 are now fully implemented, 2 partially and 2 broken (multi-strategy cleaning and ffill/bfill were fixed 2026-11-05). Ten more modules (about 40% of the code) are written but not reachable from the UI.
