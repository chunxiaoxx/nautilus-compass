"""T2 · dimension PoI → recall boost (close Layer2↔3 end-to-end).

Proves the FULL chain with REAL data_001: credit dimensions → central snapshot →
the SHIPPED boost chain (recall_pkg.poi_weighting.boost_top_k_with_snapshot) →
the most-validated dimension atom (calc-formula, 4 proven items) is re-ranked
AHEAD of a less-validated one (attachment-use, 1 item) when they tie on base
cosine. "最被验证维度优先浮现". NO LLM · pure arithmetic + real ingested atoms.

Reuses the vtf capsule pipeline (build_dimension_atoms / ingest_atoms) and the
real RUBRIC mapper — no new wheels. Skips if the vtf sibling repo is absent.
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
from proof.poi_credit_store import fetch_all_credits  # noqa: E402
from recall_pkg.poi_weighting import boost_top_k_with_snapshot  # noqa: E402

VTF = Path("C:/Users/chunx/Projects/vertical-task-factory")
NOW = "2026-06-06T09:00:00Z"


def _mk_db():
    conn = sqlite3.connect(":memory:")
    conn.execute("CREATE TABLE poi_credit (memory_key TEXT PRIMARY KEY, "
                 "cumulative_impact REAL NOT NULL DEFAULT 0, "
                 "event_count INTEGER NOT NULL DEFAULT 0, last_impact_at TEXT)")
    conn.commit()
    return conn


def _load_vtf():
    cap = VTF / "fde-toolbox"
    cl_p = VTF / "data_001_checklist.json"
    v_p = VTF / "_v5_data001_real_verdict_20260605.json"
    if not (cap.exists() and cl_p.exists() and v_p.exists()):
        pytest.skip("vtf sibling repo / data_001 fixtures not present")
    sys.path.insert(0, str(cap))
    try:
        from fde_knowledge_capsule import (
            build_dimension_atoms, ingest_atoms, map_to_rubric_dimension)
    except Exception:
        pytest.skip("fde_knowledge_capsule not importable")
    checklist = json.loads(cl_p.read_text(encoding="utf-8"))
    verdict = json.loads(v_p.read_text(encoding="utf-8"))
    return (checklist, verdict, build_dimension_atoms, ingest_atoms,
            map_to_rubric_dimension)


def test_most_validated_dimension_surfaces_first(tmp_path):
    checklist, verdict, build_atoms, ingest, mapper = _load_vtf()
    conn = _mk_db()

    # 1 · credit real data_001 dimensions into the central table (project must
    #     match the ingest namespace so the credit key == the boost key)
    adp.credit_dimensions_from_verdict(
        conn, "data_001", checklist, verdict, NOW, placeholder="?",
        dimension_for=mapper, project="fde-knowledge")
    snapshot = fetch_all_credits(conn)

    # 2 · ingest the real dimension atoms under <tmp>/fde-knowledge/memory/ so
    #     memory_key_from_path(atom) == the credited ledger key
    mem_dir = tmp_path / "fde-knowledge" / "memory"
    atoms = build_atoms("data_001", checklist, verdict)
    paths = ingest(atoms, str(mem_dir))  # {dimension: path}

    # sanity: calc-formula (4 proven items) outscores attachment-use (1 item)
    cf_key = adp.dimension_memory_key("calc-formula")
    au_key = adp.dimension_memory_key("attachment-use")
    assert snapshot[cf_key] > snapshot[au_key]

    # 3 · two dimension atoms TIED on base cosine → boost must break the tie
    #     toward the most-validated dimension
    base = 0.80
    entries = [
        (base, {"path": paths["attachment-use"], "dim": "attachment-use"}),
        (base, {"path": paths["calc-formula"], "dim": "calc-formula"}),
    ]
    boosted = boost_top_k_with_snapshot(entries, snapshot)

    # calc-formula now ranks first, attachment-use last
    assert boosted[0][1]["dim"] == "calc-formula"
    assert boosted[-1][1]["dim"] == "attachment-use"
    # boost math: calc-formula 4.0*0.1=+0.4 → ×1.4 ; attachment-use 1.0*0.1 → ×1.1
    assert boosted[0][0] == pytest.approx(base * 1.4, abs=1e-6)
    assert boosted[-1][0] == pytest.approx(base * 1.1, abs=1e-6)


def test_full_dimension_order_by_validation(tmp_path):
    """All 5 real data_001 dimensions, tied on base cosine → final order is
    monotonic in PoI credit (most-validated first)."""
    checklist, verdict, build_atoms, ingest, mapper = _load_vtf()
    conn = _mk_db()
    res = adp.credit_dimensions_from_verdict(
        conn, "data_001", checklist, verdict, NOW, placeholder="?",
        dimension_for=mapper, project="fde-knowledge")
    snapshot = fetch_all_credits(conn)
    mem_dir = tmp_path / "fde-knowledge" / "memory"
    paths = ingest(build_atoms("data_001", checklist, verdict), str(mem_dir))

    base = 0.75
    entries = [(base, {"path": paths[d], "dim": d}) for d in res["credited"]]
    boosted = boost_top_k_with_snapshot(entries, snapshot)

    ranked_credit = [res["credited"][e[1]["dim"]] for e in boosted]
    # boosted score is strictly increasing in credit (equal base) → order is
    # non-increasing in credit
    assert ranked_credit == sorted(ranked_credit, reverse=True)
    # calc-formula (highest credit) is first
    assert boosted[0][1]["dim"] == "calc-formula"
