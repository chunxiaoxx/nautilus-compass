"""Local sys.path bootstrap so `from nautilus_cli.__main__ import main` works
when pytest is invoked from outside phase3/cli/ (e.g. repo root)."""
import sys
from pathlib import Path

_CLI_ROOT = Path(__file__).resolve().parent.parent
if str(_CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(_CLI_ROOT))
