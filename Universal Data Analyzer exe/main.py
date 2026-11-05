import os
import sys

# Top-level packages (core, ui, ...) live next to this file; make them importable from any CWD.
# Frozen (PyInstaller) builds unpack them under sys._MEIPASS.
sys.path.insert(0, getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__))))

from ui.main_window import main  # noqa: E402

if __name__ == "__main__":
    main()
