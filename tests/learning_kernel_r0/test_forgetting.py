from __future__ import annotations

import pytest

from benchmarks.learning_kernel_r0.forgetting import (
    ForgettingPolicy,
    apply_lifecycle,
    forgetting_regret,
    reduce_lifecycle,
)
from benchmarks.learning_kernel_r0.schema import memory_view_from_mapping


HASH_A = "sha256:" + "a" * 64
POLICY = ForgettingPolicy(
    min_active_support=2,
    archive_harm_threshold=2,
)


def active_view():
    return memory_view_from_mapping(
        {
            "view_id": "lkr0_view_alpha_aaaaaaaaaaaa",
            "source_packet_hash": HASH_A,
            "route_key": "compass/s4/provider_boundary",
            "query_class": "project_recall",
            "action_kind": "repair",
            "representation": "distilled",
            "rendered_text": "Use the declared credential field.",
            "semantic_score": 0.9,
            "verification_state": "independent_verified",
            "verdict": "success",
            "lifecycle_state": "active",
            "expires_at": None,
        }
    )


def transition(
    current: str = "active",
    *,
    independent_support: int = 2,
    verified_harm: int = 0,
    protected_harm: bool = False,
    expired: bool = False,
) -> str:
    return reduce_lifecycle(
        current,
        independent_support=independent_support,
        verified_harm=verified_harm,
        protected_harm=protected_harm,
        expired=expired,
        policy=POLICY,
    )


def test_low_support_cools_instead_of_deleting() -> None:
    assert transition(independent_support=1) == "cooling"


def test_verified_harm_archives_at_explicit_threshold() -> None:
    assert transition(verified_harm=2, independent_support=10) == "archived"


def test_protected_harm_archives_despite_aggregate_support() -> None:
    assert transition(protected_harm=True, independent_support=100) == "archived"


def test_expired_active_view_cools() -> None:
    assert transition(expired=True) == "cooling"


def test_archived_view_is_terminal_until_signed_recovery_exists() -> None:
    assert transition("archived", independent_support=2) == "archived"
    assert transition("archived", independent_support=100) == "archived"


def test_cooled_view_can_recover_with_independent_support() -> None:
    assert transition("cooling", independent_support=3) == "active"


def test_apply_lifecycle_changes_only_reversible_view_state() -> None:
    source = active_view()
    transitioned = apply_lifecycle(
        source,
        independent_support=1,
        verified_harm=0,
        protected_harm=False,
        expired=False,
        policy=POLICY,
    )

    assert source.lifecycle_state == "active"
    assert transitioned.lifecycle_state == "cooling"
    assert transitioned.source_packet_hash == source.source_packet_hash
    assert transitioned.view_id == source.view_id
    assert transitioned.rendered_text == source.rendered_text


def test_forgetting_regret_uses_matched_outcomes_without_mutation() -> None:
    selected = (True, False, False, True)
    oracle = (True, True, True, True)

    assert forgetting_regret(selected, oracle) == 0.5
    assert selected == (True, False, False, True)
    assert oracle == (True, True, True, True)


def test_forgetting_regret_is_nonnegative() -> None:
    assert forgetting_regret((True, True), (True, False)) == 0.0


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("independent_support", True),
        ("verified_harm", -1),
        ("protected_harm", 1),
        ("expired", "no"),
    ),
)
def test_reducer_rejects_ambiguous_inputs(field: str, value: object) -> None:
    kwargs = {
        "independent_support": 2,
        "verified_harm": 0,
        "protected_harm": False,
        "expired": False,
        "policy": POLICY,
    }
    kwargs[field] = value
    with pytest.raises((TypeError, ValueError), match=field):
        reduce_lifecycle("active", **kwargs)


def test_policy_rejects_nonpositive_thresholds() -> None:
    with pytest.raises(ValueError, match="min_active_support"):
        ForgettingPolicy(
            min_active_support=0,
            archive_harm_threshold=2,
        )
