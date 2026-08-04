"""Hash-bound causal, safety, forgetting, latency, and cost metrics."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass
from statistics import median

from benchmarks.poi_gate2.action_metrics import percentile_95

from .forgetting import forgetting_regret
from .runner import validate_result_hash
from .schema import LearningRunResult


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_VIEW_ID_PATTERN = re.compile(r"lkr0_view_[a-z0-9_]{1,96}")


@dataclass(frozen=True, slots=True)
class RecoveryObservation:
    source_result_hash: str
    view_id: str
    eligible: bool
    recovered: bool
    verification_state: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_result_hash, str) or _HASH_PATTERN.fullmatch(
            self.source_result_hash
        ) is None:
            raise ValueError("source_result_hash must be a lowercase SHA-256 value")
        if not isinstance(self.view_id, str) or _VIEW_ID_PATTERN.fullmatch(self.view_id) is None:
            raise ValueError("view_id must be a stable lkr0_view_ identifier")
        if not isinstance(self.eligible, bool) or not isinstance(self.recovered, bool):
            raise TypeError("eligible and recovered must be booleans")
        if self.recovered and not self.eligible:
            raise ValueError("recovered observation must be eligible")
        if self.verification_state not in {
            "blocked",
            "local_only",
            "independent_verified",
        }:
            raise ValueError("verification_state is unsupported")


@dataclass(frozen=True, slots=True)
class MetricBreakdown:
    selector: str
    intervention: str
    query_class: str
    count: int
    success_rate: float
    first_pass_success_rate: float


@dataclass(frozen=True, slots=True)
class LearningMetrics:
    total_runs: int
    success_rate: float
    first_pass_success_rate: float
    raw_vs_distilled_delta: float
    poison_rejection_rate: float
    contradiction_rejection_rate: float
    forgetting_regret: float
    recovery_rate: float
    latency_p50_ms: float
    latency_p95_ms: float
    total_input_tokens: int
    total_output_tokens: int
    total_estimated_cost_usd: float
    breakdown: tuple[MetricBreakdown, ...]


def aggregate_metrics(
    results: tuple[LearningRunResult, ...],
    *,
    recovery_observations: tuple[RecoveryObservation, ...] = (),
) -> LearningMetrics:
    _validate_results(results)
    raw = tuple(row for row in results if row.intervention == "raw")
    distilled = tuple(row for row in results if row.intervention == "distilled")
    if not raw or not distilled:
        raise ValueError("raw and distilled results are required")

    stale = tuple(row for row in results if row.intervention == "stale")
    matched_stale, matched_oracle = _matched_forgetting_outcomes(stale, distilled)
    recovery_rate = _recovery_rate(results, recovery_observations)
    groups: dict[tuple[str, str, str], list[LearningRunResult]] = defaultdict(list)
    for result in results:
        groups[(result.selector, result.intervention, result.query_class)].append(result)

    return LearningMetrics(
        total_runs=len(results),
        success_rate=_success_rate(results),
        first_pass_success_rate=sum(row.first_pass_success for row in results) / len(results),
        raw_vs_distilled_delta=_matched_intervention_delta(raw, distilled),
        poison_rejection_rate=_rejection_rate(results, "poisoned"),
        contradiction_rejection_rate=_rejection_rate(results, "contradictory"),
        forgetting_regret=(
            forgetting_regret(matched_stale, matched_oracle) if matched_stale else 0.0
        ),
        recovery_rate=recovery_rate,
        latency_p50_ms=float(median(row.latency_ms for row in results)),
        latency_p95_ms=percentile_95(tuple(row.latency_ms for row in results)),
        total_input_tokens=sum(row.input_tokens for row in results),
        total_output_tokens=sum(row.output_tokens for row in results),
        total_estimated_cost_usd=sum(row.estimated_cost_usd for row in results),
        breakdown=tuple(
            MetricBreakdown(
                selector=key[0],
                intervention=key[1],
                query_class=key[2],
                count=len(group),
                success_rate=_success_rate(tuple(group)),
                first_pass_success_rate=sum(row.first_pass_success for row in group)
                / len(group),
            )
            for key, group in sorted(groups.items())
        ),
    )


def _matched_forgetting_outcomes(
    stale: tuple[LearningRunResult, ...],
    distilled: tuple[LearningRunResult, ...],
) -> tuple[tuple[bool, ...], tuple[bool, ...]]:
    oracle = {_match_key(row): row for row in distilled}
    selected_outcomes = []
    oracle_outcomes = []
    for row in sorted(stale, key=_match_key):
        match = oracle.get(_match_key(row))
        if match is None:
            raise ValueError("every stale result requires a matched distilled oracle")
        selected_outcomes.append(row.success)
        oracle_outcomes.append(match.success)
    return tuple(selected_outcomes), tuple(oracle_outcomes)


def _matched_intervention_delta(
    raw: tuple[LearningRunResult, ...],
    distilled: tuple[LearningRunResult, ...],
) -> float:
    raw_by_key = {_match_key(row): row for row in raw}
    distilled_by_key = {_match_key(row): row for row in distilled}
    if set(raw_by_key) != set(distilled_by_key):
        raise ValueError("matched raw and distilled results are required")
    deltas = [
        float(distilled_by_key[key].success) - float(raw_by_key[key].success)
        for key in sorted(raw_by_key)
    ]
    return sum(deltas) / len(deltas)


def _match_key(row: LearningRunResult) -> tuple[str, str, str, str, int]:
    return (
        row.task_id,
        row.task_hash,
        row.query_class,
        row.selector,
        row.replica,
    )


def _rejection_rate(results: tuple[LearningRunResult, ...], intervention: str) -> float:
    relevant = tuple(row for row in results if row.intervention == intervention)
    if not relevant:
        return 0.0
    return sum(not row.selected_view_ids for row in relevant) / len(relevant)


def _recovery_rate(
    results: tuple[LearningRunResult, ...],
    observations: tuple[RecoveryObservation, ...],
) -> float:
    if not isinstance(observations, tuple):
        raise TypeError("recovery_observations must be a tuple")
    results_by_hash = {row.result_hash: row for row in results}
    seen_hashes = set()
    eligible = []
    for observation in observations:
        if not isinstance(observation, RecoveryObservation):
            raise TypeError("recovery_observations must contain RecoveryObservation values")
        if observation.verification_state != "independent_verified":
            raise ValueError("recovery observations must be independent_verified")
        source = results_by_hash.get(observation.source_result_hash)
        if source is None:
            raise ValueError("recovery source_result_hash must bind to an evaluated result")
        if source.intervention != "stale":
            raise ValueError("recovery evidence must bind to a stale result")
        if observation.view_id not in source.selected_view_ids:
            raise ValueError("recovery evidence must bind to a selected view")
        if observation.source_result_hash in seen_hashes:
            raise ValueError("recovery source_result_hash values must be unique")
        seen_hashes.add(observation.source_result_hash)
        if observation.eligible:
            eligible.append(observation.recovered)
    return sum(eligible) / len(eligible) if eligible else 0.0


def _success_rate(results: tuple[LearningRunResult, ...]) -> float:
    return sum(row.success for row in results) / len(results)


def _validate_results(results: tuple[LearningRunResult, ...]) -> None:
    if not isinstance(results, tuple) or not results:
        raise ValueError("results must be a non-empty tuple")
    if any(not isinstance(row, LearningRunResult) for row in results):
        raise TypeError("results must contain LearningRunResult values")
    for row in results:
        validate_result_hash(row)
    if len({row.run_id for row in results}) != len(results):
        raise ValueError("results must contain unique run_id values")
    if len({row.result_hash for row in results}) != len(results):
        raise ValueError("results must contain unique result_hash values")


__all__ = [
    "LearningMetrics",
    "MetricBreakdown",
    "RecoveryObservation",
    "aggregate_metrics",
]
