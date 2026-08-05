from __future__ import annotations

from dataclasses import replace

import pytest

from benchmarks.live_agent_c2.metrics import (
    PairOutcome,
    compute_metrics,
    outcome_from_mapping,
    outcome_to_mapping,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def outcome(
    index: int,
    *,
    provider_key: str = "codex/gpt-5-codex",
    query_class: str = "episodic_lookup",
    flat_success: bool = False,
    governed_success: bool = True,
    protected: bool = False,
    replay_verified: bool = True,
    poison_admissions: int = 0,
    flat_cost=0.01,
    governed_cost=0.02,
):
    return PairOutcome(
        pair_id=f"c2_pair_metric_{index:04d}",
        provider_key=provider_key,
        query_class=query_class,
        protected=protected,
        flat_success=flat_success,
        governed_success=governed_success,
        flat_latency_ms=100 + index,
        governed_latency_ms=120 + index,
        flat_input_tokens=10,
        flat_output_tokens=2,
        governed_input_tokens=14,
        governed_output_tokens=3,
        flat_cost_usd=flat_cost,
        governed_cost_usd=governed_cost,
        flat_bundle_hash=HASH_A,
        governed_bundle_hash=HASH_B,
        replay_verified=replay_verified,
        poison_admissions=poison_admissions,
    )


def test_paired_bootstrap_is_deterministic_and_provider_stratified():
    rows = tuple(outcome(index) for index in range(12)) + tuple(
        outcome(
            100 + index,
            provider_key="claude/fable-5",
            flat_success=True,
            governed_success=False,
        )
        for index in range(4)
    )

    first = compute_metrics(rows, seed=2486, bootstrap_samples=1000)
    second = compute_metrics(rows, seed=2486, bootstrap_samples=1000)

    assert first == second
    assert first.overall.delta == 0.5
    assert first.by_provider["codex/gpt-5-codex"].delta == 1.0
    assert first.by_provider["claude/fable-5"].delta == -1.0
    assert first.overall.ci_low <= first.overall.delta <= first.overall.ci_high
    assert first.pairs_hash.startswith("sha256:")


def test_metrics_report_provider_query_tokens_cost_latency_and_unknown_costs():
    rows = (
        outcome(0, flat_cost=None),
        outcome(1, governed_cost=None),
    )
    metrics = compute_metrics(
        rows,
        seed=2486,
        bootstrap_samples=500,
        invalid_attempt_count=3,
        retry_count=2,
    )

    assert metrics.total_pairs == 2
    assert metrics.invalid_attempt_count == 3
    assert metrics.retry_count == 2
    assert metrics.overall.flat_input_tokens == 20
    assert metrics.overall.governed_output_tokens == 6
    assert metrics.overall.known_cost_usd == pytest.approx(0.03)
    assert metrics.overall.unknown_cost_arms == 2
    assert metrics.overall.flat_latency_p95_ms == 101.0
    assert metrics.overall.governed_latency_p95_ms == 121.0
    assert (
        "codex/gpt-5-codex",
        "episodic_lookup",
    ) in metrics.by_provider_query_class


def test_metrics_keep_replay_and_poison_failures_visible():
    rows = (
        outcome(0, replay_verified=False),
        outcome(1, poison_admissions=1),
    )
    metrics = compute_metrics(rows, seed=1, bootstrap_samples=200)

    assert metrics.overall.replay_failures == 1
    assert metrics.overall.poison_admissions == 1


def test_metrics_reject_duplicate_pairs_and_invalid_types():
    row = outcome(0)
    assert outcome_from_mapping(outcome_to_mapping(row)) == row
    unknown = outcome_to_mapping(row)
    unknown["raw_output"] = "forbidden"
    with pytest.raises(TypeError, match="unknown PairOutcome fields"):
        outcome_from_mapping(unknown)
    with pytest.raises(ValueError, match="unique pair_id"):
        compute_metrics((row, row), seed=1, bootstrap_samples=200)
    with pytest.raises(TypeError, match="PairOutcome"):
        compute_metrics(({"pair_id": "not-typed"},), seed=1, bootstrap_samples=200)
    with pytest.raises(ValueError, match="query_class"):
        replace(row, query_class="unknown")
    with pytest.raises(ValueError, match="protected"):
        replace(row, query_class="protected_noop", protected=False)
