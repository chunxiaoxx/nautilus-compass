"""T1 · dimension-level PoI credit (Layer2↔3 tie).

`credit_dimensions_from_verdict` decomposes a soul checklist_scorer verdict into
per-RUBRIC-dimension PoI credits on `fde-dim-<dimension>` keys: a PASSED item
credits its mapped dimension (+score), a FAILED item credits 0 (only the
avoid-pitfall capsule is retained — no "fail also adds score"). This closes the
recursive flywheel at dimension granularity so the most-validated dimension
accrues the most PoI and surfaces first in recall. NO LLM.

The item→dimension mapper is injected (`dimension_for`) to keep compass decoupled
from the vtf capsule module; production wires in
`fde_knowledge_capsule.map_to_rubric_dimension`. design §3.
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


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _credit(conn, mk):
    row = conn.execute("SELECT cumulative_impact, event_count FROM poi_credit "
                       "WHERE memory_key=?", (mk,)).fetchone()
    return row  # None if absent


def _dim_credit(conn, dim, project="fde-knowledge"):
    """Look up a dimension's credit by its production ledger key
    (<project>/fde-dim-<dim>.md) — the key the boost actually hits."""
    return _credit(conn, adp.dimension_memory_key(dim, project))


# stub mapper: dimension lives directly on the checklist item ('dim' field)
def _stub_dim(item):
    return item.get("dim", "coverage")


NOW = "2026-06-06T09:00:00Z"


def _checklist(items):
    return {"task_uid": "t", "items": items}


def _verdict(score, items, **extra):
    base = {"score": score, "passed": sum(1 for i in items if i["pass"]),
            "total": len(items), "veto_failed": False, "overall_pass": True,
            "items": items}
    base.update(extra)
    return base


# ── RED 1 · passed items credit their mapped dimensions ──────────────────────
def test_passed_items_credit_their_dimensions():
    conn = _mk_db()
    checklist = _checklist([
        {"id": "c1", "dim": "hallucination-control", "point": "privacy"},
        {"id": "c2", "dim": "calc-formula", "point": "model"},
    ])
    verdict = _verdict(1.0, [
        {"id": "c1", "pass": True, "veto": True, "reason": "ok"},
        {"id": "c2", "pass": True, "veto": False, "reason": "ok"},
    ])
    res = adp.credit_dimensions_from_verdict(
        conn, "data_001", checklist, verdict, NOW, placeholder="?",
        dimension_for=_stub_dim)

    assert res["memory_keys"]["hallucination-control"] == \
        "fde-knowledge/fde-dim-hallucination-control.md"
    assert _dim_credit(conn, "hallucination-control") == pytest.approx((1.0, 1))
    assert _dim_credit(conn, "calc-formula") == pytest.approx((1.0, 1))
    assert res["pass_score"] == pytest.approx(1.0)


# ── RED 2 · a failed item credits 0 (keeps only the avoid-pitfall capsule) ───
def test_failed_item_zero_credit():
    conn = _mk_db()
    checklist = _checklist([
        {"id": "c1", "dim": "citation", "point": "cite"},
        {"id": "c2", "dim": "coverage", "point": "cover"},
    ])
    verdict = _verdict(0.5, [
        {"id": "c1", "pass": False, "veto": False, "reason": "missing cite"},
        {"id": "c2", "pass": True, "veto": False, "reason": "ok"},
    ])
    res = adp.credit_dimensions_from_verdict(
        conn, "data_x", checklist, verdict, NOW, placeholder="?",
        dimension_for=_stub_dim)

    # failed dimension never written
    assert _dim_credit(conn, "citation") is None
    assert "citation" not in res["credited"]
    assert "c1" in res["skipped_fail"]
    # passed dimension credited with the verdict score
    assert _dim_credit(conn, "coverage") == pytest.approx((0.5, 1))


# ── RED 3 · two passed items on same dimension accumulate ────────────────────
def test_same_dimension_accumulates_within_task():
    conn = _mk_db()
    checklist = _checklist([
        {"id": "c1", "dim": "calc-formula", "point": "a"},
        {"id": "c2", "dim": "calc-formula", "point": "b"},
        {"id": "c3", "dim": "calc-formula", "point": "c"},
    ])
    verdict = _verdict(1.0, [
        {"id": "c1", "pass": True, "veto": False, "reason": "ok"},
        {"id": "c2", "pass": True, "veto": False, "reason": "ok"},
        {"id": "c3", "pass": True, "veto": False, "reason": "ok"},
    ])
    adp.credit_dimensions_from_verdict(
        conn, "data_y", checklist, verdict, NOW, placeholder="?",
        dimension_for=_stub_dim)
    # 3 passed items on calc-formula → cumulative 3.0, event_count 3
    assert _dim_credit(conn, "calc-formula") == pytest.approx((3.0, 3))


# ── RED 4 · verdict item with no matching checklist item is skipped ──────────
def test_unmatched_verdict_item_skipped():
    conn = _mk_db()
    checklist = _checklist([{"id": "c1", "dim": "coverage", "point": "a"}])
    verdict = _verdict(1.0, [
        {"id": "c1", "pass": True, "veto": False, "reason": "ok"},
        {"id": "c99", "pass": True, "veto": False, "reason": "orphan"},
    ])
    res = adp.credit_dimensions_from_verdict(
        conn, "data_z", checklist, verdict, NOW, placeholder="?",
        dimension_for=_stub_dim)
    assert "c99" in res["skipped_unmatched"]
    assert _dim_credit(conn, "coverage") == pytest.approx((1.0, 1))


# ── RED 5 · default mapper sends unmapped/task-specific → uncategorized ───────
def test_default_mapper_uncategorized_for_task_specific():
    conn = _mk_db()
    checklist = _checklist([{"id": "c1", "dimension": "task-specific", "point": "x"}])
    verdict = _verdict(1.0, [{"id": "c1", "pass": True, "veto": False, "reason": "ok"}])
    # no dimension_for injected → degraded default
    adp.credit_dimensions_from_verdict(
        conn, "data_d", checklist, verdict, NOW, placeholder="?")
    assert _dim_credit(conn, "uncategorized") == pytest.approx((1.0, 1))


# ── RED 6 · cross-task accumulation on the same dimension key (compounding) ──
def test_cross_task_accumulation():
    conn = _mk_db()
    cl = _checklist([{"id": "c1", "dim": "hallucination-control", "point": "privacy"}])
    v = _verdict(1.0, [{"id": "c1", "pass": True, "veto": True, "reason": "ok"}])
    adp.credit_dimensions_from_verdict(conn, "data_001", cl, v, NOW,
                                       placeholder="?", dimension_for=_stub_dim)
    adp.credit_dimensions_from_verdict(conn, "data_002", cl, v, NOW,
                                       placeholder="?", dimension_for=_stub_dim)
    # same dimension key accrues evidence across two tasks
    assert _dim_credit(conn, "hallucination-control") == pytest.approx((2.0, 2))


# ── RED 7 · integration with REAL data_001 verdict + real RUBRIC mapper ──────
VTF = Path("C:/Users/chunx/Projects/vertical-task-factory")


def _load_real():
    cl_p = VTF / "data_001_checklist.json"
    v_p = VTF / "_v5_data001_real_verdict_20260605.json"
    cap = VTF / "fde-toolbox"
    if not (cl_p.exists() and v_p.exists() and cap.exists()):
        pytest.skip("vtf sibling repo / data_001 fixtures not present")
    sys.path.insert(0, str(cap))
    try:
        from fde_knowledge_capsule import map_to_rubric_dimension
    except Exception:
        pytest.skip("fde_knowledge_capsule not importable")
    checklist = json.loads(cl_p.read_text(encoding="utf-8"))
    verdict = json.loads(v_p.read_text(encoding="utf-8"))
    return checklist, verdict, map_to_rubric_dimension


def test_real_data001_all_passed_credit_real_dimensions():
    conn = _mk_db()
    checklist, verdict, mapper = _load_real()
    res = adp.credit_dimensions_from_verdict(
        conn, "data_001", checklist, verdict, NOW, placeholder="?",
        dimension_for=mapper)

    # data_001 is 11/11 pass → every scored item credits exactly one dimension
    total_events = sum(r[1] for r in
                       [_credit(conn, k) for k in res["memory_keys"].values()])
    assert total_events == 11
    # task-specific must have been mapped to real §10 dims, never uncategorized
    assert _dim_credit(conn, "uncategorized") is None
    # at least the privacy dimension surfaced (c1/c5 → hallucination-control)
    assert _dim_credit(conn, "hallucination-control") is not None
    # every credited key is a project-qualified fde-dim-*.md ledger key (boost-compatible)
    assert all("/fde-dim-" in k and k.endswith(".md")
               for k in res["memory_keys"].values())
