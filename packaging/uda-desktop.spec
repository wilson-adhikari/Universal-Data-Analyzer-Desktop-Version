# PyInstaller spec for UDA Desktop (one-folder, windowed).
# Build from anywhere:
#   pyinstaller --noconfirm --workpath D:\uda-build\work --distpath D:\uda-build\dist packaging/uda-desktop.spec
# onedir (not onefile) keeps the Qt/PySide6 LGPL DLLs as separate, user-replaceable files.
import os

from PyInstaller.utils.hooks import copy_metadata

APP_DIR = os.path.join(SPECPATH, "..", "Universal Data Analyzer exe")

a = Analysis(
    [os.path.join(APP_DIR, "main.py")],
    pathex=[APP_DIR],
    # Their licence files ship with the app: BSD/MIT-style licences require the notice in binary copies.
    datas=[d for pkg in ("pandas", "numpy", "matplotlib", "seaborn", "scipy", "SQLAlchemy", "openpyxl") for d in copy_metadata(pkg)],
    hiddenimports=[
        "matplotlib.backends.backend_qtagg",  # imported statically today; pinned in case that changes
        "sqlalchemy.dialects.sqlite",  # dialects are loaded by name from the user's connection string
    ],
    excludes=["tkinter", "pytest"],
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="UDA-Desktop",
    console=False,
    upx=False,
)
coll = COLLECT(exe, a.binaries, a.datas, name="UDA-Desktop", upx=False)
