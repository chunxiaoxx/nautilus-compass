#!/usr/bin/env python3
"""TDD · convert verified development outcomes into memory capsules."""
from __future__ import annotations

import json
from pathlib import Path

from ops.dev_outcome_to_memory_capsules import (
    build_capsules,
    signal_support_from_capsules,
    write_capsules,
)


def _outcomes() -> list[dict]:
    return [
        {
            "id": "c2",
            "title": "paired recall policy gate",
            "commit": "666c0cb",
            "kind": "benchmark_gate",
            "impact": 1.0,
            "tier": "semantic",
            "evidence": [
                "python -m pytest tests/test_recall_policy_gate.py -q",
                ".cache/bench-profile-20260721-035112-(default in daemon.py)/recall_policy_gate.json",
            ],
            "result": "raw lifecycle promotion blocked when raw delta is negative",
        },
        {
            "id": "c3",
            "title": "guarded lifecycle recall default",
            "commit": "9632954",
            "kind": "runtime_default",
            "impact": 1.0,
            "tier": "semantic",
            "evidence": [
                "python -m pytest tests/test_lifecycle_policy.py tests/test_recall_policy_preflight.py -q",
                ".cache/bench-profile-20260721-040249-(default in daemon.py)/summary.json",
            ],
            "result": "runtime default moved to guarded and preflight accepts guarded",
        },
        {
            "id": "c4",
            "title": "release recall policy preflight",
            "commit": "a523020",
            "kind": "release_gate",
            "impact": 1.0,
            "tier": "semantic",
            "evidence": [
                "python -m pytest tests/test_release_recall_policy_gate_contract.py -q",
                "docs/evidence/recall_policy_gate_current.json",
            ],
            "result": "release workflow consumes current policy gate evidence",
        },
    ]


def test_build_capsules_emit_lifecycle_frontmatter_and_evidence():
    capsules = build_capsules(_outcomes(), generated_at="2026-07-21T08:20:00Z")

    assert len(capsules) == 3
    text = capsules[0].markdown
    assert text.startswith("---\n")
    assert "type: execution_outcome" in text
    assert "ingested_via: dev_outcome_to_memory_capsules" in text
    assert "tier: semantic" in text
    assert "cumulative_impact: 1.0" in text
    assert "impact_event_count: 1" in text
    assert "commit: 666c0cb" in text
    assert "paired recall policy gate" in text
    assert "raw lifecycle promotion blocked" in text


def test_signal_support_from_capsules_meets_guarded_min_count():
    support = signal_support_from_capsules(build_capsules(_outcomes()))
    assert support == {
        "n_capsules": 3,
        "n_impact": 3,
        "n_tier_nonworking": 3,
        "meets_min_signal_count": True,
    }


def test_write_capsules_is_idempotent(tmp_path: Path):
    capsules = build_capsules(_outcomes(), generated_at="2026-07-21T08:20:00Z")
    first = write_capsules(capsules, tmp_path)
    second = write_capsules(capsules, tmp_path)

    assert first == second
    assert len(list(tmp_path.glob("session_dev_outcome_*.md"))) == 3
    assert json.loads((tmp_path / "_dev_outcome_capsules_manifest.json").read_text(encoding="utf-8"))[
        "written"
    ] == [str(p) for p in first]
