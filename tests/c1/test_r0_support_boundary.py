from __future__ import annotations

import ast
import math
from pathlib import Path

import pytest

from benchmarks.common_statistics import percentile_95
from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json
from benchmarks.poi_gate2.dogfood_evidence import (
    DogfoodPacketBundle,
    DogfoodPacketCandidate,
    evaluate_dogfood_bundle,
)
from gep.experience_packet import ExperiencePacket


HASH_1 = "sha256:" + "1" * 64
HASH_2 = "sha256:" + "2" * 64


def test_canonical_hash_is_order_independent_and_rejects_non_finite_values() -> None:
    assert canonical_json_bytes({"b": 2, "a": 1}) == b'{"a":1,"b":2}'
    assert hash_json({"b": 2, "a": 1}) == hash_json({"a": 1, "b": 2})
    with pytest.raises(ValueError, match="non-finite"):
        canonical_json_bytes({"score": math.nan})


def test_common_percentile_has_no_action_projection_dependency() -> None:
    assert percentile_95((0.0, 0.25, 0.5, 1.0)) == 1.0
    with pytest.raises(ValueError, match="at least one"):
        percentile_95(())


def test_dogfood_projection_remains_blocked_without_independent_verdict() -> None:
    packet = ExperiencePacket(
        episode_id="c1.portability_repair",
        task="Repair candidate portability.",
        action_kind="canonical_fixture_rebuild",
        tool_chain=("git", "pytest"),
        outcome="success_after_repair",
        failure_mode="line_ending_drift",
        route_key="compass/c1/portability",
        capsule_candidate=False,
        policy_hint="pin_line_endings_before_hashing",
    )
    candidate = DogfoodPacketCandidate.from_args(
        packet=packet,
        plan_commit="a" * 40,
        plan_hash=HASH_1,
        source_evidence_hashes=(HASH_2,),
        verification_state="repair_resolved",
    )
    report = evaluate_dogfood_bundle(
        DogfoodPacketBundle.from_args(candidates=(candidate,))
    )

    assert report["stage_a_input_count"] == 0
    assert report["runtime_recommendation"] == "flat"
    assert report["improvement_claim"] is False


def test_poi_support_surface_excludes_live_and_business_modules() -> None:
    root = Path(__file__).resolve().parents[2] / "benchmarks" / "poi_gate2"
    assert {path.name for path in root.glob("*.py")} == {
        "__init__.py",
        "canonical.py",
        "dogfood_evidence.py",
    }
    forbidden_prefixes = (
        "benchmarks.poi_gate2.live_agent",
        "benchmarks.poi_gate2.provider",
        "benchmarks.poi_gate2.repair",
        "benchmarks.poi_gate2.action_projection",
        "nautilus_platform",
        "nautilus_v5",
        "fde",
    )
    imported_modules: set[str] = set()
    for path in root.glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
    assert all(
        not module.startswith(prefix)
        for module in imported_modules
        for prefix in forbidden_prefixes
    )
