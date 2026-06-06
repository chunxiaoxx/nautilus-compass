"""Task A2 · dimension-level PoI auto-driven from the verdict-bus (Option C).

The bus row carries the verdict items (id + pass) but NOT the checklist content
(only checklist_uid) — so dimension granularity needs the checklist. Option C
joins each bus verdict to its LOCAL `<task_uid>_checklist.json` by task_uid and
runs the existing credit_dimensions_from_verdict. No cross-framework change: both
halves (bus verdict + local checklist) already live in compass. NO LLM.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
from proof import fde_poi_adapter as adp  # noqa: E402
from proof import fde_verdict_bus_reader as bus  # noqa: E402


def _mk_bus():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE fde_verdicts (id INTEGER PRIMARY KEY, "
        "verdict_id TEXT UNIQUE NOT NULL, task_uid TEXT NOT NULL, source TEXT NOT NULL, "
        "checklist_uid TEXT, overall_pass INTEGER NOT NULL, veto_failed INTEGER NOT NULL, "
        "score REAL NOT NULL, items TEXT NOT NULL DEFAULT '[]', artifacts TEXT, "
        "created_at TEXT NOT NULL)")
    conn.commit()
    return conn


def _ins(conn, verdict_id, task_uid, overall_pass, veto_failed, score, items, created_at):
    conn.execute(
        "INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, "
        "veto_failed, score, items, created_at) VALUES (?,?,?,?,?,?,?,?)",
        (verdict_id, task_uid, "soul", int(overall_pass), int(veto_failed), score,
         json.dumps(items), created_at))
    conn.commit()


def _mk_credit():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _dim(conn, dim):
    return conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                        "WHERE memory_key=?", (adp.dimension_memory_key(dim),)).fetchone()


def _write_checklist(cdir: Path, task_uid: str, items: list):
    (cdir / f"{task_uid}_checklist.json").write_text(
        json.dumps({"task_uid": task_uid, "items": items}, ensure_ascii=False),
        encoding="utf-8")


def _stub_dim(item):
    return item.get("dimension", "coverage")


# ── RED 1 · bus verdict joined to local checklist → dimension PoI ────────────
def test_credits_dimensions_from_bus_joined_to_local_checklist(tmp_path):
    busc = _mk_bus()
    _ins(busc, "v-1", "data_001", True, False, 0.9,
         [{"id": "c1", "pass": True}, {"id": "c2", "pass": True}],
         "2026-06-05T02:47:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()
    _write_checklist(cdir, "data_001", [
        {"id": "c1", "point": "公式测算", "dimension": "calc-formula"},
        {"id": "c2", "point": "用附件", "dimension": "attachment-use"}])
    creditc = _mk_credit()

    res = bus.credit_dimensions_from_bus(
        busc, creditc, str(cdir), placeholder="?", dimension_for=_stub_dim)

    assert res["processed"] == 1
    assert _dim(creditc, "calc-formula") == pytest.approx((0.9, 1))
    assert _dim(creditc, "attachment-use") == pytest.approx((0.9, 1))
    assert res["last_created_at"] == "2026-06-05T02:47:00Z"


# ── RED 2 · a verdict with no local checklist is skipped (recorded) ──────────
def test_skips_task_without_local_checklist(tmp_path):
    busc = _mk_bus()
    _ins(busc, "v-9", "data_099", True, False, 1.0,
         [{"id": "c1", "pass": True}], "2026-06-05T03:00:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()  # no data_099_checklist.json
    creditc = _mk_credit()

    res = bus.credit_dimensions_from_bus(
        busc, creditc, str(cdir), placeholder="?", dimension_for=_stub_dim)

    assert res["processed"] == 1
    assert res["skipped_no_checklist"] == ["data_099"]
    assert _dim(creditc, "coverage") is None  # nothing credited
    # watermark still advances so a missing checklist does not stall the stream
    assert res["last_created_at"] == "2026-06-05T03:00:00Z"


# ── RED 3 · failed item credits 0 (only the passed dimension accrues) ────────
def test_failed_item_credits_zero(tmp_path):
    busc = _mk_bus()
    _ins(busc, "v-2", "data_002", False, False, 0.8,
         [{"id": "c1", "pass": True}, {"id": "c4", "pass": False}],
         "2026-06-05T11:22:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()
    _write_checklist(cdir, "data_002", [
        {"id": "c1", "point": "公式", "dimension": "calc-formula"},
        {"id": "c4", "point": "隐私", "dimension": "hallucination-control"}])
    creditc = _mk_credit()

    res = bus.credit_dimensions_from_bus(
        busc, creditc, str(cdir), placeholder="?", dimension_for=_stub_dim)

    assert res["processed"] == 1
    assert _dim(creditc, "calc-formula") == pytest.approx((0.8, 1))
    assert _dim(creditc, "hallucination-control") is None  # failed → 0


# ── RED 4 · since watermark filters already-settled verdicts ─────────────────
def test_since_watermark_filters(tmp_path):
    busc = _mk_bus()
    _ins(busc, "v-1", "data_001", True, False, 0.9,
         [{"id": "c1", "pass": True}], "2026-06-05T02:47:00Z")
    _ins(busc, "v-2", "data_002", True, False, 0.8,
         [{"id": "c1", "pass": True}], "2026-06-05T11:22:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()
    _write_checklist(cdir, "data_001", [{"id": "c1", "dimension": "calc-formula"}])
    _write_checklist(cdir, "data_002", [{"id": "c1", "dimension": "coverage"}])
    creditc = _mk_credit()

    res = bus.credit_dimensions_from_bus(
        busc, creditc, str(cdir), since="2026-06-05T02:47:00Z",
        placeholder="?", dimension_for=_stub_dim)

    assert res["processed"] == 1
    assert _dim(creditc, "calc-formula") is None  # data_001 already settled
    assert _dim(creditc, "coverage") is not None
