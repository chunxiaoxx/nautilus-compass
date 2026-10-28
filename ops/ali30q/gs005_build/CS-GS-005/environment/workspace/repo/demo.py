"""Convenience shim · run Nautilus Soul demo from fresh clone without pip install.

Usage from repo root:
    python demo.py

Equivalent to (after pip install -e phase3/cli/):
    nautilus demo
"""
import sys
from pathlib import Path

# Make phase3/cli importable so `nautilus_cli.demo` resolves
sys.path.insert(0, str(Path(__file__).resolve().parent / "phase3" / "cli"))

from nautilus_cli.demo import run_demo

if __name__ == "__main__":
    sys.exit(run_demo())
