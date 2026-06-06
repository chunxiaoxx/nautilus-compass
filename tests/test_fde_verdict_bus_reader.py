"""G-platform-spine · compass read path against the LOCKED fde_verdicts schema.

Platform built the verdict-bus (W1): `fde_verdicts` schema locked + ingest
endpoint live (docs/FDE_VERDICT_BUS_CONTRACT.md). compass owns the PoI mapping:
`from_fde_verdicts` reads the bus rows (read-only) and credits task-level PoI
(fde-capsule-<task_uid>) via the existing checklist-verdict adapter. Buildable +
testable NOW against the locked schema with a sqlite mock; only the LIVE cloud
SELECT is gated on G-cloud (GRANT SELECT ... TO compass_sub). NO LLM.

Contract columns consumed: verdict_id, task_uid, overall_pass, veto_failed,
score, items, created_at (items as JSONB list in postgres / json TEXT in sqlite).
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from proof import fde_verdict_bus_reader as bus  # noqa: E402


def _mk_bus():
    """sqlite mock of the locked fde_verdicts schema (items as json TEXT)."""
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE fde_verdicts (id INTEGER PRIMARY KEY, "
        "verdict_id TEXT UNIQUE NOT NULL, task_uid TEXT NOT NULL, source TEXT NOT NULL, "
        "checklist_uid TEXT, overall_pass INTEGER NOT NULL, veto_failed INTEGER NOT NULL, "
        "score REAL NOT NULL, items TEXT NOT NULL DEFAULT '[]', artifacts TEXT, "
        "created_at TEXT NOT NULL)")
    conn.commit()
    return conn


def _ins(conn, verdict_id, task_uid, overall_pass, veto_failed, score, items, created_at,
         source="soul"):  # soul = the authoritative PoI fitness source (settles)
    conn.execute(
        "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, "
        "veto_failed, score, items, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (verdict_id, task_uid, source, int(overall_pass), int(veto_failed), score,
         json.dumps(items), created_at))
    conn.commit()


def _mk_credit():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _credit(conn, mk):
    return conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                        "WHERE memory_key=?", (mk,)).fetchone()


ITEMS = [{"id": "c1", "pass": True, "veto": True, "reason": "ok"}]


# ── RED 1 · reads bus rows → task-level PoI credits ──────────────────────────
def test_reads_verdicts_and_credits_task_poi():
    busc = _mk_bus()
    _ins(busc, "v-1", "data_001", True, False, 1.0, ITEMS, "2026-06-05T02:47:00Z")
    _ins(busc, "v-2", "data_002", True, False, 0.8333, ITEMS, "2026-06-05T11:22:00Z")
    creditc = _mk_credit()

    res = bus.from_fde_verdicts(busc, creditc, placeholder="?")

    assert res["processed"] == 2
    assert _credit(creditc, "fde-capsule-data_001") == pytest.approx((1.0, 1))
    assert _credit(creditc, "fde-capsule-data_002") == pytest.approx((0.8333, 1))
    assert res["last_created_at"] == "2026-06-05T11:22:00Z"


# ── RED 2 · `since` watermark filters already-processed rows ─────────────────
def test_since_watermark_filters():
    busc = _mk_bus()
    _ins(busc, "v-1", "data_001", True, False, 1.0, ITEMS, "2026-06-05T02:47:00Z")
    _ins(busc, "v-2", "data_002", True, False, 0.8333, ITEMS, "2026-06-05T11:22:00Z")
    creditc = _mk_credit()

    res = bus.from_fde_verdicts(busc, creditc, since="2026-06-05T02:47:00Z",
                                placeholder="?")
    assert res["processed"] == 1
    assert _credit(creditc, "fde-capsule-data_001") is None  # already settled
    assert _credit(creditc, "fde-capsule-data_002") is not None


# ── RED 3 · veto_failed row → negative PoI (V5 executed_failed ruling) ───────
def test_veto_failed_negative_credit():
    busc = _mk_bus()
    _ins(busc, "v-9", "data_009", False, True, 0.9,
         [{"id": "c2", "pass": False, "veto": True, "reason": "PII leak"}],
         "2026-06-05T12:00:00Z")
    creditc = _mk_credit()
    res = bus.from_fde_verdicts(busc, creditc, placeholder="?")
    assert res["processed"] == 1
    row = _credit(creditc, "fde-capsule-data_009")
    assert row[0] == pytest.approx(-0.5)


# ── peek · read-only dry-run lists rows WITHOUT crediting ────────────────────
def test_peek_is_readonly_and_lists_rows():
    busc = _mk_bus()
    _ins(busc, "v-1", "data_001", True, False, 1.0, ITEMS, "2026-06-05T02:47:00Z")
    _ins(busc, "v-2", "data_002", True, False, 0.8333, ITEMS, "2026-06-05T11:22:00Z")
    creditc = _mk_credit()

    rows = bus.peek_fde_verdicts(busc, placeholder="?")
    assert [r["task_uid"] for r in rows] == ["data_001", "data_002"]
    assert rows[1]["score"] == pytest.approx(0.8333)
    # nothing credited (read-only)
    assert _credit(creditc, "fde-capsule-data_001") is None
    # since filter
    assert len(bus.peek_fde_verdicts(busc, since="2026-06-05T02:47:00Z",
                                     placeholder="?")) == 1


# ── RED · only authoritative source ('soul') settles; kairos-opus二审 excluded ─
# (platform-soul 2026-06-06: V5 adds Kairos Opus adversarial 二审 as
# source='kairos-opus'; settling those double-counts the same task's PoI — the
# reader must settle only the soul 一审 fitness signal.)
def test_only_soul_source_settles_kairos_excluded():
    busc = _mk_bus()
    _ins(busc, "v-soul", "data_001", True, False, 1.0, ITEMS, "2026-06-06T01:00:00Z",
         source="soul")
    _ins(busc, "v-kairos", "data_001", True, False, 0.9, ITEMS, "2026-06-06T02:00:00Z",
         source="kairos-opus")
    creditc = _mk_credit()

    res = bus.from_fde_verdicts(busc, creditc, placeholder="?")

    # only the soul 一审 settled (kairos-opus 二审 skipped → no double-count)
    assert res["processed"] == 1
    assert _credit(creditc, "fde-capsule-data_001") == pytest.approx((1.0, 1))
    # watermark advances only past the settled (soul) row, not the skipped kairos row
    assert res["last_created_at"] == "2026-06-06T01:00:00Z"


def test_real_live_tag_fde_capsule_v5_settles():
    # production fde_verdicts tags the 一审 rows source='fde-capsule-v5' (verified
    # 2026-06-06), not 'soul' — the live loop must keep settling those.
    busc = _mk_bus()
    _ins(busc, "v-live", "data_001", True, False, 1.0, ITEMS, "2026-06-06T01:00:00Z",
         source="fde-capsule-v5")
    creditc = _mk_credit()
    res = bus.from_fde_verdicts(busc, creditc, placeholder="?")
    assert res["processed"] == 1
    assert _credit(creditc, "fde-capsule-data_001") == pytest.approx((1.0, 1))


def test_peek_also_filters_to_settling_sources():
    busc = _mk_bus()
    _ins(busc, "v-soul", "data_001", True, False, 1.0, ITEMS, "2026-06-06T01:00:00Z",
         source="soul")
    _ins(busc, "v-kairos", "data_001", True, False, 0.9, ITEMS, "2026-06-06T02:00:00Z",
         source="kairos-opus")
    rows = bus.peek_fde_verdicts(busc, placeholder="?")
    assert [r["task_uid"] for r in rows] == ["data_001"]
    assert len(rows) == 1  # kairos-opus not listed as a would-settle row


# ── RED 4 · items already a list (postgres JSONB) is accepted ────────────────
def test_items_as_list_accepted():
    # simulate psycopg2 returning JSONB as a python list (not a json str)
    busc = _mk_bus()
    busc.execute(
        "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, "
        "veto_failed, score, items, created_at) VALUES (?,?,?,?,?,?,?,?)",
        ("v-list", "data_003", "soul", 1, 0, 1.0, json.dumps(ITEMS),
         "2026-06-05T13:00:00Z"))
    busc.commit()
    creditc = _mk_credit()
    # monkeypatch row factory to hand items back as a list
    res = bus.from_fde_verdicts(busc, creditc, placeholder="?")
    assert res["processed"] == 1
    assert _credit(creditc, "fde-capsule-data_003") == pytest.approx((1.0, 1))
