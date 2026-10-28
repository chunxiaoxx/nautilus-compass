"""Tests for nautilus_cli.demo · canned replay walkthrough."""
from __future__ import annotations
import sys
from pathlib import Path

# Make nautilus_cli importable when tests run from anywhere
CLI_ROOT = Path(__file__).resolve().parent.parent
if str(CLI_ROOT) not in sys.path:
    sys.path.insert(0, str(CLI_ROOT))


def test_demo_prints_both_cycles(capsys):
    from nautilus_cli.demo import run_demo
    code = run_demo()
    assert code == 0
    out = capsys.readouterr().out
    assert "CYCLE 5" in out
    assert "CYCLE 9" in out


def test_demo_includes_commit_hashes(capsys):
    from nautilus_cli.demo import run_demo
    run_demo()
    out = capsys.readouterr().out
    assert "572547e7d" in out
    assert "9248e84c5" in out


def test_demo_exits_zero():
    from nautilus_cli.demo import run_demo
    assert run_demo() == 0
