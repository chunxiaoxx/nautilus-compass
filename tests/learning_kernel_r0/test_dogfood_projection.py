from __future__ import annotations

import json
from pathlib import Path

from benchmarks.learning_kernel_r0.dogfood_projection import (
    build_projection,
    write_projection,
)
from benchmarks.poi_gate2.canonical import hash_json


ROOT = Path(__file__).parents[2]
SOURCE = ROOT / "docs" / "evidence" / "s4_live_agent_dogfood_candidates_v1.json"
COMMITTED = ROOT / "docs" / "evidence" / "learning_kernel_r0_dogfood_preflight_v1.json"


def test_unverified_dogfood_remains_visible_but_cannot_enter_learning() -> None:
    projection = build_projection(SOURCE)

    assert projection["candidate_count"] == 3
    assert len(projection["candidates"]) == 3
    assert projection["stage_a_admitted_count"] == 0
    assert {row["reason_code"] for row in projection["candidates"]} == {
        "blocked_missing_independent_verdict"
    }
    assert projection["synthesized_authority"] == {
        "reward": False,
        "impact": False,
        "capsule": False,
        "selector": False,
        "utility": False,
    }
    assert projection["development_recommendation"] == "flat"
    assert projection["runtime_recommendation"] == "flat"
    assert projection["improvement_claim"] is False
    supplied_hash = projection["projection_hash"]
    assert supplied_hash == hash_json(
        {key: value for key, value in projection.items() if key != "projection_hash"}
    )


def test_projection_is_rebuildable_and_write_is_idempotent(tmp_path) -> None:
    rebuilt = tmp_path / "projection.json"
    write_projection(SOURCE, rebuilt)
    first = rebuilt.read_bytes()
    write_projection(SOURCE, rebuilt)

    assert rebuilt.read_bytes() == first
    assert json.loads(first) == build_projection(SOURCE)
    assert first == COMMITTED.read_bytes()
