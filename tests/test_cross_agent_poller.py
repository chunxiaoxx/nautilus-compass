"""Tests for ops/cross_agent_outcome_poller.py · L4 cross-agent outcome poller.

Covers pure transforms (DB row -> compass session_*.md) + watermark state +
drift-signal aggregation. DB I/O (ssh tunnel + psycopg2) is integration-verified
separately and kept thin / not unit-tested here.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

import importlib.util
import sys

_OPS = Path(__file__).resolve().parent.parent / "ops" / "cross_agent_outcome_poller.py"
_spec = importlib.util.spec_from_file_location("cross_agent_outcome_poller", _OPS)
poller = importlib.util.module_from_spec(_spec)
sys.modules["cross_agent_outcome_poller"] = poller
_spec.loader.exec_module(poller)


# ---------------------------------------------------------------- parse_secret
def test_parse_secret_key_value_lines(tmp_path: Path):
    f = tmp_path / ".secret"
    f.write_text(
        "compass_sub read-only credential (do not commit)\n"
        "password: s3cr3t-with:colon\n"
        "host: localhost\n"
        "port: 5432\n"
        "dbname: nautilus_production\n"
        "schema: public\n",
        encoding="utf-8",
    )
    cfg = poller.parse_secret(str(f))
    assert cfg["password"] == "s3cr3t-with:colon"  # value may itself contain colon
    assert cfg["host"] == "localhost"
    assert cfg["port"] == "5432"
    assert cfg["dbname"] == "nautilus_production"
    # the comment header line (no key:value) is ignored
    assert "compass_sub" not in cfg


def test_parse_secret_missing_password_raises(tmp_path: Path):
    f = tmp_path / ".secret"
    f.write_text("host: localhost\nport: 5432\n", encoding="utf-8")
    with pytest.raises(ValueError):
        poller.parse_secret(str(f))


# ------------------------------------------------------ build_b2_session_md
def _b2_row(**over):
    row = {
        "id": 125824,
        "agent_id": "v5-singleton",
        "tool_name": "write_file",
        "args_summary": "path=foo.py",
        "output_summary": "wrote 12 lines",
        "success": True,
        "elapsed_ms": 340,
        "ts": datetime(2026, 6, 2, 14, 30, tzinfo=timezone.utc),
        "phase": "ship",
    }
    row.update(over)
    return row


def test_build_b2_filename_deterministic_from_id_and_ts():
    fn1, _ = poller.build_b2_session_md(_b2_row())
    fn2, _ = poller.build_b2_session_md(_b2_row())
    assert fn1 == fn2  # idempotent · same row -> same filename (no now())
    assert fn1.startswith("session_")
    assert fn1.endswith(".md")
    assert "125824" in fn1  # stable id present -> watermark-safe dedup


def test_build_b2_success_is_green_failure_is_yellow():
    _, ok = poller.build_b2_session_md(_b2_row(success=True))
    _, bad = poller.build_b2_session_md(_b2_row(success=False))
    assert "drift: green" in ok
    assert "drift: yellow" in bad


def test_build_b2_frontmatter_has_recall_fields():
    _, md = poller.build_b2_session_md(_b2_row())
    assert md.startswith("---")
    for field in ("type: cross-agent-tool-call", "agent_type: v5-singleton",
                  "thread_id:", "tool_name: write_file"):
        assert field in md, f"missing {field!r}"
    # body retains the source summary for recall
    assert "wrote 12 lines" in md


def test_build_b2_handles_non_ascii_and_none_summary():
    # output_summary None and non-ascii agent must not crash; filename ascii-safe
    fn, md = poller.build_b2_session_md(
        _b2_row(agent_id="才燊-agent", output_summary=None, args_summary=None)
    )
    assert fn.isascii()
    assert "---" in md


# ------------------------------------------------------ build_a2_session_md
def _a2_row(**over):
    row = {
        "cycle_id": "cyc_20260602_001",
        "spec": "add poller",
        "ship_status": "shipped",
        "semantic_pass": True,
        "tests_pass": True,
        "actual_lines_added": 120,
        "actual_lines_removed": 4,
        "drift_ratio": 0.02,
        "composite_score": 0.91,
        "git_sha": "abc1234",
        "created_at": datetime(2026, 6, 2, 9, 0, tzinfo=timezone.utc),
        "goal_source": "self-audit",
        "fitness_delta": 0.05,
    }
    row.update(over)
    return row


def test_build_a2_filename_deterministic_from_cycle_id():
    fn1, _ = poller.build_a2_session_md(_a2_row())
    fn2, _ = poller.build_a2_session_md(_a2_row())
    assert fn1 == fn2
    assert "cyc_20260602_001" in fn1
    assert fn1.endswith(".md")


def test_build_a2_failed_tests_is_drift_signal():
    _, ok = poller.build_a2_session_md(_a2_row(semantic_pass=True, tests_pass=True))
    _, bad = poller.build_a2_session_md(_a2_row(tests_pass=False))
    assert "drift: green" in ok
    assert "drift: yellow" in bad


def test_build_a2_success_with_null_checks_is_green():
    # real data: semantic_pass / tests_pass are NULL; ship_status carries health.
    # ship_status='success' with null checks must NOT be a false drift (cry-wolf).
    _, ok = poller.build_a2_session_md(
        _a2_row(ship_status="success", semantic_pass=None, tests_pass=None))
    assert "drift: green" in ok
    _, bad = poller.build_a2_session_md(
        _a2_row(ship_status="fail", semantic_pass=None, tests_pass=None))
    assert "drift: yellow" in bad


def test_build_a2_frontmatter_has_fields():
    _, md = poller.build_a2_session_md(_a2_row())
    assert "type: cross-agent-cycle-outcome" in md
    assert "ship_status: shipped" in md
    assert "composite_score" in md


# ------------------------------------------------------ compute_drift_signal
def test_drift_signal_all_success_no_alert():
    rows = [_b2_row(id=i, success=True) for i in range(10)]
    sig = poller.compute_drift_signal("v5-singleton", rows)
    assert sig["agent_id"] == "v5-singleton"
    assert sig["n"] == 10
    assert sig["success_rate"] == 1.0
    assert sig["alert"] is False


def test_drift_signal_low_success_rate_alerts():
    rows = ([_b2_row(id=i, success=False) for i in range(6)]
            + [_b2_row(id=100 + i, success=True) for i in range(4)])
    sig = poller.compute_drift_signal("v5-singleton", rows)
    assert sig["n"] == 10
    assert sig["success_rate"] == pytest.approx(0.4)
    assert sig["alert"] is True  # 40% < 0.5 threshold


def test_drift_signal_too_few_samples_no_alert():
    # below min-sample floor -> never alert (avoid cry-wolf on n=1)
    rows = [_b2_row(id=1, success=False)]
    sig = poller.compute_drift_signal("v5-singleton", rows)
    assert sig["alert"] is False
    assert sig["n"] == 1


# -------------------------------------------------- b2 rollup (anti-flooding)
def test_b2_rollup_single_file_for_many_agents():
    # b2 is 125k rows · MUST NOT write per-row files · one rollup summarises all
    signals = [
        {"agent_id": "v5", "n": 100, "successes": 95, "success_rate": 0.95, "alert": False},
        {"agent_id": "kairos", "n": 20, "successes": 6, "success_rate": 0.30, "alert": True},
    ]
    fn, md = poller.build_b2_rollup_session_md(signals, window_label="24h")
    assert fn.startswith("session_") and fn.endswith(".md")
    assert "xrollup" in fn  # distinct from per-call xacall files
    assert "v5" in md and "kairos" in md
    assert "type: cross-agent-drift-rollup" in md


def test_b2_rollup_drift_yellow_when_any_alert():
    sig_ok = [{"agent_id": "v5", "n": 100, "successes": 99, "success_rate": 0.99, "alert": False}]
    sig_bad = [{"agent_id": "k", "n": 20, "successes": 5, "success_rate": 0.25, "alert": True}]
    _, ok = poller.build_b2_rollup_session_md(sig_ok, window_label="24h")
    _, bad = poller.build_b2_rollup_session_md(sig_bad, window_label="24h")
    assert "drift: green" in ok
    assert "drift: yellow" in bad


def test_b2_rollup_empty_signals_is_stall_marker():
    # no rows in window -> still emit a marker (daemon-stall / silence is signal)
    fn, md = poller.build_b2_rollup_session_md([], window_label="24h")
    assert fn.endswith(".md")
    assert "no agent tool activity" in md.lower() or "0 agent" in md.lower()


# ------------------------------------------------------ watermark state
def test_watermark_roundtrip(tmp_path: Path):
    p = tmp_path / "wm.json"
    poller.save_watermark(str(p), {"last_b2_id": 999, "last_a2_ts": "2026-06-02T09:00:00+00:00"})
    wm = poller.load_watermark(str(p))
    assert wm["last_b2_id"] == 999
    assert wm["last_a2_ts"] == "2026-06-02T09:00:00+00:00"


def test_watermark_missing_file_returns_defaults(tmp_path: Path):
    wm = poller.load_watermark(str(tmp_path / "nope.json"))
    assert wm["last_b2_id"] == 0
    assert wm["last_a2_ts"] is None
