"""OV self-evolving session-end pipeline smoke tests."""
import sys
import os
import json
import time
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage.self_evolve import (
    recent_sessions, count_ungrouped, scan_entity_links,
    trigger_l1_build_if_due, evolve_at_session_end, log_evolve_event,
    DEFAULT_L1_TRIGGER_THRESHOLD, EVOLVE_LOG,
)


def _make_session(memory_dir: Path, name: str, body: str = "body",
                  thread_id: str = "", description: str = "test") -> Path:
    p = memory_dir / name
    front = ["---", f"name: {name}", f"description: {description}"]
    if thread_id:
        front.append(f"thread_id: {thread_id}")
    front.extend(["---", body])
    p.write_text("\n".join(front) + "\n", encoding="utf-8")
    return p


def test_1_recent_sessions_within_lookback():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        _make_session(m, "session_a.md")
        _make_session(m, "session_b.md")
        recent = recent_sessions(m, within_hours=24)
        assert len(recent) == 2
    print("OK 1 recent_sessions within lookback")


def test_2_recent_sessions_empty_dir():
    with tempfile.TemporaryDirectory() as t:
        assert recent_sessions(Path(t)) == []
    print("OK 2 empty memory dir")


def test_3_count_ungrouped_no_l1():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        for i in range(5):
            _make_session(m, f"session_{i}.md")
        assert count_ungrouped(m) == 5
    print("OK 3 ungrouped count no L1")


def test_4_count_ungrouped_with_l1_index():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        for i in range(5):
            _make_session(m, f"session_{i}.md")
        l1 = m / "_l1"
        l1.mkdir()
        (l1 / "_l1_index.json").write_text(
            json.dumps({"session_0.md": "t-a.md", "session_1.md": "t-a.md"}),
            encoding="utf-8",
        )
        assert count_ungrouped(m) == 3
    print("OK 4 ungrouped count with L1 coverage")


def test_5_scan_entity_links_aggregation():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        _make_session(m, "session_a.md",
                       body="cites [[people/alice]] and [[sessions/session_b]]")
        _make_session(m, "session_b.md",
                       body="cites [[companies/acme]]")
        sessions = recent_sessions(m)
        stats = scan_entity_links(sessions)
        assert stats["sessions_scanned"] == 2
        assert stats["sessions_with_refs"] == 2
        assert stats["refs_total"] == 3
        assert stats["by_namespace"]["people"] == 1
        assert stats["by_namespace"]["companies"] == 1
        assert stats["by_namespace"]["sessions"] == 1
    print("OK 5 scan_entity_links aggregation")


def test_6_trigger_l1_below_threshold():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        # Only 2 sessions · below default threshold 3
        for i in range(2):
            _make_session(m, f"session_{i}.md", thread_id="t-A")
        r = trigger_l1_build_if_due(m, threshold=3)
        assert not r["triggered"]
        assert r["ungrouped"] == 2
    print("OK 6 below threshold no trigger")


def test_7_trigger_l1_at_threshold_thread_group():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        for i in range(3):
            _make_session(m, f"session_{i}.md", thread_id="t-X")
        r = trigger_l1_build_if_due(m, threshold=3)
        assert r["triggered"]
        # t-X group of 3 should form
        assert r["groups"] >= 1
        # L1 file written
        assert (m / "_l1" / "t-X.md").exists()
    print("OK 7 threshold met · L1 built")


def test_8_evolve_full_flow():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        for i in range(4):
            _make_session(m, f"session_{i}.md",
                           thread_id="t-evolve",
                           body=f"session {i} cites [[people/agent_{i}]]")
        cache = Path(t) / "_cache"
        event = evolve_at_session_end(m, cache_dir=cache)
        assert event["ok"]
        assert event["recent_sessions"] == 4
        assert event["entity_scan"]["refs_total"] == 4
        assert event["l1_build"]["triggered"]
        # Log written
        log = cache / EVOLVE_LOG
        assert log.exists()
    print("OK 8 evolve full flow")


def test_9_evolve_missing_memory_dir():
    with tempfile.TemporaryDirectory() as t:
        ghost = Path(t) / "nonexistent"
        cache = Path(t) / "_cache"
        event = evolve_at_session_end(ghost, cache_dir=cache)
        assert not event["ok"]
    print("OK 9 missing memory_dir graceful")


def test_10_idempotent_double_invoke():
    with tempfile.TemporaryDirectory() as t:
        m = Path(t)
        for i in range(3):
            _make_session(m, f"session_{i}.md", thread_id="t-id")
        cache = Path(t) / "_cache"
        e1 = evolve_at_session_end(m, cache_dir=cache)
        e2 = evolve_at_session_end(m, cache_dir=cache)
        assert e1["ok"] and e2["ok"]
        # Both should report L1 built · second call sees already-grouped · ungrouped=0
        assert e2["l1_build"].get("triggered") is False
    print("OK 10 idempotent double-invoke")


def test_11_log_evolve_event_appends():
    with tempfile.TemporaryDirectory() as t:
        cache = Path(t)
        log_evolve_event({"ok": True, "step": "a"}, cache_dir=cache)
        log_evolve_event({"ok": True, "step": "b"}, cache_dir=cache)
        lines = (cache / EVOLVE_LOG).read_text(encoding="utf-8").strip().splitlines()
        assert len(lines) == 2
    print("OK 11 log appends")


if __name__ == "__main__":
    tests = [test_1_recent_sessions_within_lookback, test_2_recent_sessions_empty_dir,
             test_3_count_ungrouped_no_l1, test_4_count_ungrouped_with_l1_index,
             test_5_scan_entity_links_aggregation, test_6_trigger_l1_below_threshold,
             test_7_trigger_l1_at_threshold_thread_group, test_8_evolve_full_flow,
             test_9_evolve_missing_memory_dir, test_10_idempotent_double_invoke,
             test_11_log_evolve_event_appends]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} self_evolve smoke pass")
