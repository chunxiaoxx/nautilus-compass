"""Task A3 · reconcile glue settles task-level AND dimension-level in one pass.

`fde_verdict_reconcile.settle_once` runs the task-level spine
(BUS.from_fde_verdicts) and, when a checklist_dir is configured, the dimension
credit (BUS.credit_dimensions_from_bus joined to local checklists) over the SAME
`since` watermark — so one cron pass advances one watermark and both granularities
settle idempotently. A second pass with the advanced watermark double-credits
neither. NO LLM.
"""
from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_HERE))
from proof import fde_poi_adapter as adp  # noqa: E402


def _load():
    spec = importlib.util.spec_from_file_location(
        "fde_verdict_reconcile", _HERE / "ops" / "fde_verdict_reconcile.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute(
        "CREATE TABLE fde_verdicts (id INTEGER PRIMARY KEY, verdict_id TEXT UNIQUE, "
        "task_uid TEXT, source TEXT, checklist_uid TEXT, overall_pass INT, "
        "veto_failed INT, score REAL, items TEXT, artifacts TEXT, created_at TEXT)")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _ins(conn, vid, uid, op, vf, score, items, created_at):
    conn.execute("INSERT INTO fde_verdicts (verdict_id, task_uid, source, overall_pass, "
                 "veto_failed, score, items, created_at) VALUES (?,?,?,?,?,?,?,?)",
                 (vid, uid, "soul", int(op), int(vf), score, json.dumps(items), created_at))
    conn.commit()


def _credit(conn, mk):
    return conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                        "WHERE memory_key=?", (mk,)).fetchone()


def _checklist(cdir, uid, items):
    (cdir / f"{uid}_checklist.json").write_text(
        json.dumps({"task_uid": uid, "items": items}, ensure_ascii=False), encoding="utf-8")


def _stub_dim(item):
    return item.get("dimension", "coverage")


# ── RED 1 · one pass settles BOTH task capsule and dimension keys ────────────
def test_settle_once_credits_task_and_dimension(tmp_path):
    rec = _load()
    conn = _mk_db()
    _ins(conn, "v-1", "data_001", True, False, 0.9,
         [{"id": "c1", "pass": True}], "2026-06-05T02:47:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()
    _checklist(cdir, "data_001", [{"id": "c1", "dimension": "calc-formula"}])

    res = rec.settle_once(conn, None, str(cdir), placeholder="?", dimension_for=_stub_dim)

    assert res["last_created_at"] == "2026-06-05T02:47:00Z"
    assert _credit(conn, "fde-capsule-data_001") == pytest.approx((0.9, 1))   # task spine
    assert _credit(conn, adp.dimension_memory_key("calc-formula")) == pytest.approx((0.9, 1))


# ── RED 2 · second pass with the advanced watermark double-credits nothing ───
def test_settle_once_idempotent(tmp_path):
    rec = _load()
    conn = _mk_db()
    _ins(conn, "v-1", "data_001", True, False, 0.9,
         [{"id": "c1", "pass": True}], "2026-06-05T02:47:00Z")
    cdir = tmp_path / "cl"; cdir.mkdir()
    _checklist(cdir, "data_001", [{"id": "c1", "dimension": "calc-formula"}])

    first = rec.settle_once(conn, None, str(cdir), placeholder="?", dimension_for=_stub_dim)
    second = rec.settle_once(conn, first["last_created_at"], str(cdir),
                             placeholder="?", dimension_for=_stub_dim)

    assert second["task"]["processed"] == 0
    assert second["dimension"]["processed"] == 0
    # credits unchanged after the second pass
    assert _credit(conn, "fde-capsule-data_001") == pytest.approx((0.9, 1))
    assert _credit(conn, adp.dimension_memory_key("calc-formula")) == pytest.approx((0.9, 1))


# ── RED 3 · no checklist_dir → task-level still settles, dimension skipped ────
def test_settle_once_without_checklist_dir_still_does_task_level():
    rec = _load()
    conn = _mk_db()
    _ins(conn, "v-1", "data_001", True, False, 0.9,
         [{"id": "c1", "pass": True}], "2026-06-05T02:47:00Z")

    res = rec.settle_once(conn, None, None, placeholder="?", dimension_for=_stub_dim)

    assert _credit(conn, "fde-capsule-data_001") == pytest.approx((0.9, 1))
    assert res["dimension"]["processed"] == 0
