"""Tests for v0.9.5 stake_publisher · publisher · A2A flow.

Run:
  PYTHONUTF8=1 python tests/test_stake_publisher.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

PLUGIN_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN_DIR))


def setup_test_env(tmp: Path) -> tuple[Path, Path, Path]:
    """Create test events_dir + processed/failed subdirs · return paths."""
    events_dir = tmp / "stake_events"
    processed_dir = events_dir / "processed"
    failed_dir = events_dir / "failed"
    events_dir.mkdir(parents=True)
    processed_dir.mkdir()
    failed_dir.mkdir()
    return events_dir, processed_dir, failed_dir


def make_event(events_dir: Path, name: str, drift: str, signals: list, retries: int = 0):
    ev = {
        "ts": "2026-05-05T10:00:00Z",
        "type": f"drift_{drift}",
        "agent_id": f"ag_test_{name}",
        "user_id": "u_test",
        "drift": drift,
        "drift_signals": signals,
        "_retries": retries,
    }
    p = events_dir / f"{name}.json"
    p.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
    return p


def test_consume_success():
    """Successful POST → file moves to processed/."""
    import stake_publisher
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        events_dir, processed_dir, failed_dir = setup_test_env(tmp)

        with patch.object(stake_publisher, "EVENTS_DIR", events_dir), \
             patch.object(stake_publisher, "PROCESSED_DIR", processed_dir), \
             patch.object(stake_publisher, "FAILED_DIR", failed_dir):

            with patch.object(stake_publisher, "post_a2a_event",
                              return_value=(True, '{"status":"ok"}')):
                p = make_event(events_dir, "evt_red", "red", ["test signal"])
                result = stake_publisher.consume_one(p)

        assert result == "ok", f"expected ok · got {result}"
        assert not p.exists(), "original should be moved"
        moved = list(processed_dir.glob("*.json"))
        assert len(moved) == 1, f"expected 1 in processed · got {len(moved)}"
        ev = json.loads(moved[0].read_text(encoding="utf-8"))
        assert "_processed_at" in ev
        print("  [PASS] consume_success · moved to processed/")


def test_consume_network_failure_kept():
    """Network failure → file kept · retries incremented."""
    import stake_publisher
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        events_dir, processed_dir, failed_dir = setup_test_env(tmp)

        with patch.object(stake_publisher, "EVENTS_DIR", events_dir), \
             patch.object(stake_publisher, "PROCESSED_DIR", processed_dir), \
             patch.object(stake_publisher, "FAILED_DIR", failed_dir):

            with patch.object(stake_publisher, "post_a2a_event",
                              return_value=(False, "url error: connection refused")):
                p = make_event(events_dir, "evt_net_fail", "red", ["network test"])
                result = stake_publisher.consume_one(p)

        assert result == "kept", f"expected kept · got {result}"
        assert p.exists(), "file should be kept"
        ev = json.loads(p.read_text(encoding="utf-8"))
        assert ev["_retries"] == 1
        assert "connection refused" in ev["_last_error"]
        print("  [PASS] consume_network_failure_kept · retries=1")


def test_consume_max_retries_failed():
    """After MAX_RETRIES failures → moved to failed/."""
    import stake_publisher
    stake_publisher.MAX_RETRIES = 3
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        events_dir, processed_dir, failed_dir = setup_test_env(tmp)

        with patch.object(stake_publisher, "EVENTS_DIR", events_dir), \
             patch.object(stake_publisher, "PROCESSED_DIR", processed_dir), \
             patch.object(stake_publisher, "FAILED_DIR", failed_dir):

            with patch.object(stake_publisher, "post_a2a_event",
                              return_value=(False, "always fails")):
                # Pre-set retries to MAX_RETRIES
                p = make_event(events_dir, "evt_fail", "red", ["test"], retries=3)
                result = stake_publisher.consume_one(p)

        assert result == "failed", f"expected failed · got {result}"
        assert not p.exists()
        moved = list(failed_dir.glob("*.json"))
        assert len(moved) == 1
        print("  [PASS] consume_max_retries_failed · moved to failed/")


def test_consume_bad_json():
    """Bad JSON file → moved to failed/."""
    import stake_publisher
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        events_dir, processed_dir, failed_dir = setup_test_env(tmp)

        bad = events_dir / "bad.json"
        bad.write_text("not valid json {{", encoding="utf-8")

        with patch.object(stake_publisher, "EVENTS_DIR", events_dir), \
             patch.object(stake_publisher, "PROCESSED_DIR", processed_dir), \
             patch.object(stake_publisher, "FAILED_DIR", failed_dir):

            result = stake_publisher.consume_one(bad)

        assert result == "failed"
        assert not bad.exists()
        moved = list(failed_dir.glob("*.json"))
        assert len(moved) == 1
        print("  [PASS] consume_bad_json · moved to failed/")


def test_envelope_format():
    """A2A envelope should match the protocol spec."""
    import stake_publisher

    captured = {}
    def fake_urlopen(req, *args, **kw):
        captured["url"] = req.full_url
        captured["method"] = req.get_method()
        captured["body"] = json.loads(req.data.decode("utf-8"))
        captured["headers"] = dict(req.headers)
        # Mock response
        m = MagicMock()
        m.read.return_value = b'{"status":"ok"}'
        m.__enter__ = lambda self: m
        m.__exit__ = lambda *args: None
        return m

    with patch("urllib.request.urlopen", fake_urlopen):
        ok, info = stake_publisher.post_a2a_event({
            "type": "drift_red",
            "agent_id": "ag_test",
            "user_id": "u_test",
            "drift_signals": ["test"],
        })
        assert ok
        assert captured["method"] == "POST"
        body = captured["body"]
        assert body["protocol"] == "a2a/v1"
        assert body["from"] == "compass-memory"
        assert body["to"] == "nautilus-stake"
        assert body["type"] == "DRIFT_EVENT"
        assert body["payload"]["agent_id"] == "ag_test"
        print(f"  [PASS] envelope format correct · type=DRIFT_EVENT")


def run_all():
    tests = [
        test_consume_success,
        test_consume_network_failure_kept,
        test_consume_max_retries_failed,
        test_consume_bad_json,
        test_envelope_format,
    ]
    print("=== compass v0.9.5 stake_publisher tests ===\n")
    failed = 0
    for t in tests:
        print(f"[{t.__name__}]")
        try:
            t()
        except AssertionError as e:
            print(f"  [FAIL] {e}")
            failed += 1
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  [ERROR] {type(e).__name__}: {e}")
            failed += 1
        print()
    print(f"=== {len(tests) - failed}/{len(tests)} passed ===")
    return failed


if __name__ == "__main__":
    sys.exit(run_all())
