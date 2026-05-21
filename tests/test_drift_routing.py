"""S5 · drift/routing.py smoke tests."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from drift.routing import (
    infer_route, route_target_dir, is_recall_eligible,
    route_entry, log_routing_decision, filter_eligible,
    ROUTE_GREEN, ROUTE_YELLOW, ROUTE_RED,
    DEFAULT_QUARANTINE_DIR, DEFAULT_WARNING_DIR, DEFAULT_ROUTING_LOG,
)


def test_1_infer_route_explicit_label():
    assert infer_route(drift="green") == ROUTE_GREEN
    assert infer_route(drift="yellow") == ROUTE_YELLOW
    assert infer_route(drift="red") == ROUTE_RED
    print("OK 1 infer from explicit label")


def test_2_infer_route_default_green():
    assert infer_route(drift="") == ROUTE_GREEN
    assert infer_route(drift="none") == ROUTE_GREEN
    print("OK 2 default green when no label")


def test_3_infer_from_score():
    assert infer_route(drift="", drift_score=-0.10) == ROUTE_RED  # < -0.04
    assert infer_route(drift="", drift_score=-0.02) == ROUTE_YELLOW
    assert infer_route(drift="", drift_score=0.5) == ROUTE_GREEN
    print("OK 3 score-based inference")


def test_4_target_dir_red_quarantine():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        assert route_target_dir(tmp, ROUTE_RED).name == DEFAULT_QUARANTINE_DIR
        assert route_target_dir(tmp, ROUTE_YELLOW).name == DEFAULT_WARNING_DIR
        assert route_target_dir(tmp, ROUTE_GREEN) == tmp
    print("OK 4 target dir mapping")


def test_5_recall_eligibility():
    assert is_recall_eligible(ROUTE_GREEN)
    assert is_recall_eligible(ROUTE_YELLOW, include_yellow=True)
    assert not is_recall_eligible(ROUTE_YELLOW, include_yellow=False)
    assert not is_recall_eligible(ROUTE_RED)
    assert is_recall_eligible(ROUTE_RED, include_red=True)
    print("OK 5 recall eligibility")


def test_6_route_entry_dry_run():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        f = tmp / "s_red.md"
        f.write_text("---\ndrift: red\n---\nbody\n", encoding="utf-8")
        d = route_entry(f, drift="red", memory_root=tmp, apply_move=False)
        assert d["route"] == ROUTE_RED
        assert not d["moved"]
        # File not moved
        assert f.exists()
        assert not (tmp / DEFAULT_QUARANTINE_DIR / "s_red.md").exists()
    print("OK 6 route_entry dry-run no move")


def test_7_route_entry_apply_move():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        f = tmp / "s_yellow.md"
        f.write_text("---\ndrift: yellow\n---\n", encoding="utf-8")
        d = route_entry(f, drift="yellow", memory_root=tmp, apply_move=True)
        assert d["moved"]
        assert not f.exists()
        assert (tmp / DEFAULT_WARNING_DIR / "s_yellow.md").exists()
    print("OK 7 route_entry apply_move physical")


def test_8_log_routing_decision():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        d = {"route": "yellow", "original_path": "s.md", "drift": "yellow"}
        log_path = log_routing_decision(d, tmp)
        assert log_path.name == DEFAULT_ROUTING_LOG
        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert entry["route"] == "yellow"
        assert "ts" in entry
    print("OK 8 log routing decision")


def test_9_filter_eligible_excludes_red():
    entries = [
        {"path": "g.md", "drift": "green"},
        {"path": "y.md", "drift": "yellow"},
        {"path": "r.md", "drift": "red"},
    ]
    out = filter_eligible(entries)
    paths = [e["path"] for e in out]
    assert "g.md" in paths
    assert "y.md" in paths
    assert "r.md" not in paths
    print("OK 9 filter excludes red")


def test_10_filter_with_include_red():
    entries = [{"path": "r.md", "drift": "red"}]
    out = filter_eligible(entries, include_red=True)
    assert len(out) == 1
    print("OK 10 filter include_red opt-in")


def test_11_filter_explicit_route_field():
    entries = [
        {"path": "x.md", "route": "red"},  # explicit · no need to infer
        {"path": "y.md", "route": "green"},
    ]
    out = filter_eligible(entries)
    paths = [e["path"] for e in out]
    assert "y.md" in paths
    assert "x.md" not in paths
    print("OK 11 filter uses explicit route field")


if __name__ == "__main__":
    tests = [test_1_infer_route_explicit_label, test_2_infer_route_default_green,
             test_3_infer_from_score, test_4_target_dir_red_quarantine,
             test_5_recall_eligibility, test_6_route_entry_dry_run,
             test_7_route_entry_apply_move, test_8_log_routing_decision,
             test_9_filter_eligible_excludes_red, test_10_filter_with_include_red,
             test_11_filter_explicit_route_field]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} drift.routing smoke pass")
