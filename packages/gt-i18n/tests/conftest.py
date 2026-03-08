"""Make the tests directory importable so helpers.py can be used."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
