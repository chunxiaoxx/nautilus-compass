from __future__ import annotations

import pytest

from benchmarks.learning_kernel_r0.utility import (
    R0_SIGNER_KEY_ID,
    R0_VERIFIER_POLICY_HASH,
    SignedVerdictBinding,
    UtilityObservation,
    rebuild_utility,
)
from gep.verdict_packet import VerdictPacket


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
HASH_C = "sha256:" + "c" * 64

SIGNATURES = {
    (HASH_A, "success"): (
        "f23aa67910a30c6e69e936b33ba271150727f8ca006d76106347127501180b81"
        "c2c4a344ba9051fb940247f0754ce78f22526d8bf94cacaf33b6c3cf07d73f02"
    ),
    (HASH_B, "partial"): (
        "3482278ee52e99524690a8df1522ef82ed533c3b7f819c4fb1403028f4145f49"
        "d844f4580d55d9b8bff176afb169ca16b56435c3ddd4091549e7af537fa7e008"
    ),
    (HASH_B, "success"): (
        "2cee20cd7fe0bdd1552333a33a551f35280d56b02b7743670520ab1b6cf20f5a"
        "b9e2227ae22acc0e7ea39122f6f6bf182cb55726dcf22cfeaad173ed7d635009"
    ),
    (HASH_A, "failure"): (
        "8b1d79a4ba4e4182c8019f70066cda154c2f92bc844e2c16e694633d200ed614"
        "628ab4ae3072f2d60ef5ca4dad700de9946c20d1fc6166f9df8adda2c041580e"
    ),
}


def observation(
    *,
    reward: float,
    result_hash: str,
    view_id: str = "lkr0_view_alpha_aaaaaaaaaaaa",
    verdict_result_hash: str | None = None,
    verdict_outcome: str | None = None,
    signature: str | None = None,
    signer_key_id: str = R0_SIGNER_KEY_ID,
    verifier_policy_hash: str = R0_VERIFIER_POLICY_HASH,
) -> UtilityObservation:
    outcome = verdict_outcome or ("success" if reward == 1.0 else "partial")
    signed_result_hash = verdict_result_hash or result_hash
    verdict = VerdictPacket(
        episode_id="utility_result",
        episode_event_hash=signed_result_hash,
        outcome=outcome,  # type: ignore[arg-type]
        verifier_kind="software_test",
        verifier_version="lkr0-verifier-v1",
        verifier_policy_hash=verifier_policy_hash,
        evidence_hash=HASH_B,
    )
    binding = SignedVerdictBinding(
        verdict=verdict,
        signer_key_id=signer_key_id,
        signature=signature or SIGNATURES[(signed_result_hash, outcome)],
    )
    return UtilityObservation(
        context_key=("compass/s4/provider_boundary", "project_recall", "repair"),
        view_id=view_id,
        reward=reward,
        result_hash=result_hash,
        signed_verdict=binding,
    )


def rebuild(*items: UtilityObservation):
    return rebuild_utility(tuple(items))


def test_rebuild_utility_computes_exact_context_mean() -> None:
    scores = rebuild(
        observation(reward=1.0, result_hash=HASH_A),
        observation(reward=0.0, result_hash=HASH_B),
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
    assert rebuild(item, item) == rebuild(item)


def test_duplicate_result_hash_with_conflicting_content_is_rejected() -> None:
    with pytest.raises(ValueError, match="conflicting duplicate result_hash"):
        rebuild(
            observation(reward=1.0, result_hash=HASH_A),
            observation(
                reward=-1.0,
                result_hash=HASH_A,
                verdict_outcome="failure",
            ),
        )


def test_verdict_must_bind_exact_result_hash() -> None:
    with pytest.raises(ValueError, match="verdict.*result_hash"):
        observation(reward=1.0, result_hash=HASH_A, verdict_result_hash=HASH_B)


def test_reward_must_match_verdict_and_be_finite() -> None:
    with pytest.raises(ValueError, match="reward must match"):
        observation(
            reward=1.0,
            result_hash=HASH_A,
            verdict_outcome="failure",
        )
    with pytest.raises(ValueError, match="reward must be finite"):
        observation(
            reward=float("nan"),
            result_hash=HASH_A,
            verdict_outcome="success",
        )


def test_signature_must_match_pinned_trust_anchor() -> None:
    with pytest.raises(ValueError, match="verdict signature"):
        observation(
            reward=1.0,
            result_hash=HASH_A,
            signature="0" * 128,
        )
    with pytest.raises(ValueError, match="untrusted signer"):
        observation(
            reward=1.0,
            result_hash=HASH_A,
            signer_key_id="caller_supplied_key",
        )


def test_caller_cannot_supply_its_own_verifier_policy() -> None:
    with pytest.raises(ValueError, match="trusted verifier policy"):
        observation(
            reward=1.0,
            result_hash=HASH_A,
            verifier_policy_hash=HASH_C,
            signature="0" * 128,
        )
