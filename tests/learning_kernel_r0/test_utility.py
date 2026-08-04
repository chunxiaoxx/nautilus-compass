from __future__ import annotations

import pytest

from benchmarks.learning_kernel_r0.utility import UtilityObservation, rebuild_utility


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64


def observation(
    *,
    reward: float,
    result_hash: str,
    view_id: str = "lkr0_view_alpha_aaaaaaaaaaaa",
    verification_state: str = "independent_verified",
) -> UtilityObservation:
    return UtilityObservation(
        context_key=("compass/s4/provider_boundary", "project_recall", "repair"),
        view_id=view_id,
        reward=reward,
        result_hash=result_hash,
        verification_state=verification_state,
        verdict_hash=HASH_C,
    )


def test_rebuild_utility_computes_exact_context_mean() -> None:
    scores = rebuild_utility(
        (
            observation(reward=1.0, result_hash=HASH_A),
            observation(reward=0.0, result_hash=HASH_B),
        )
    )

    assert scores[
        (
            "compass/s4/provider_boundary",
            "project_recall",
            "repair",
            "lkr0_view_alpha_aaaaaaaaaaaa",
        )
    ] == 0.5


def test_duplicate_identical_result_is_idempotent() -> None:
    item = observation(reward=1.0, result_hash=HASH_A)
    assert rebuild_utility((item, item)) == rebuild_utility((item,))


def test_duplicate_result_hash_with_conflicting_content_is_rejected() -> None:
    with pytest.raises(ValueError, match="conflicting duplicate result_hash"):
        rebuild_utility(
            (
                observation(reward=1.0, result_hash=HASH_A),
                observation(reward=-1.0, result_hash=HASH_A),
            )
        )


def test_unverified_observation_is_rejected_by_rebuild() -> None:
    with pytest.raises(ValueError, match="independent_verified"):
        rebuild_utility(
            (
                observation(
                    reward=1.0,
                    result_hash=HASH_A,
                    verification_state="local_only",
                ),
            )
        )


def test_bare_verdict_hash_and_nonfinite_reward_are_rejected() -> None:
    with pytest.raises(ValueError, match="verdict_hash must be sha256"):
        UtilityObservation(
            context_key=("route", "query", "action"),
            view_id="lkr0_view_alpha_aaaaaaaaaaaa",
            reward=1.0,
            result_hash=HASH_A,
            verification_state="independent_verified",
            verdict_hash="c" * 64,
        )

    with pytest.raises(ValueError, match="reward must be finite"):
        observation(reward=float("nan"), result_hash=HASH_A)
