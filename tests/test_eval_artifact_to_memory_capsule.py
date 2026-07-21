#!/usr/bin/env python3
"""TDD for turning eval artifacts into memory capsules."""
from __future__ import annotations

import json
from pathlib import Path

from ops.eval_artifact_to_memory_capsule import (
    build_capsule,
    capsule_filename,
    write_capsule,
)


def _recall_artifact() -> dict:
    return {
        "generated_at": "2026-07-21T03:11:50Z",
        "meta": {
            "n_memories": 132,
            "n_impact": 1,
            "n_tier_nonworking": 0,
            "embedder": "BAAI/bge-m3",
        },
        "result_summary": {
            "flat": {"p1": 0.970, "p3": 0.992, "p5": 0.992, "mrr": 0.9804866850321395},
            "poi": {"delta_mrr_vs_flat": 0.0},
            "tier": {"delta_mrr_vs_flat": 0.0},
            "gemini": {"delta_mrr_vs_flat": 0.0},
        },
        "recommendations": [
            {
                "priority": "medium",
                "action": "bootstrap_tier_signals",
                "reason": "All memories are working tier.",
                "next_step": "Review tier promotion cadence.",
            }
        ],
    }


def _hint_artifact() -> dict:
    return {
        "risk": "medium",
        "next_actions": [
            {
                "priority": "medium",
                "action": "bootstrap_tier_signals",
                "reason": "All memories are working tier.",
                "next_step": "Review tier promotion cadence.",
            }
        ],
    }


def test_build_capsule_contains_lifecycle_frontmatter_and_benchmark_body():
    capsule = build_capsule(
        _recall_artifact(),
        _hint_artifact(),
        source_artifact=Path(".cache/eval_recall.json"),
        manifest={"suite": "smoke", "python_version": "Python 3.13.12"},
    )

    text = capsule.markdown
    assert text.startswith("---\n")
    assert "tier: semantic" in text
    assert "cumulative_impact: 1.0" in text
    assert "impact_event_count: 1" in text
    assert "ingested_via: eval_artifact_to_memory_capsule" in text
    assert "flat MRR: 0.9804866850321395" in text
    assert "bootstrap_tier_signals" in text
    assert "n_tier_nonworking: 0" in text


def test_capsule_filename_is_deterministic_for_same_source():
    source = Path(".cache/bench-profile-x/eval_recall.json")
    assert capsule_filename(source) == capsule_filename(source)
    assert capsule_filename(source).startswith("session_eval_capsule_")
    assert capsule_filename(source).endswith(".md")


def test_write_capsule_is_idempotent(tmp_path: Path):
    recall = _recall_artifact()
    hint = _hint_artifact()
    source = tmp_path / "eval_recall.json"
    source.write_text(json.dumps(recall), encoding="utf-8")

    capsule = build_capsule(recall, hint, source_artifact=source, manifest={})
    first = write_capsule(capsule, tmp_path / "memory")
    second = write_capsule(capsule, tmp_path / "memory")

    assert first == second
    assert first.exists()
    assert len(list((tmp_path / "memory").glob("session_eval_capsule_*.md"))) == 1
    assert "Route A benchmark smoke baseline" in first.read_text(encoding="utf-8")
