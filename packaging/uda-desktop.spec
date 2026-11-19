# PyInstaller spec for UDA Desktop (one-folder, windowed).
# Build from anywhere:
#   pyinstaller --noconfirm --workpath D:\uda-build\work --distpath D:\uda-build\dist packaging/uda-desktop.spec
# onedir (not onefile) keeps the Qt/PySide6 LGPL DLLs as separate, user-replaceable files.
import os

APP_DIR = os.path.join(SPECPATH, "..", "Universal Data Analyzer exe")

a = Analysis(
    [os.path.join(APP_DIR, "main.py")],
    pathex=[APP_DIR],
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
