"""cnt_c3 · PoI consumer for soul's rsi_delta feed (pre-built · wire on deploy).

soul's `GET /api/platform/fde/rsi_delta/{task_uid}?escapes_only=true` returns the
PoI-eligible ΔReward rows (escapes_noise=True only). This consumer turns each row
into a PoI credit, honoring the spec's hard rules:
  · credit ∝ delta_reward (>0 · already past the escapes gate)
  · idempotent by delta_id (same delta never double-credits)
  · attribution: credit accrues to producer_model + grounding_source.policy
    (the WINNING strategy — external selection pressure points at "what produces")
  · escapes_noise=False NEVER credits (feed pre-filters; we self-filter defensively).

Reuses proof.poi_credit_store.upsert_credit (central ledger). NO LLM. NO live
endpoint — fixture rows match soul's exact schema; wire `fetch_rsi_delta_feed` to
the live endpoint only after G-cloud deploy.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from proof import fde_rsi_delta_consumer as c  # noqa: E402
from proof.poi_credit_store import fetch_all_credits  # noqa: E402

NOW = "2026-06-09T02:00:00Z"


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _row(**over):
    r = {
        "delta_id": "d1", "benchmark": "autolab_radix_sort", "task_uid": "radix_sort",
        "producer_model": "deepseek-chat", "n_bare": 10, "n_grounded": 10,
        "bare_mean": 0.1835, "grounded_mean": 0.2568, "delta_reward": 0.0734,
        "p_value": 0.0215, "escapes_noise": True,
        "grounding_source": {"policy": "correctness-first", "round": 2,
                             "corpus": "autolab_avoid_radix_sort"},
        "created_at": NOW,
    }
    r.update(over)
    return r


# ── RED 1 · escapes_noise=False NEVER credits (defensive self-filter) ────────
def test_escapes_false_never_credits():
    conn = _mk_db()
    res = c.consume_rsi_delta(conn, _row(escapes_noise=False), NOW, placeholder="?")
    assert res["credited"] is False
    assert res["reason"] == "not_escapes"
    assert fetch_all_credits(conn) == {}


# ── RED 2 · credit == delta_reward, on the attributed key ────────────────────
def test_credit_equals_delta_reward():
    conn = _mk_db()
    res = c.consume_rsi_delta(conn, _row(), NOW, placeholder="?")
    assert res["credited"] is True
    assert res["delta"] == 0.0734
    assert fetch_all_credits(conn)[res["memory_key"]] == 0.0734


# ── RED 3 · memory_key attributes producer_model + grounding policy ──────────
def test_memory_key_attributes_producer_and_policy():
    key = c.rsi_delta_memory_key(_row())
    assert "deepseek-chat" in key
    assert "correctness-first" in key
    other = c.rsi_delta_memory_key(_row(grounding_source={"policy": "aggressive"}))
    assert other != key


# ── RED 4 · idempotent by delta_id (DB-backed dedup · same delta never twice) ─
def test_dedup_by_delta_id():
    conn = _mk_db()
    c.ensure_processed_table(conn)
    is_proc = lambda did: c.db_is_processed(conn, did, "?")        # noqa: E731
    mark = lambda did: c.db_mark_processed(conn, did, NOW, "?")    # noqa: E731
    r = _row(delta_id="dX")
    first = c.consume_rsi_delta(conn, r, NOW, placeholder="?",
                               is_processed=is_proc, mark_processed=mark)
    second = c.consume_rsi_delta(conn, r, NOW, placeholder="?",
                                is_processed=is_proc, mark_processed=mark)
    assert first["credited"] is True
    assert second["credited"] is False
    assert second["reason"] == "duplicate"
    # credited exactly once → cumulative_impact is a single delta, not doubled
    assert fetch_all_credits(conn)[first["memory_key"]] == 0.0734


# ── RED 5 · non-positive delta is skipped (defensive · feed should pre-gate) ─
def test_non_positive_delta_skipped():
    conn = _mk_db()
    res = c.consume_rsi_delta(conn, _row(delta_reward=0.0), NOW, placeholder="?")
    assert res["credited"] is False
    assert res["reason"] == "non_positive"
    assert fetch_all_credits(conn) == {}


# ── RED 6 · batch feed credits ONLY eligible rows + sums correctly ───────────
def test_feed_batch_only_credits_eligible():
    conn = _mk_db()
    rows = [
        _row(delta_id="a", delta_reward=0.05),                       # ok
        _row(delta_id="b", escapes_noise=False, delta_reward=0.9),   # not escapes
        _row(delta_id="c", delta_reward=-0.1),                       # non positive
        _row(delta_id="d", delta_reward=0.03),                       # ok
    ]
    out = c.consume_rsi_delta_feed(conn, rows, NOW, placeholder="?")
    assert out["credited_count"] == 2
    assert out["total_delta"] == 0.08  # 0.05 + 0.03, same key → accrues
    assert fetch_all_credits(conn)[c.rsi_delta_memory_key(_row())] == 0.08
