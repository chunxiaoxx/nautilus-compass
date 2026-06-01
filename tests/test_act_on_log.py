"""E.fix-1/2/3 tests · drift alert act-on instrumentation.

Background: 5/27 finding (session_20260527_drift_loop_open_tuneout) ·
detection side wrote 25k+ drift events to drift_mitigation_log.jsonl with
alert_id but ZERO ack events ever written → act-on rate uncomputable →
closed-loop monitoring impossible.

Plan §E.1/E.2 originally proposed new telemetry/ dir with parallel
event log. Audit 2026-05-30 found:
- drift_mitigation_log.jsonl already records fires (recall.py:159)
- audit_kpi.py already has KPI framework reading usage.jsonl
- feedback.py:cmd_log already handles user fp/tp labels
What's missing: ack writer + rate calculator that joins fires with acks.

E.fix architecture (reuse existing infra):
- E.fix-1: drift/act_log.py adds log_drift_ack writing to SAME
  drift_mitigation_log sidecar (distinguished by kind: "ack").
- E.fix-2: audit_kpi.act_on_rate reads same sidecar · groups by alert_id ·
  counts ack-covered fires within window.
- E.fix-3: feedback.py:cmd_log also calls log_drift_ack on fp/tp marks ·
  so user CLI labels surface as acks in the rate metric.

Flat layout per C.3 / D.fix conventions.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

# Ensure repo root on sys.path
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ─── E.fix-1: drift/act_log.py ────────────────────────────────────


def test_log_drift_ack_writes_ack_record(tmp_path):
    """E.fix-1 · ack record has kind=ack + alert_id + status + ts."""
    from drift.act_log import log_drift_ack

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    log_drift_ack(alert_id="a-test1", status="fp", sidecar=sidecar)

    lines = [l for l in sidecar.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(lines) == 1
    rec = json.loads(lines[0])
    assert rec["kind"] == "ack"
    assert rec["alert_id"] == "a-test1"
    assert rec["status"] == "fp"
    assert "ts" in rec


def test_log_drift_ack_empty_alert_id_noop(tmp_path):
    """E.fix-1 · empty alert_id must not write anything (defensive)."""
    from drift.act_log import log_drift_ack

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    log_drift_ack(alert_id="", status="acknowledged", sidecar=sidecar)
    log_drift_ack(alert_id=None, status="acknowledged", sidecar=sidecar)  # type: ignore[arg-type]

    assert not sidecar.exists() or sidecar.read_text() == ""


def test_iter_drift_events_skips_corrupt_lines(tmp_path):
    """E.fix-1 · reader returns valid records · drops corrupt JSON silently."""
    from drift.act_log import iter_drift_events

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    sidecar.write_text(
        '{"kind": "ack", "alert_id": "a1", "status": "fp"}\n'
        'corrupt-line-no-json\n'
        '\n'
        '{"alert_id": "a2", "mitigation_injected": true}\n',
        encoding="utf-8",
    )

    records = list(iter_drift_events(sidecar))
    assert len(records) == 2
    assert records[0]["alert_id"] == "a1"
    assert records[1]["alert_id"] == "a2"


# ─── E.fix-2: audit_kpi.act_on_rate ───────────────────────────────


def _write_drift_log(sidecar: Path, fires: list[tuple[str, str]], acks: list[tuple[str, str]]):
    """Helper · write fire + ack records with given (alert_id, iso_ts) pairs."""
    sidecar.parent.mkdir(parents=True, exist_ok=True)
    with open(sidecar, "w", encoding="utf-8") as f:
        for alert_id, ts in fires:
            f.write(json.dumps({
                "ts": ts,
                "alert_id": alert_id,
                "kind": "score_threshold",
                "mitigation_injected": True,
            }) + "\n")
        for alert_id, ts in acks:
            f.write(json.dumps({
                "ts": ts,
                "alert_id": alert_id,
                "kind": "ack",
                "status": "fp",
            }) + "\n")


def test_act_on_rate_zero_when_no_acks(tmp_path):
    """E.fix-2 · 5 fires + 0 acks → rate = 0.0 · fires=5 · acked=0."""
    from audit_kpi import act_on_rate

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    fires = [(f"a-{i}", now_iso) for i in range(5)]
    _write_drift_log(sidecar, fires=fires, acks=[])

    result = act_on_rate(sidecar=sidecar, window_hours=168)
    assert result["fires"] == 5
    assert result["acked"] == 0
    assert result["rate"] == 0.0


def test_act_on_rate_with_partial_acks(tmp_path):
    """E.fix-2 · 4 fires · 2 of them acked → rate = 0.5."""
    from audit_kpi import act_on_rate

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_drift_log(
        sidecar,
        fires=[(f"a-{i}", now_iso) for i in range(4)],
        acks=[("a-0", now_iso), ("a-2", now_iso)],
    )

    result = act_on_rate(sidecar=sidecar, window_hours=168)
    assert result["fires"] == 4
    assert result["acked"] == 2
    assert result["rate"] == 0.5


def test_act_on_rate_window_filter_drops_old_fires(tmp_path):
    """E.fix-2 · fires outside window_hours not counted · only recent fires."""
    from audit_kpi import act_on_rate

    sidecar = tmp_path / "drift_mitigation_log.jsonl"
    now = datetime.now(timezone.utc)
    recent_iso = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    old_iso = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _write_drift_log(
        sidecar,
        fires=[("a-recent", recent_iso), ("a-old", old_iso)],
        acks=[("a-recent", recent_iso)],
    )

    result = act_on_rate(sidecar=sidecar, window_hours=24)
    assert result["fires"] == 1, "old fire should be filtered"
    assert result["acked"] == 1
    assert result["rate"] == 1.0


# ─── E.fix-3: feedback.cmd_log wires log_drift_ack ────────────────


def test_feedback_cmd_log_also_writes_drift_ack(tmp_path, monkeypatch):
    """E.fix-3 · `feedback log <alert_id> fp` writes both feedback.jsonl AND
    ack record into drift_mitigation_log.jsonl · so act_on_rate sees user-labeled
    alerts as acked.
    """
    import feedback as feedback_mod

    fake_feedback = tmp_path / "feedback.jsonl"
    fake_mitigation = tmp_path / "drift_mitigation_log.jsonl"
    monkeypatch.setattr(feedback_mod, "FEEDBACK_LOG", fake_feedback)
    # Patch the act_log default sidecar so cmd_log's ack also lands here
    import drift.act_log as act_log_mod
    monkeypatch.setattr(act_log_mod, "DEFAULT_SIDECAR", fake_mitigation)

    class Args:
        alert_id = "a-wire-test"
        verdict = "fp"

    feedback_mod.cmd_log(Args())

    # feedback.jsonl side
    fb_lines = [l for l in fake_feedback.read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(fb_lines) == 1
    fb_rec = json.loads(fb_lines[0])
    assert fb_rec["alert_id"] == "a-wire-test"
    assert fb_rec["verdict"] == "fp"

    # drift_mitigation_log side (ack record)
    mt_lines = [l for l in fake_mitigation.read_text(encoding="utf-8").splitlines() if l.strip()]
    ack_recs = [json.loads(l) for l in mt_lines if json.loads(l).get("kind") == "ack"]
    assert len(ack_recs) == 1
    assert ack_recs[0]["alert_id"] == "a-wire-test"
    assert ack_recs[0]["status"] == "fp"
