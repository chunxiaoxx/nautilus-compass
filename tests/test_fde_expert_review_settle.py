"""Task · expert-review → PoI settle (the real north-star fuel intake).

The human expert review is the FIRST non-self-referential PoI signal (anchor #3).
It does NOT flow through the fde_verdicts bus (that is the soul checklist path
filtered by SETTLE_SOURCES) — the expert verdict is the 复核状态/分项分 format and
flows through the DIRECT credit_from_verdict adapter. This settle runner reads
filled expert review records (the 飞书 Bitable rows · field contract per
T3_feishu_retention_design §2) and credits PoI on fde-capsule-<task_uid> — the
SAME key the soul task-level + capsule pipeline credit, so the expert signal
compounds on the task capsule. Idempotent via a 复核时间 watermark. NO LLM.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from ops import fde_expert_review_settle as ers  # noqa: E402
from proof import fde_poi_adapter as adp  # noqa: E402

NOW = "2026-06-06T12:00:00Z"


def _db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _credit(conn, uid):
    return conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                        "WHERE memory_key=?", (adp.verdict_memory_key({"task_uid": uid}),)).fetchone()


# ── RED 1 · a 通过 review credits the task capsule (mean(分项分)/10) ──────────
def test_pass_review_credits_capsule():
    conn = _db()
    reviews = [{"task_uid": "data_004", "复核状态": "通过",
                "分项分": {"计算": 9, "证据链": 8, "格式": 10}, "复核时间": "2026-06-06T09:00:00Z"}]

    res = ers.settle_expert_reviews(conn, reviews, NOW, placeholder="?")

    assert res["processed"] == 1
    # mean(9,8,10)/10 = 0.9
    assert _credit(conn, "data_004") == pytest.approx((0.9, 1))


# ── RED 2 · a 打回 review applies the negative signal ────────────────────────
def test_reject_review_negative_credit():
    conn = _db()
    reviews = [{"task_uid": "data_001", "复核状态": "打回",
                "分项分": {"完整性": 4}, "复核时间": "2026-06-06T09:00:00Z"}]
    res = ers.settle_expert_reviews(conn, reviews, NOW, placeholder="?")
    assert res["processed"] == 1
    row = _credit(conn, "data_001")
    assert row[0] == pytest.approx(adp.DEFAULT_REJECT_DELTA)


# ── RED 3 · 待复核 (pending) is skipped, no credit ───────────────────────────
def test_pending_review_skipped():
    conn = _db()
    reviews = [{"task_uid": "data_002", "复核状态": "待复核", "复核时间": "2026-06-06T09:00:00Z"}]
    res = ers.settle_expert_reviews(conn, reviews, NOW, placeholder="?")
    assert res["settled"] == []
    assert res["skipped_pending"] == ["data_002"]
    assert _credit(conn, "data_002") is None


# ── RED 4 · 复核时间 watermark filters already-settled reviews ───────────────
def test_since_watermark_filters():
    conn = _db()
    reviews = [
        {"task_uid": "data_003", "复核状态": "通过", "分项分": {"x": 10},
         "复核时间": "2026-06-06T08:00:00Z"},
        {"task_uid": "data_004", "复核状态": "通过", "分项分": {"x": 10},
         "复核时间": "2026-06-06T10:00:00Z"}]
    res = ers.settle_expert_reviews(conn, reviews, NOW, placeholder="?",
                                    since="2026-06-06T08:00:00Z")
    assert res["processed"] == 1
    assert _credit(conn, "data_003") is None       # already settled (at watermark)
    assert _credit(conn, "data_004") is not None
    assert res["last_review_at"] == "2026-06-06T10:00:00Z"


# ── RED 5 · map a feishu Bitable record → review dict (分项分 from score columns)
def test_bitable_record_to_review():
    record = {"record_id": "rec1", "fields": {
        "task_uid": "data_004", "复核状态": "通过",
        "引用准确性": 8, "覆盖完整性": 7, "防编造(幻觉)": 10,
        "复核理由": "归因成立", "复核人": "张三", "复核时间": "2026-06-06T14:00:00Z"}}

    r = ers.bitable_record_to_review(record)

    assert r["task_uid"] == "data_004"
    assert r["复核状态"] == "通过"
    assert r["分项分"] == {"引用准确性": 8, "覆盖完整性": 7, "防编造(幻觉)": 10}
    assert r["复核时间"] == "2026-06-06T14:00:00Z"


# ── RED 6 · a record with no 复核状态 maps to pending (skipped on settle) ─────
def test_bitable_record_missing_status_is_pending():
    record = {"fields": {"task_uid": "data_005"}}
    r = ers.bitable_record_to_review(record)
    assert ers._is_pending(r)


# ── RED 7 · settle a list of bitable records end-to-end ──────────────────────
def test_settle_from_bitable_records():
    conn = _db()
    records = [
        {"fields": {"task_uid": "data_004", "复核状态": "通过", "引用准确性": 10,
                    "复核时间": "2026-06-06T14:00:00Z"}},
        {"fields": {"task_uid": "data_005", "复核状态": "待复核",
                    "复核时间": "2026-06-06T14:01:00Z"}}]
    reviews = [ers.bitable_record_to_review(rec) for rec in records]
    res = ers.settle_expert_reviews(conn, reviews, NOW, placeholder="?")
    assert _credit(conn, "data_004") == pytest.approx((1.0, 1))
    assert res["skipped_pending"] == ["data_005"]
