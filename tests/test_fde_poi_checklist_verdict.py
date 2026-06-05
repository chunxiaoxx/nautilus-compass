"""T3 alignment · consume soul's REAL checklist_scorer verdict format.

soul's checklist_scorer emits {score, passed, total, veto_failed, overall_pass,
items:[{id,pass,veto,reason}]} (see _v5_data001_real_verdict.json), NOT the mock
复核状态/分项分 shape. This aligns fde_poi_adapter to that real format so the PoI
consumer works on the actual verdict stream / fde_verdicts table. NO LLM.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from proof import fde_poi_adapter as adp  # noqa: E402

PASS_V = {"score": 1.0, "passed": 11, "total": 11, "veto_failed": False,
          "overall_pass": True,
          "items": [{"id": "c1", "pass": True, "veto": True, "reason": "ok"}]}
PARTIAL_PASS_V = {"score": 0.82, "passed": 9, "total": 11, "veto_failed": False,
                  "overall_pass": True, "items": []}
VETO_FAIL_V = {"score": 0.9, "passed": 10, "total": 11, "veto_failed": True,
               "overall_pass": False,
               "items": [{"id": "c2", "pass": False, "veto": True, "reason": "PII leak"}]}
REJECT_V = {"score": 0.3, "passed": 3, "total": 10, "veto_failed": False,
            "overall_pass": False, "items": []}


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def test_checklist_pass_is_success():
    assert adp.checklist_verdict_to_outcome(PASS_V) == {"success": True}


def test_checklist_veto_fail_is_failure():
    # veto_failed overrides any score → failure
    assert adp.checklist_verdict_to_outcome(VETO_FAIL_V) == {"success": False}


def test_checklist_reject_is_failure():
    assert adp.checklist_verdict_to_outcome(REJECT_V) == {"success": False}


def test_checklist_delta_uses_score_on_pass():
    # pass → delta = score (the checklist pass rate, GOAL's "checklist 通过率")
    assert adp.checklist_verdict_delta(PASS_V) == pytest.approx(1.0)
    assert adp.checklist_verdict_delta(PARTIAL_PASS_V) == pytest.approx(0.82)


def test_checklist_delta_negative_on_fail():
    assert adp.checklist_verdict_delta(VETO_FAIL_V) == pytest.approx(-0.5)
    assert adp.checklist_verdict_delta(REJECT_V) == pytest.approx(-0.5)


def test_credit_from_checklist_verdict_e2e():
    conn = _mk_db()
    res = adp.credit_from_checklist_verdict(conn, PARTIAL_PASS_V, "data_001",
                                            "2026-06-05T19:00:00Z", placeholder="?")
    assert res["action_outcome"] == "success"
    assert res["memory_key"] == "fde-capsule-data_001"
    row = conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                       "WHERE memory_key=?", ("fde-capsule-data_001",)).fetchone()
    assert row[0] == pytest.approx(0.82)
    assert row[1] == 1


def test_credit_from_checklist_veto_fail_negative():
    conn = _mk_db()
    res = adp.credit_from_checklist_verdict(conn, VETO_FAIL_V, "data_009",
                                            "2026-06-05T19:00:00Z", placeholder="?")
    assert res["action_outcome"] == "failure"
    row = conn.execute("SELECT cumulative_impact FROM poi_credit WHERE memory_key=?",
                       ("fde-capsule-data_009",)).fetchone()
    assert row[0] == pytest.approx(-0.5)
