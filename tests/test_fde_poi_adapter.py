"""T3/T4 · FDE expert-review verdict → PoI credit adapter (the dual-flywheel
bite). Expert verdict (通过/打回 + 分项分) is the EXTERNAL ground truth: a passed
review credits the FDE task-template memory_key (→ boosted in future recall = the
compounding loop), a rejection applies a negative signal. NO LLM. Mock verdicts,
sqlite poi_credit — no live feishu / no live postgres.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))

from proof import fde_poi_adapter as adp  # noqa: E402


PASS_VERDICT = {
    "task_uid": "HR-CBJ-001",
    "复核状态": "通过",
    "分项分": {"计算与公式": 9, "证据链": 8, "格式交付": 9},
    "复核理由": "测算口径正确,公式活;扣分点=缺2024公告页码citation",
    "复核人": "专家A",
}
REJECT_VERDICT = {
    "task_uid": "HR-ZP-002",
    "复核状态": "打回",
    "分项分": {"完整性": 4},
    "复核理由": "信息密度不真实,像泛模板,打回重出",
    "复核人": "专家B",
}


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
        "cumulative_impact REAL NOT NULL DEFAULT 0, "
        "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)"
    )
    conn.commit()
    return conn


# ── unit: verdict → outcome ──
def test_pass_maps_to_success():
    assert adp.verdict_to_outcome(PASS_VERDICT) == {"success": True}


def test_reject_maps_to_failure():
    assert adp.verdict_to_outcome(REJECT_VERDICT) == {"success": False}


def test_unknown_maps_to_pending():
    assert adp.verdict_to_outcome({"复核状态": "待复核"}) == {"success": None}


def test_english_labels_supported():
    assert adp.verdict_to_outcome({"status": "approved"}) == {"success": True}
    assert adp.verdict_to_outcome({"status": "rejected"}) == {"success": False}


# ── unit: verdict → delta ──
def test_pass_delta_is_mean_dim_over_10():
    # mean(9,8,9)=8.667 → /10 = 0.8667
    assert adp.verdict_delta(PASS_VERDICT) == pytest.approx(0.8667, abs=1e-4)


def test_reject_delta_is_negative():
    assert adp.verdict_delta(REJECT_VERDICT) == pytest.approx(-0.5)


def test_pass_without_scores_is_unit_positive():
    assert adp.verdict_delta({"复核状态": "通过"}) == pytest.approx(1.0)


def test_pending_delta_zero():
    assert adp.verdict_delta({"复核状态": "待复核"}) == 0.0


# ── unit: memory_key derivation ──
def test_memory_key_matches_capsule_naming():
    # must match feishu_retention_scaffold: fde-capsule-<uid lower>
    assert adp.verdict_memory_key(PASS_VERDICT) == "fde-capsule-hr-cbj-001"


# ── e2e: verdict → poi_credit upsert (sqlite) ──
def test_pass_credits_memory_key():
    conn = _mk_db()
    res = adp.credit_from_verdict(conn, PASS_VERDICT,
                                  adp.verdict_memory_key(PASS_VERDICT),
                                  "2026-06-05T19:00:00Z", placeholder="?")
    assert res["action_outcome"] == "success"
    row = conn.execute(
        "SELECT cumulative_impact, event_count FROM poi_credit WHERE memory_key=?",
        ("fde-capsule-hr-cbj-001",)).fetchone()
    assert row[0] == pytest.approx(0.8667, abs=1e-4)
    assert row[1] == 1


def test_reject_applies_negative_credit():
    conn = _mk_db()
    res = adp.credit_from_verdict(conn, REJECT_VERDICT,
                                  adp.verdict_memory_key(REJECT_VERDICT),
                                  "2026-06-05T19:00:00Z", placeholder="?")
    assert res["action_outcome"] == "failure"
    row = conn.execute(
        "SELECT cumulative_impact FROM poi_credit WHERE memory_key=?",
        ("fde-capsule-hr-zp-002",)).fetchone()
    assert row[0] == pytest.approx(-0.5)


def test_repeated_pass_accumulates():
    conn = _mk_db()
    mk = adp.verdict_memory_key(PASS_VERDICT)
    for _ in range(3):
        adp.credit_from_verdict(conn, PASS_VERDICT, mk,
                                "2026-06-05T19:00:00Z", placeholder="?")
    row = conn.execute(
        "SELECT cumulative_impact, event_count FROM poi_credit WHERE memory_key=?",
        (mk,)).fetchone()
    assert row[0] == pytest.approx(0.8667 * 3, abs=1e-3)
    assert row[1] == 3


def test_pending_is_noop():
    conn = _mk_db()
    res = adp.credit_from_verdict(conn, {"task_uid": "X", "复核状态": "待复核"},
                                  "fde-capsule-x", "2026-06-05T19:00:00Z",
                                  placeholder="?")
    assert res["action_outcome"] == "pending"
    assert conn.execute("SELECT COUNT(*) FROM poi_credit").fetchone()[0] == 0
