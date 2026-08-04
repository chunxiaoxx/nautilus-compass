from __future__ import annotations

import pytest

from benchmarks.learning_kernel_r0.metrics import (
    RecoveryObservation,
    aggregate_metrics,
)
from benchmarks.learning_kernel_r0.runner import build_run_result


HASH_A = "sha256:" + "a" * 64


def _result(
    task: str,
    intervention: str,
    success: bool,
    *,
    replica: int = 0,
    selected: tuple[str, ...] = (),
    latency_ms: int = 10,
):
    return build_run_result(
        task_id=f"lkr0_task_{task}",
        task_hash=HASH_A,
        query_class="ordinary",
        selector="governed",
        intervention=intervention,
        replica=replica,
        selected_view_ids=selected,
        success=success,
        first_pass_success=success,
        verifier_code="mechanical_pass" if success else "mechanical_fail",
        latency_ms=latency_ms,
        input_tokens=10,
        output_tokens=2,
        estimated_cost_usd=0.01,
    )


def _results():
    return (
        _result("alpha", "raw", False, latency_ms=10),
        _result("alpha", "distilled", True, latency_ms=20),
        _result(
            "alpha",
            "stale",
            False,
            selected=("lkr0_view_stale_alpha",),
            latency_ms=30,
        ),
        _result("alpha", "poisoned", False, latency_ms=40),
        _result(
            "alpha",
            "contradictory",
            False,
            selected=("lkr0_view_bad_alpha",),
            latency_ms=50,
        ),
        _result("beta", "raw", True, latency_ms=60),
        _result("beta", "distilled", True, latency_ms=70),
        _result(
            "beta",
            "stale",
            True,
            selected=("lkr0_view_stale_beta",),
            latency_ms=80,
        ),
    )


def test_metrics_report_causal_safety_forgetting_and_cost_breakdowns() -> None:
    results = _results()
    recoveries = (
        RecoveryObservation(
            source_result_hash=results[2].result_hash,
            view_id="lkr0_view_stale_alpha",
            eligible=True,
            recovered=False,
            verification_state="independent_verified",
        ),
        RecoveryObservation(
            source_result_hash=results[7].result_hash,
            view_id="lkr0_view_stale_beta",
            eligible=True,
            recovered=True,
            verification_state="independent_verified",
        ),
    )

    summary = aggregate_metrics(results, recovery_observations=recoveries)

    assert summary.total_runs == 8
    assert summary.success_rate == pytest.approx(4 / 8)
    assert summary.raw_vs_distilled_delta == pytest.approx(0.5)
    assert summary.poison_rejection_rate == 1.0
    assert summary.contradiction_rejection_rate == 0.0
    assert summary.forgetting_regret == 0.5
    assert summary.recovery_rate == 0.5
    assert summary.latency_p50_ms == 45.0
    assert summary.latency_p95_ms == 80.0
    assert summary.total_input_tokens == 80
    assert summary.total_output_tokens == 16
    assert summary.total_estimated_cost_usd == pytest.approx(0.08)
    assert len(summary.breakdown) == 5
    stale = next(row for row in summary.breakdown if row.intervention == "stale")
    assert stale.count == 2
    assert stale.success_rate == 0.5


def test_metrics_require_matched_distilled_oracle_for_stale_results() -> None:
    unmatched = (
        _result("alpha", "raw", False),
        _result("alpha", "distilled", True),
        _result("beta", "stale", False),
    )
    with pytest.raises(ValueError, match="matched distilled oracle"):
        aggregate_metrics(unmatched)


def test_metrics_require_matched_raw_and_distilled_causal_pairs() -> None:
    unmatched = (
        _result("alpha", "raw", False),
        _result("beta", "distilled", True),
    )
    with pytest.raises(ValueError, match="matched raw and distilled"):
        aggregate_metrics(unmatched)


def test_recovery_observations_require_independent_hash_bound_evidence() -> None:
    results = _results()
    local_only = RecoveryObservation(
        source_result_hash=results[2].result_hash,
        view_id="lkr0_view_stale_alpha",
        eligible=True,
        recovered=True,
        verification_state="local_only",
    )
    with pytest.raises(ValueError, match="independent_verified"):
        aggregate_metrics(results, recovery_observations=(local_only,))

    unknown_hash = RecoveryObservation(
        source_result_hash="sha256:" + "f" * 64,
        view_id="lkr0_view_stale_alpha",
        eligible=True,
        recovered=True,
        verification_state="independent_verified",
    )
    with pytest.raises(ValueError, match="source_result_hash"):
        aggregate_metrics(results, recovery_observations=(unknown_hash,))

    wrong_intervention = RecoveryObservation(
        source_result_hash=results[1].result_hash,
        view_id="lkr0_view_stale_alpha",
        eligible=True,
        recovered=True,
        verification_state="independent_verified",
    )
    with pytest.raises(ValueError, match="stale result"):
        aggregate_metrics(results, recovery_observations=(wrong_intervention,))

    wrong_view = RecoveryObservation(
        source_result_hash=results[2].result_hash,
        view_id="lkr0_view_stale_unknown",
        eligible=True,
        recovered=True,
        verification_state="independent_verified",
    )
    with pytest.raises(ValueError, match="selected view"):
        aggregate_metrics(results, recovery_observations=(wrong_view,))
