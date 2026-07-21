#!/usr/bin/env python3
"""TDD for tuning action extraction from eval_recall artifacts."""
from __future__ import annotations

import json
from pathlib import Path

from ops.eval_recall_tuning_hint import derive_next_actions


def test_critical_recommendation_creates_high_risk():
    artifact = {
        "meta": {"n_memories": 0, "n_impact": 0, "n_tier_nonworking": 0},
        "recommendations": [
            {
                "priority": "critical",
                "action": "seed_memory_corpus",
                "reason": "No memories loaded",
                "next_step": "Add memory",
            }
        ],
        "result_summary": {
            "flat": {"delta_mrr_vs_flat": 0.0},
        },
    }
    out = derive_next_actions(artifact)
    assert out["risk"] == "high"
    assert out["blocking_reason"] == "No memories loaded"
    assert out["next_actions"][0]["action"] == "seed_memory_corpus"


def test_low_risk_when_only_continue_recommendation(tmp_path):
    artifact = {
        "meta": {"n_memories": 5, "n_impact": 3, "n_tier_nonworking": 2},
        "recommendations": [
            {
                "priority": "low",
                "action": "continue",
                "reason": "Collect more runs",
                "next_step": "keep iterating",
            }
        ],
        "result_summary": {
            "flat": {"delta_mrr_vs_flat": 0.0},
        },
    }
    artifact_file = tmp_path / "artifact.json"
    artifact_file.write_text(json.dumps(artifact), encoding="utf-8")

    out = derive_next_actions(artifact)
    assert out["risk"] == "low"
    assert out["blocking_reason"] == ""
    assert out["next_actions"][0]["action"] == "continue"

    # also verify optional output persistence path accepts writes
    out_file = tmp_path / "hint.json"
    out_file.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")
    assert out_file.exists()
