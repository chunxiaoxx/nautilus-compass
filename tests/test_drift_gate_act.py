"""S4 module 5 · drift/gate_act.py smoke tests."""
import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proof.poi_schema import ProofOfImpact
from drift.gate_act import (
    act_stage_drift_check, log_drift_act_event, check_and_log,
    DRIFT_ACT_LOG, SEVERITY_HIGH, SEVERITY_MEDIUM,
)


def _make_memory(tmp: Path, name: str, drift: str = "green") -> Path:
    p = tmp / name
    p.write_text(f"---\nname: {name}\ndrift: {drift}\n---\nbody\n", encoding="utf-8")
    return p


def _poi(outcome="success", cites=None, declaration="supports"):
    return ProofOfImpact(
        action_id="b-t",
        agent_id="a",
        cited_memory_paths=cites or ["x.md"],
        action_outcome=outcome,
        timestamp_action="2026-05-21T12:00:00Z",
        timestamp_outcome="2026-05-21T12:05:00Z",
        declaration_type=declaration,
    )


def test_1_red_drift_plus_failure_high():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "r.md", drift="red")
        poi = _poi(outcome="failure", cites=[str(m)])
        r = act_stage_drift_check(poi)
        assert r["count"] == 1
        assert r["signals"][0]["severity"] == SEVERITY_HIGH
    print("OK 1 red + failure → HIGH signal")


def test_2_yellow_drift_plus_failure_medium():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "y.md", drift="yellow")
        poi = _poi(outcome="failure", cites=[str(m)])
        r = act_stage_drift_check(poi)
        assert r["count"] == 1
        assert r["signals"][0]["severity"] == SEVERITY_MEDIUM
    print("OK 2 yellow + failure → MEDIUM signal")


def test_3_green_plus_success_no_signal():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "g.md", drift="green")
        poi = _poi(outcome="success", cites=[str(m)])
        r = act_stage_drift_check(poi)
        assert r["count"] == 0
    print("OK 3 green + success → no signal")


def test_4_contradicts_plus_success_high():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "g.md", drift="green")
        poi = _poi(outcome="success", cites=[str(m)], declaration="contradicts")
        r = act_stage_drift_check(poi)
        assert r["count"] >= 1
        assert any(s["severity"] == SEVERITY_HIGH for s in r["signals"])
    print("OK 4 contradicts + success → HIGH (stale memory)")


def test_5_log_writes_jsonl():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        cache = tmp / "_cache"
        poi = _poi()
        sig = {"signals": [{"severity": "high", "reason": "test"}], "count": 1}
        log_path = log_drift_act_event(poi, sig, cache_dir=cache)
        assert log_path.exists()
        entry = json.loads(log_path.read_text(encoding="utf-8").strip())
        assert entry["action_id"] == "b-t"
        assert entry["signal_count"] == 1
    print("OK 5 log writes jsonl")


def test_6_check_and_log_no_signal_no_write():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        cache = tmp / "_cache"
        m = _make_memory(tmp, "g.md", drift="green")
        poi = _poi(outcome="success", cites=[str(m)])
        r = check_and_log(poi, cache_dir=cache)
        assert r["count"] == 0
        # No log file written
        assert not (cache / DRIFT_ACT_LOG).exists() or \
               (cache / DRIFT_ACT_LOG).stat().st_size == 0
    print("OK 6 no signal → no log write")


def test_7_check_and_log_with_signal_writes():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        cache = tmp / "_cache"
        m = _make_memory(tmp, "r.md", drift="red")
        poi = _poi(outcome="failure", cites=[str(m)])
        r = check_and_log(poi, cache_dir=cache)
        assert r["count"] >= 1
        assert (cache / DRIFT_ACT_LOG).exists()
    print("OK 7 signal → log written")


def test_8_pending_outcome_no_signal():
    """pending outcome shouldn't fire signals (still in flight)."""
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m = _make_memory(tmp, "r.md", drift="red")
        poi = _poi(outcome="pending", cites=[str(m)])
        r = act_stage_drift_check(poi)
        # pending doesn't match failure branch · no red+failure signal
        # but check_and_log not invoked here · just verify no false positive
        red_failure_signals = [s for s in r["signals"]
                               if "red-drift" in s["reason"]]
        assert len(red_failure_signals) == 0
    print("OK 8 pending outcome no red+failure")


if __name__ == "__main__":
    tests = [test_1_red_drift_plus_failure_high, test_2_yellow_drift_plus_failure_medium,
             test_3_green_plus_success_no_signal, test_4_contradicts_plus_success_high,
             test_5_log_writes_jsonl, test_6_check_and_log_no_signal_no_write,
             test_7_check_and_log_with_signal_writes, test_8_pending_outcome_no_signal]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} drift.gate_act smoke pass")
