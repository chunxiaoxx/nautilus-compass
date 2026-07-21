#!/usr/bin/env python3
"""TDD · paired raw-vs-guarded recall policy gate."""
from __future__ import annotations

import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from ops.recall_policy_gate import build_policy_gate  # noqa: E402


def _artifact(policy: str, d1: float, d2: float, d3: float = 0.0) -> dict:
    return {
        "meta": {
            "signal_policy": policy,
            "n_memories": 133,
            "n_impact": 2,
            "n_tier_nonworking": 1,
        },
        "result_summary": {
            "flat": {"mrr": 0.981, "delta_mrr_vs_flat": 0.0},
            "poi": {"mrr": 0.981 + d1, "delta_mrr_vs_flat": d1},
            "tier": {"mrr": 0.981 + d2, "delta_mrr_vs_flat": d2},
            "gemini": {"mrr": 0.981 + d3, "delta_mrr_vs_flat": d3},
        },
    }


def test_blocks_raw_lifecycle_promotion_when_raw_has_negative_delta():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=-0.001, d2=-0.0008),
        guarded=_artifact("guarded", d1=0.0, d2=0.0),
    )

    assert gate["gate"] == "block_raw_lifecycle_promotion"
    assert gate["promotion"]["raw_lifecycle_allowed"] is False
    assert gate["promotion"]["recommended_default"] == "guarded"
    assert gate["deltas"]["raw"]["poi"] == -0.001
    assert gate["deltas"]["guarded"]["tier"] == 0.0
    assert any("poi" in item["mode"] for item in gate["evidence"]["raw_negative_modes"])


def test_blocks_all_lifecycle_promotion_when_raw_and_guarded_are_negative():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=-0.001, d2=-0.0008),
        guarded=_artifact("guarded", d1=-0.001, d2=-0.0008),
    )

    assert gate["gate"] == "block_all_lifecycle_promotion"
    assert gate["promotion"]["raw_lifecycle_allowed"] is False
    assert gate["promotion"]["recommended_default"] == "flat"
    assert gate["evidence"]["guarded_negative_modes"]


def test_allows_raw_candidate_only_with_positive_supported_uplift():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=0.006, d2=0.007),
        guarded=_artifact("guarded", d1=0.0, d2=0.0),
    )

    assert gate["gate"] == "raw_lifecycle_candidate"
    assert gate["promotion"]["raw_lifecycle_allowed"] is True
    assert gate["promotion"]["recommended_default"] == "raw"


def test_keeps_default_neutral_when_no_policy_has_measurable_uplift():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=0.0, d2=0.0),
        guarded=_artifact("guarded", d1=0.0, d2=0.0),
    )

    assert gate["gate"] == "no_measurable_lifecycle_uplift"
    assert gate["promotion"]["raw_lifecycle_allowed"] is False
    assert gate["promotion"]["recommended_default"] == "guarded"


def test_recommends_routed_when_routed_has_positive_uplift_without_negative_delta():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=-0.001, d2=-0.001),
        guarded=_artifact("guarded", d1=-0.001, d2=-0.001),
        routed=_artifact("routed", d1=0.006, d2=0.006),
    )

    assert gate["gate"] == "routed_lifecycle_candidate"
    assert gate["promotion"]["recommended_default"] == "routed"
    assert gate["promotion"]["routed_lifecycle_allowed"] is True
    assert gate["deltas"]["routed"]["poi"] == 0.006


def test_does_not_recommend_routed_when_routed_is_negative():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=-0.001, d2=-0.001),
        guarded=_artifact("guarded", d1=-0.001, d2=-0.001),
        routed=_artifact("routed", d1=-0.001, d2=0.0),
    )

    assert gate["gate"] == "block_all_lifecycle_promotion"
    assert gate["promotion"]["recommended_default"] == "flat"
    assert gate["evidence"]["routed_negative_modes"]


def test_policy_gate_payload_is_json_serializable():
    gate = build_policy_gate(
        raw=_artifact("raw", d1=-0.001, d2=0.0),
        guarded=_artifact("guarded", d1=0.0, d2=0.0),
    )
    json.dumps(gate, ensure_ascii=False)
