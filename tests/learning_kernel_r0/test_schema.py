from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from benchmarks.learning_kernel_r0.schema import (
    INTERVENTIONS,
    SELECTORS,
    LearningKernelManifest,
    LearningRunResult,
    MemoryView,
    manifest_from_mapping,
    memory_view_from_mapping,
    run_result_from_mapping,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def manifest_mapping() -> dict[str, object]:
    return {
        "schema_version": "compass.learning_kernel.manifest.v1",
        "manifest_id": "lkr0_manifest_baseline",
        "selector": "flat",
        "intervention": "no_memory",
        "task_hashes": [HASH_A],
        "experience_hashes": [HASH_B],
        "protected_query_classes": ["protected_no_context"],
        "runtime_recommendation": "flat",
        "improvement_claim": False,
    }


def memory_view_mapping() -> dict[str, object]:
    return {
        "view_id": "lkr0_view_repair",
        "source_packet_hash": HASH_A,
        "route_key": "compass/s4/provider_boundary",
        "query_class": "project_recall",
        "action_kind": "provider_boundary_repair",
        "representation": "distilled",
        "rendered_text": "Map the selected credential to the declared provider field.",
        "semantic_score": 0.75,
        "verification_state": "independent_verified",
        "verdict": "success",
        "lifecycle_state": "active",
        "expires_at": None,
    }


def run_result_mapping() -> dict[str, object]:
    return {
        "run_id": "lkr0_run_baseline",
        "task_id": "lkr0_task_repair",
        "task_hash": HASH_A,
        "query_class": "project_recall",
        "selector": "governed",
        "intervention": "distilled",
        "replica": 0,
        "selected_view_ids": ["lkr0_view_repair"],
        "success": True,
        "first_pass_success": True,
        "verifier_code": "verified_pass",
        "latency_ms": 17,
        "input_tokens": 100,
        "output_tokens": 20,
        "estimated_cost_usd": 0.002,
        "result_hash": HASH_C,
    }


def test_manifest_accepts_all_frozen_selectors_and_interventions() -> None:
    for selector in SELECTORS:
        for intervention in INTERVENTIONS:
            raw = manifest_mapping()
            raw["selector"] = selector
            raw["intervention"] = intervention
            manifest = manifest_from_mapping(raw)
            assert manifest.selector == selector
            assert manifest.intervention == intervention


def test_manifest_rejects_unknown_selector() -> None:
    raw = manifest_mapping()
    raw["selector"] = "magic_memory"
    with pytest.raises(ValueError, match="selector is unsupported"):
        manifest_from_mapping(raw)


def test_manifest_requires_flat_runtime_and_false_claim() -> None:
    promoted = manifest_mapping()
    promoted["runtime_recommendation"] = "promote"
    with pytest.raises(ValueError, match="runtime_recommendation must be flat"):
        manifest_from_mapping(promoted)

    claimed = manifest_mapping()
    claimed["improvement_claim"] = True
    with pytest.raises(ValueError, match="improvement_claim must be false"):
        manifest_from_mapping(claimed)


def test_memory_view_requires_prefixed_source_packet_hash() -> None:
    raw = memory_view_mapping()
    raw["source_packet_hash"] = "a" * 64
    with pytest.raises(ValueError, match="source_packet_hash must be sha256"):
        memory_view_from_mapping(raw)


def test_memory_view_rejects_nonfinite_score_and_unsafe_rendered_text() -> None:
    nonfinite = memory_view_mapping()
    nonfinite["semantic_score"] = float("nan")
    with pytest.raises(ValueError, match="semantic_score must be finite"):
        memory_view_from_mapping(nonfinite)

    credential = memory_view_mapping()
    credential["rendered_text"] = "api_key=sk-do-not-store"
    with pytest.raises(ValueError, match="rendered_text contains unsafe"):
        memory_view_from_mapping(credential)


def test_run_result_requires_mechanical_verdict_code() -> None:
    raw = run_result_mapping()
    raw["verifier_code"] = ""
    with pytest.raises(ValueError, match="verifier_code must be a safe token"):
        run_result_from_mapping(raw)


@pytest.mark.parametrize("field", ["latency_ms", "input_tokens", "output_tokens"])
def test_run_result_rejects_boolean_integer_fields(field: str) -> None:
    raw = run_result_mapping()
    raw[field] = True
    with pytest.raises(TypeError, match=field):
        run_result_from_mapping(raw)


def test_run_result_requires_task_hash_and_nonnegative_replica() -> None:
    bare_hash = run_result_mapping()
    bare_hash["task_hash"] = "a" * 64
    with pytest.raises(ValueError, match="task_hash must be sha256"):
        run_result_from_mapping(bare_hash)

    boolean_replica = run_result_mapping()
    boolean_replica["replica"] = True
    with pytest.raises(TypeError, match="replica"):
        run_result_from_mapping(boolean_replica)

    negative_replica = run_result_mapping()
    negative_replica["replica"] = -1
    with pytest.raises(ValueError, match="replica"):
        run_result_from_mapping(negative_replica)


def test_unknown_keys_fail_closed() -> None:
    for parser, raw in (
        (manifest_from_mapping, manifest_mapping()),
        (memory_view_from_mapping, memory_view_mapping()),
        (run_result_from_mapping, run_result_mapping()),
    ):
        raw["raw_dialogue"] = "must not cross the boundary"
        with pytest.raises(TypeError, match="unknown"):
            parser(raw)


def test_contracts_are_immutable_and_normalize_sequences() -> None:
    manifest = manifest_from_mapping(manifest_mapping())
    view = memory_view_from_mapping(memory_view_mapping())
    result = run_result_from_mapping(run_result_mapping())

    assert isinstance(manifest, LearningKernelManifest)
    assert isinstance(view, MemoryView)
    assert isinstance(result, LearningRunResult)
    assert manifest.task_hashes == (HASH_A,)
    assert manifest.experience_hashes == (HASH_B,)
    assert result.selected_view_ids == ("lkr0_view_repair",)

    with pytest.raises(FrozenInstanceError):
        manifest.selector = "semantic"  # type: ignore[misc]
