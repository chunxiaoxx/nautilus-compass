"""Candidate-only policy gate for Learning Kernel R0 evidence."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass


PROTECTED_REGRESSION_FLOOR = -0.0005

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_VIEW_ID_PATTERN = re.compile(r"lkr0_view_[a-z0-9_]{1,96}")


@dataclass(frozen=True, slots=True)
class CandidateDecision:
    candidate_state: str
    reason_code: str
    failed_metric: str | None
    observed_value: float | str | None
    threshold_value: float | str | None
    runtime_recommendation: str = "flat"
    improvement_claim: bool = False


def evaluate_candidate_policy(
    *,
    aggregate_delta: float,
    permutation_p95: float,
    candidate_selector: str,
    protected_deltas: Mapping[str, float],
    protected_query_classes: tuple[str, ...],
    required_query_classes: tuple[str, ...],
    observed_query_classes: tuple[str, ...],
    admitted_poisoned_view_ids: tuple[str, ...],
    expected_replay_hash: str,
    actual_replay_hash: str,
) -> CandidateDecision:
    """Return a diagnostic decision while leaving the runtime policy flat."""

    aggregate_delta = _finite_number("aggregate_delta", aggregate_delta)
    permutation_p95 = _finite_number("permutation_p95", permutation_p95)
    _validate_token("candidate_selector", candidate_selector)
    required = _token_tuple("required_query_classes", required_query_classes)
    observed = _token_tuple("observed_query_classes", observed_query_classes)
    protected = _token_tuple("protected_query_classes", protected_query_classes)
    if not set(protected).issubset(required):
        raise ValueError("protected_query_classes must be required query classes")
    deltas = _protected_deltas(protected_deltas, protected)
    poisoned = _view_id_tuple("admitted_poisoned_view_ids", admitted_poisoned_view_ids)
    _validate_hash("expected_replay_hash", expected_replay_hash)
    _validate_hash("actual_replay_hash", actual_replay_hash)

    if actual_replay_hash != expected_replay_hash:
        return _decision(
            "blocked",
            "reproducibility_mismatch",
            "replay_hash",
            actual_replay_hash,
            expected_replay_hash,
        )
    if candidate_selector != "governed":
        return _decision(
            "blocked",
            "diagnostic_selector_not_eligible",
            "candidate_selector",
            candidate_selector,
            "governed",
        )
    if poisoned:
        return _decision(
            "blocked",
            "poison_admitted",
            "admitted_poisoned_views",
            float(len(poisoned)),
            0.0,
        )
    regressions = tuple(
        (query_class, delta)
        for query_class, delta in sorted(deltas.items())
        if delta < PROTECTED_REGRESSION_FLOOR
    )
    if regressions:
        query_class, delta = regressions[0]
        return _decision(
            "blocked",
            "protected_regression",
            f"protected_delta:{query_class}",
            delta,
            PROTECTED_REGRESSION_FLOOR,
        )
    missing = tuple(sorted(set(required) - set(observed)))
    if missing:
        return _decision(
            "flat",
            "missing_query_class_support",
            "missing_query_classes",
            ",".join(missing),
            "none",
        )
    missing_deltas = tuple(sorted(set(protected) - set(deltas)))
    if missing_deltas:
        return _decision(
            "flat",
            "missing_protected_delta",
            "missing_protected_deltas",
            ",".join(missing_deltas),
            "none",
        )
    if aggregate_delta <= 0:
        return _decision(
            "flat",
            "delta_not_positive",
            "aggregate_delta",
            aggregate_delta,
            0.0,
        )
    if aggregate_delta <= permutation_p95:
        return _decision(
            "flat",
            "delta_not_above_permutation_p95",
            "aggregate_delta",
            aggregate_delta,
            permutation_p95,
        )
    return _decision(
        "candidate_only",
        "all_learning_gates_green",
        None,
        None,
        None,
    )


def _decision(
    state: str,
    reason: str,
    metric: str | None,
    observed: float | str | None,
    threshold: float | str | None,
) -> CandidateDecision:
    return CandidateDecision(
        candidate_state=state,
        reason_code=reason,
        failed_metric=metric,
        observed_value=observed,
        threshold_value=threshold,
        runtime_recommendation="flat",
        improvement_claim=False,
    )


def _protected_deltas(
    values: Mapping[str, float],
    protected_query_classes: tuple[str, ...],
) -> dict[str, float]:
    if not isinstance(values, Mapping):
        raise TypeError("protected_deltas must be a mapping")
    output = {}
    for query_class, value in values.items():
        _validate_token("protected_deltas query class", query_class)
        if query_class not in protected_query_classes:
            raise ValueError("protected_deltas must refer to protected query classes")
        output[query_class] = _finite_number("protected_deltas", value)
    return output


def _token_tuple(name: str, values: object) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    for value in values:
        _validate_token(name, value)
    return values


def _view_id_tuple(name: str, values: object) -> tuple[str, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{name} must be a tuple")
    if len(set(values)) != len(values):
        raise ValueError(f"{name} must not contain duplicates")
    for value in values:
        if not isinstance(value, str) or _VIEW_ID_PATTERN.fullmatch(value) is None:
            raise ValueError(f"{name} contains an invalid poisoned view identifier")
    return values


def _finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    normalized = float(value)
    if not math.isfinite(normalized):
        raise ValueError(f"{name} must be finite")
    return normalized


def _validate_token(name: str, value: object) -> None:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must contain safe tokens")


def _validate_hash(name: str, value: object) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 value")


__all__ = [
    "PROTECTED_REGRESSION_FLOOR",
    "CandidateDecision",
    "evaluate_candidate_policy",
]
