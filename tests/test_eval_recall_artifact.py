#!/usr/bin/env python3
"""TDD for eval_recall artifact shape used by tuning scripts."""
from __future__ import annotations

import argparse
from pathlib import Path

from tests.eval_recall import build_recall_payload, build_recommendations


def _mk_args(mode="all"):
    return argparse.Namespace(mode=mode)


def _fake_result(mode, base_mrr=0.5, delta=0.0, failed_count=0):
    base_rank = [{"mode": mode, "n": 2, "P@1": 0.5, "P@3": 0.6, "P@5": 0.7, "MRR": base_mrr, "failed": []}]
    if delta:
        base_rank[0]["delta_vs_flat"] = {
            "P@1": delta,
            "P@3": delta,
            "P@5": delta,
            "MRR": delta,
        }
    base_rank[0]["failed"] = [
        (f"session_{i}", i + 1, "query...")
        for i in range(failed_count)
    ]
    return base_rank[0]


def test_build_recall_payload_shape_and_truncation():
    args = _mk_args("all")
    mems = [
        {"query": "q1"},
        {"query": "q2"},
        {"query": "q3"},
    ]
    results = [
        _fake_result("flat", base_mrr=0.42, delta=0.0, failed_count=2),
        _fake_result("poi", base_mrr=0.44, delta=0.02, failed_count=25),
    ]
    out_path = Path(".cache/test_eval_recall_payload.json")
    payload = build_recall_payload(args, mems, results, n_impact=1, n_nonworking=0, out_path=out_path,
                                   embedder="mock-embedder", command="python tests/eval_recall.py --mode all")

    assert payload["version"] == "1.0"
    assert payload["meta"]["payload_version"] == "1.0"
    assert payload["meta"]["n_memories"] == len(mems)
    assert payload["meta"]["n_tier_nonworking"] == 0
    assert payload["meta"]["embedder"] == "mock-embedder"
    assert payload["meta"]["out_file"] == str(out_path)
    assert payload["meta"]["command"] == "python tests/eval_recall.py --mode all"

    # artifact must be machine-consumable, and failed list should be capped
    assert len(payload["results"]) == 2
    assert payload["results"][1]["failed"][0]["name"] == "session_0"
    assert payload["results"][1]["failed"][-1]["name"] == "session_19"
    assert len(payload["results"][1]["failed"]) == 20

    assert payload["result_summary"]["flat"]["p1"] == 0.5
    assert payload["result_summary"]["poi"]["delta_mrr_vs_flat"] == 0.02

    rec_actions = {r["action"] for r in payload["recommendations"]}
    assert "bootstrap_tier_signals" in rec_actions


def test_build_recommendations_nodata_and_low_delta():
    mode_results = [
        {"mode": "flat", "MRR": 0.4, "delta_vs_flat": None},
        {"mode": "poi", "MRR": 0.401, "delta_vs_flat": {"MRR": 0.001}},
        {"mode": "tier", "MRR": 0.4015, "delta_vs_flat": {"MRR": 0.0015}},
    ]
    recs = build_recommendations(mode_results, n_memories=0, n_impact=0, n_nonworking=0)
    assert len(recs) == 1
    assert recs[0]["action"] == "seed_memory_corpus"
    assert recs[0]["priority"] == "critical"

    recs = build_recommendations(mode_results, n_memories=5, n_impact=0, n_nonworking=0)
    actions = {r["action"] for r in recs}
    assert "bootstrap_poi_signals" in actions
    assert "bootstrap_tier_signals" in actions
    assert "freeze_or_rewrite" in actions
