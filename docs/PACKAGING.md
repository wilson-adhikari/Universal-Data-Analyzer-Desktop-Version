# Packaging — UDA Desktop (Windows, PyInstaller spike)

Status: spike (2026-11-06). Builds and launches; not a release. No installer, signing or versioning yet.

## Build

Python 3.11. Keep build output off a small system drive.

```powershell
py -3.11 -m venv D:\uda-build\venv
D:\uda-build\venv\Scripts\pip install -r requirements-runtime.txt pyinstaller==6.22.3 pytest==9.2.0
D:\uda-build\venv\Scripts\pyinstaller --noconfirm --workpath D:\uda-build\work --distpath D:\uda-build\dist packaging\uda-desktop.spec
```

Output: `D:\uda-build\dist\UDA-Desktop\UDA-Desktop.exe` (one-folder, windowed). The spec can be run from any directory.

Tests (any directory): `python -m pytest "Universal Data Analyzer exe/tests"` — set `QT_QPA_PLATFORM=offscreen` on headless machines.

## Verified versions

Python 3.11.0, pandas 3.1.1, numpy 2.4.6, matplotlib 3.11.2, seaborn 0.13.2, scipy 1.17.1,
SQLAlchemy 2.1.8, openpyxl 3.1.5, PySide6 6.12.0, PyInstaller 6.22.3 (hooks-contrib 2026.9), pytest 9.2.0.

## Result

- Bundle size: ~274 MB unpacked (PySide6 94 MB, of which `opengl32sw.dll` 20 MB; scipy 49 MB + 20 MB libs).
- Exe started from `D:\` with `QT_QPA_PLATFORM=offscreen` stays running past 8 s with no error dialog.
  This proves imports and main-window construction only; charting inside the frozen exe was not exercised.

## Hidden imports

PyInstaller found everything without help. The spec still pins two dynamic imports:
`matplotlib.backends.backend_qtagg` and `sqlalchemy.dialects.sqlite` (dialects load by name from the connection string).
Other DB drivers (psycopg2, MySQLdb, ...) are **not** bundled, so only SQLite connection strings work in the exe.
Build warnings for `scipy.special._cdflib`, `pysqlite2`, `MySQLdb`, `psycopg2` are expected.

## Known issues

- SVG export fails (D3 in `docs/audit/TECHNICAL_DEBT.md`); `tests/test_smoke.py` marks it xfail.
- `requirements.txt` is the old, bloated list (streamlit, weasyprint, dev tools). Use `requirements-runtime.txt`; delete the old file in a later change.
- `*.spec` is in `.gitignore`; `packaging/uda-desktop.spec` was force-added.
- Under the `offscreen` Qt platform, Qt warns that it ships no fonts; the normal Windows platform uses system fonts.
- Size could drop by excluding `opengl32sw.dll` and unused Qt plugins; not done (needs testing on GPU-less machines).

## Licensing (LGPL)

PySide6/Qt are LGPLv3. The one-folder build keeps the Qt DLLs as separate, replaceable files, which onefile would not.

TODO before any distribution:
- Ship the Qt and PySide6 LGPLv3 license texts and a notice naming them, with a link to their source code.
- Tell users they may replace the Qt/PySide6 libraries, and how.
- Add third-party notices for the other bundled packages (pandas, numpy, matplotlib, seaborn, scipy, SQLAlchemy, openpyxl, Pillow).
