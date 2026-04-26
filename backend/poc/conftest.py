import sys
from pathlib import Path

_root = str(Path(__file__).resolve().parents[2])  # LA-Hacks/
if _root not in sys.path:
    sys.path.insert(0, _root)
