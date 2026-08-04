from __future__ import annotations

import math

import pytest

from benchmarks.learning_kernel_r0.policy import CandidateDecision, evaluate_candidate_policy


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def _evaluate(**overrides) -> CandidateDecision:
    values = {
        "aggregate_delta": 0.10,
        "permutation_p95": 0.05,
        "candidate_selector": "governed",
        "protected_deltas": {"protected": 0.0},
        "protected_query_classes": ("protected",),
        "required_query_classes": ("ordinary", "protected"),
        "observed_query_classes": ("ordinary", "protected"),
        "admitted_poisoned_view_ids": (),
        "expected_replay_hash": HASH_A,
        "actual_replay_hash": HASH_A,
    }
    values.update(overrides)
    return evaluate_candidate_policy(**values)


def test_positive_delta_below_permutation_p95_stays_flat() -> None:
    decision = _evaluate(aggregate_delta=0.04)

    assert decision.candidate_state == "flat"
    assert decision.reason_code == "delta_not_above_permutation_p95"
    assert decision.failed_metric == "aggregate_delta"
    assert decision.observed_value == 0.04
    assert decision.threshold_value == 0.05


def test_any_protected_regression_blocks_candidate() -> None:
    decision = _evaluate(protected_deltas={"protected": -0.0006})

    assert decision.candidate_state == "blocked"
    assert decision.reason_code == "protected_regression"
    assert decision.failed_metric == "protected_delta:protected"
    assert decision.observed_value == -0.0006
    assert decision.threshold_value == -0.0005


def test_any_admitted_poisoned_view_blocks_candidate() -> None:
    decision = _evaluate(admitted_poisoned_view_ids=("lkr0_view_poison",))

    assert decision.candidate_state == "blocked"
    assert decision.reason_code == "poison_admitted"
    assert decision.failed_metric == "admitted_poisoned_views"
    assert decision.observed_value == 1.0
    assert decision.threshold_value == 0.0


def test_missing_query_class_support_stays_flat() -> None:
    decision = _evaluate(observed_query_classes=("ordinary",))

    assert decision.candidate_state == "flat"
    assert decision.reason_code == "missing_query_class_support"
    assert decision.failed_metric == "missing_query_classes"
    assert decision.observed_value == "protected"
    assert decision.threshold_value == "none"


def test_missing_protected_delta_stays_flat() -> None:
    decision = _evaluate(protected_deltas={})

    assert decision.candidate_state == "flat"
    assert decision.reason_code == "missing_protected_delta"
    assert decision.failed_metric == "missing_protected_deltas"
    assert decision.observed_value == "protected"
    assert decision.threshold_value == "none"


def test_reproducibility_mismatch_blocks_candidate() -> None:
    decision = _evaluate(actual_replay_hash=HASH_B)

    assert decision.candidate_state == "blocked"
    assert decision.reason_code == "reproducibility_mismatch"
    assert decision.failed_metric == "replay_hash"
    assert decision.observed_value == HASH_B
    assert decision.threshold_value == HASH_A


def test_all_green_is_candidate_only_but_runtime_remains_flat() -> None:
    decision = _evaluate()

    assert decision.candidate_state == "candidate_only"
    assert decision.reason_code == "all_learning_gates_green"
    assert decision.failed_metric is None
    assert decision.runtime_recommendation == "flat"
    assert decision.improvement_claim is False


def test_diagnostic_selector_cannot_enter_candidate_gate() -> None:
    decision = _evaluate(candidate_selector="semantic")

    assert decision.candidate_state == "blocked"
    assert decision.reason_code == "diagnostic_selector_not_eligible"
    assert decision.failed_metric == "candidate_selector"


@pytest.mark.parametrize(
    ("overrides", "match"),
    (
        ({"aggregate_delta": math.nan}, "aggregate_delta"),
        ({"permutation_p95": True}, "permutation_p95"),
        ({"protected_deltas": {"protected": math.inf}}, "protected_deltas"),
        ({"required_query_classes": ("ordinary", "ordinary")}, "duplicates"),
        ({"admitted_poisoned_view_ids": ("unsafe view",)}, "poisoned"),
        ({"expected_replay_hash": "a" * 64}, "expected_replay_hash"),
    ),
)
def test_policy_rejects_ambiguous_or_unbound_inputs(overrides, match: str) -> None:
    with pytest.raises((TypeError, ValueError), match=match):
        _evaluate(**overrides)
