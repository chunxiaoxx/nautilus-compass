from __future__ import annotations

from dataclasses import replace

from benchmarks.live_agent_c2.metrics import PairOutcome, compute_metrics
from benchmarks.live_agent_c2.policy import evaluate_c2_policy
from benchmarks.live_agent_c2.schema import QUERY_CLASSES


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64
PROVIDERS = ("codex/gpt-5-codex", "claude/fable-5")


def row(index, provider_key, query_class, *, flat=False, governed=True):
    return PairOutcome(
        pair_id=f"c2_pair_gate_{index:04d}",
        provider_key=provider_key,
        query_class=query_class,
        protected=query_class == "protected_noop",
        flat_success=flat,
        governed_success=governed,
        flat_latency_ms=100,
        governed_latency_ms=100,
        flat_input_tokens=10,
        flat_output_tokens=1,
        governed_input_tokens=10,
        governed_output_tokens=1,
        flat_cost_usd=None,
        governed_cost_usd=None,
        flat_bundle_hash=HASH_A,
        governed_bundle_hash=HASH_B,
        replay_verified=True,
        poison_admissions=0,
    )


def passing_rows():
    rows = []
    index = 0
    for provider_key in PROVIDERS:
        for query_class in QUERY_CLASSES:
            for _ in range(8):
                rows.append(row(index, provider_key, query_class))
                index += 1
    return tuple(rows)


def decision(rows):
    metrics = compute_metrics(rows, seed=2486, bootstrap_samples=1000)
    return evaluate_c2_policy(metrics), metrics


def test_all_green_gate_only_recommends_next_stage_and_keeps_runtime_flat():
    result, metrics = decision(passing_rows())

    assert metrics.total_pairs == 64
    assert metrics.overall.ci_low == 1.0
    assert result.promote_recommended is True
    assert result.reasons == ()
    assert result.candidate_state == "candidate_only"
    assert result.runtime_recommendation == "flat"
    assert result.improvement_claim is False


def test_gate_rejects_insufficient_pairs_provider_or_query_coverage():
    rows = passing_rows()
    small, _ = decision(rows[:40])
    one_provider, _ = decision(tuple(item for item in rows if item.provider_key == PROVIDERS[0]))
    missing_class, _ = decision(
        tuple(item for item in rows if item.query_class != "conflict_resolution")
    )

    assert "insufficient_pairs" in small.reasons
    assert "insufficient_providers" in one_provider.reasons
    assert "missing_provider_query_coverage" in missing_class.reasons


def test_gate_rejects_nonpositive_interval_protected_regression_poison_and_replay():
    rows = list(passing_rows())
    for index in range(32):
        rows[index] = replace(rows[index], flat_success=True, governed_success=False)
    nonuniform, _ = decision(tuple(rows))
    assert "overall_interval_not_positive" in nonuniform.reasons

    rows = list(passing_rows())
    protected_indexes = [
        index
        for index, item in enumerate(rows)
        if item.provider_key == PROVIDERS[0] and item.query_class == "protected_noop"
    ]
    for index in protected_indexes:
        rows[index] = replace(rows[index], flat_success=True, governed_success=False)
    protected, _ = decision(tuple(rows))
    assert "protected_regression" in protected.reasons

    poisoned_rows = list(passing_rows())
    poisoned_rows[0] = replace(poisoned_rows[0], poison_admissions=1)
    poisoned, _ = decision(tuple(poisoned_rows))
    assert "poison_admitted" in poisoned.reasons

    replay_rows = list(passing_rows())
    replay_rows[0] = replace(replay_rows[0], replay_verified=False)
    replay, _ = decision(tuple(replay_rows))
    assert "replay_mismatch" in replay.reasons


def test_gate_rejects_zero_delta_even_when_sample_size_is_large():
    rows = tuple(replace(item, flat_success=True, governed_success=True) for item in passing_rows())
    result, metrics = decision(rows)

    assert metrics.overall.delta == 0.0
    assert result.promote_recommended is False
    assert "overall_interval_not_positive" in result.reasons
