"""Tests for Soul PR gate."""
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parent.parent
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from services.soul_pr_gate import check_paths, check_diff_loc, gate


def test_blacklist_rejects_env():
    ok, reason = check_paths([".env", "services/soul_service.py"])
    assert ok is False
    assert ".env" in reason


def test_blacklist_rejects_alembic():
    ok, reason = check_paths(["alembic/versions/abc.py"])
    assert ok is False
    assert "alembic" in reason


def test_clean_paths_pass():
    ok, _ = check_paths(["services/soul_service.py", "README.md"])
    assert ok is True


def test_diff_cap_rejects():
    ok, reason = check_diff_loc(600)
    assert ok is False
    assert "600" in reason


def test_diff_cap_allows():
    ok, _ = check_diff_loc(400)
    assert ok is True


def test_gate_combines_blacklist_first():
    ok, reason = gate(["alembic/versions/x.py"], 10)
    assert ok is False
    assert "alembic" in reason


def test_gate_passes_clean_small():
    ok, _ = gate(["services/foo.py"], 100)
    assert ok is True
