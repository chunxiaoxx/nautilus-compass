"""T3 · batch dimension flywheel pipeline (multi-task accumulation + compounding).

`batch_ingest_and_credit` runs the dimension capsule flywheel over a batch of
(task_id, checklist, verdict) tasks: per task it credits per-dimension PoI and
(optionally, via injected vtf capsule callables) ingests dimension atoms
accumulatively. The SAME dimension key accrues PoI credit (central table) AND
evidence (atom file) ACROSS tasks → cross-domain compounding: the more tasks, the
richer that dimension's recall. data_002 just landed, so this is verified on REAL
data_001 + data_002, not a dry pipeline. NO LLM.
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
from proof import fde_batch_ingest as batch  # noqa: E402

VTF = Path("C:/Users/chunx/Projects/vertical-task-factory")
NOW = "2026-06-06T09:00:00Z"


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _stub_dim(item):
    return item.get("dim", "coverage")


def _cl(items):
    return {"items": items}


def _v(score, items):
    return {"score": score, "passed": sum(1 for i in items if i["pass"]),
            "total": len(items), "veto_failed": False, "overall_pass": True,
            "items": items}


def _ev(conn, dim):
    row = conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                       "WHERE memory_key=?", (adp.dimension_memory_key(dim),)).fetchone()
    return row


# ── RED 1 · PoI-only batch: same dimension accumulates across tasks ──────────
def test_batch_poi_accumulates_across_tasks():
    conn = _mk_db()
    tasks = [
        {"task_id": "data_001",
         "checklist": _cl([{"id": "c1", "dim": "coverage"},
                           {"id": "c2", "dim": "citation"}]),
         "verdict": _v(1.0, [{"id": "c1", "pass": True}, {"id": "c2", "pass": True}])},
        {"task_id": "data_002",
         "checklist": _cl([{"id": "c1", "dim": "coverage"},
                           {"id": "c2", "dim": "calc-formula"}]),
         "verdict": _v(0.5, [{"id": "c1", "pass": True}, {"id": "c2", "pass": False}])},
    ]
    res = batch.batch_ingest_and_credit(conn, tasks, NOW, placeholder="?",
                                        dimension_for=_stub_dim)
    # coverage credited by both tasks → cumulative 1.0+0.5, 2 events
    assert _ev(conn, "coverage") == pytest.approx((1.5, 2))
    # citation only task1, calc-formula failed in task2 (no credit)
    assert _ev(conn, "citation") == pytest.approx((1.0, 1))
    assert _ev(conn, "calc-formula") is None
    assert res["dimension_events"]["coverage"] == 2
    assert len(res["per_task"]) == 2


# ── RED 2 · real data_001 + data_002 · cross-task PoI + atom compounding ─────
def _load_vtf():
    cap = VTF / "fde-toolbox"
    files = {n: VTF / n for n in (
        "data_001_checklist.json", "_v5_data001_real_verdict_20260605.json",
        "data_002_checklist.json", "_v5_data002_real_verdict_20260605.json")}
    if not cap.exists() or not all(p.exists() for p in files.values()):
        pytest.skip("vtf sibling repo / data_001+002 fixtures not present")
    sys.path.insert(0, str(cap))
    try:
        from fde_knowledge_capsule import (
            build_dimension_atoms, ingest_atoms, map_to_rubric_dimension)
    except Exception:
        pytest.skip("fde_knowledge_capsule not importable")
    load = lambda p: json.loads(files[p].read_text(encoding="utf-8"))
    return (load, build_dimension_atoms, ingest_atoms, map_to_rubric_dimension)


def test_real_two_task_compounding(tmp_path):
    load, build_atoms, ingest_atoms, mapper = _load_vtf()
    conn = _mk_db()
    mem_dir = tmp_path / "fde-knowledge" / "memory"
    tasks = [
        {"task_id": "data_001",
         "checklist": load("data_001_checklist.json"),
         "verdict": load("_v5_data001_real_verdict_20260605.json")},
        {"task_id": "data_002",
         "checklist": load("data_002_checklist.json"),
         "verdict": load("_v5_data002_real_verdict_20260605.json")},
    ]
    res = batch.batch_ingest_and_credit(
        conn, tasks, NOW, placeholder="?", dimension_for=mapper,
        build_atoms=build_atoms, ingest_atoms=ingest_atoms,
        mem_dir=str(mem_dir), project="fde-knowledge")

    # at least one dimension is validated by BOTH real tasks (cross-domain reuse)
    d1 = set(res["per_task"][0]["credited"])
    d2 = set(res["per_task"][1]["credited"])
    shared = d1 & d2
    assert shared, "expected ≥1 dimension proven by both data_001 and data_002"

    sd = sorted(shared)[0]
    # PoI: the shared dimension's events == passed-count in task1 + task2
    row = _ev(conn, sd)
    expect_events = (res["per_task"][0]["events"][sd]
                     + res["per_task"][1]["events"][sd])
    assert row[1] == expect_events

    # COMPOUNDING: the shared dimension's atom file carries evidence from BOTH
    # source tasks → the next task's copilot recalls a richer atom
    atom = Path(res["atom_paths"][sd])
    body = atom.read_text(encoding="utf-8")
    assert "<!--ev:data_001|" in body
    assert "<!--ev:data_002|" in body

    # data_002's failed items (c4, c5) credited nothing
    assert res["per_task"][1]["skipped_fail"]
