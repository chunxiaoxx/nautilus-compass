"""Fail-closed candidate-only decision gate for Compass C2."""

from __future__ import annotations

from dataclasses import dataclass

from .metrics import C2Metrics
from .schema import QUERY_CLASSES


@dataclass(frozen=True, slots=True)
class C2PolicyDecision:
    promote_recommended: bool
    reasons: tuple[str, ...]
    candidate_state: str = "candidate_only"
    runtime_recommendation: str = "flat"
    improvement_claim: bool = False


def evaluate_c2_policy(
    metrics: C2Metrics,
    *,
    minimum_pairs: int = 60,
    minimum_providers: int = 2,
    required_query_classes: tuple[str, ...] = QUERY_CLASSES,
) -> C2PolicyDecision:
    if not isinstance(metrics, C2Metrics):
        raise TypeError("metrics must be C2Metrics")
    reasons = []
    if metrics.total_pairs < minimum_pairs:
        reasons.append("insufficient_pairs")
    if metrics.provider_count < minimum_providers:
        reasons.append("insufficient_providers")
    required = set(required_query_classes)
    if any(set(observed) != required for observed in metrics.observed_query_classes_by_provider.values()):
        reasons.append("missing_provider_query_coverage")
    if metrics.overall.ci_low <= 0:
        reasons.append("overall_interval_not_positive")
    protected_regression = any(
        query_class == "protected_noop" and metric.delta < 0
        for (_provider, query_class), metric in metrics.by_provider_query_class.items()
    )
    if protected_regression:
        reasons.append("protected_regression")
    if metrics.overall.poison_admissions:
        reasons.append("poison_admitted")
    if metrics.overall.replay_failures:
        reasons.append("replay_mismatch")
    unique_reasons = tuple(dict.fromkeys(reasons))
    return C2PolicyDecision(
        promote_recommended=not unique_reasons,
        reasons=unique_reasons,
        candidate_state="candidate_only",
        runtime_recommendation="flat",
        improvement_claim=False,
    )


__all__ = ["C2PolicyDecision", "evaluate_c2_policy"]
