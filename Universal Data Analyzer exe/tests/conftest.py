import os
import sys

# Tests import the app's top-level packages (core, cleaning, ...); make them importable from any CWD.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
