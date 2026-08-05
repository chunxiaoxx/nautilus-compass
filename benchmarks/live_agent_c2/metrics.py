"""Provider-stratified paired metrics for Compass C2."""

from __future__ import annotations

import math
import random
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType
from typing import Optional

from benchmarks.common_statistics import percentile_95
from benchmarks.poi_gate2.canonical import hash_json

from .schema import QUERY_CLASSES


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_PAIR_ID_PATTERN = re.compile(r"c2_pair_[a-z0-9_]{1,96}")
_PROVIDER_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")


@dataclass(frozen=True, slots=True)
class PairOutcome:
    pair_id: str
    provider_key: str
    query_class: str
    protected: bool
    flat_success: bool
    governed_success: bool
    flat_latency_ms: int
    governed_latency_ms: int
    flat_input_tokens: int
    flat_output_tokens: int
    governed_input_tokens: int
    governed_output_tokens: int
    flat_cost_usd: Optional[float]
    governed_cost_usd: Optional[float]
    flat_bundle_hash: str
    governed_bundle_hash: str
    replay_verified: bool
    poison_admissions: int

    def __post_init__(self) -> None:
        if not isinstance(self.pair_id, str) or _PAIR_ID_PATTERN.fullmatch(self.pair_id) is None:
            raise ValueError("pair_id must be a stable c2_pair_ identifier")
        if not isinstance(self.provider_key, str) or _PROVIDER_PATTERN.fullmatch(self.provider_key) is None:
            raise ValueError("provider_key must be a safe provider/model route")
        if self.query_class not in QUERY_CLASSES:
            raise ValueError("query_class is unsupported")
        if not isinstance(self.protected, bool):
            raise TypeError("protected must be a boolean")
        if self.protected is not (self.query_class == "protected_noop"):
            raise ValueError("protected must match protected_noop query_class")
        _bool("flat_success", self.flat_success)
        _bool("governed_success", self.governed_success)
        _bool("replay_verified", self.replay_verified)
        for name in (
            "flat_latency_ms",
            "governed_latency_ms",
            "flat_input_tokens",
            "flat_output_tokens",
            "governed_input_tokens",
            "governed_output_tokens",
            "poison_admissions",
        ):
            _nonnegative_int(name, getattr(self, name))
        _optional_cost("flat_cost_usd", self.flat_cost_usd)
        _optional_cost("governed_cost_usd", self.governed_cost_usd)
        _hash("flat_bundle_hash", self.flat_bundle_hash)
        _hash("governed_bundle_hash", self.governed_bundle_hash)

    @property
    def delta(self) -> float:
        return float(self.governed_success) - float(self.flat_success)


@dataclass(frozen=True, slots=True)
class MetricSlice:
    pair_count: int
    flat_success_rate: float
    governed_success_rate: float
    delta: float
    ci_low: float
    ci_high: float
    flat_latency_mean_ms: float
    governed_latency_mean_ms: float
    flat_latency_p95_ms: float
    governed_latency_p95_ms: float
    flat_input_tokens: int
    flat_output_tokens: int
    governed_input_tokens: int
    governed_output_tokens: int
    known_cost_usd: float
    unknown_cost_arms: int
    poison_admissions: int
    replay_failures: int


@dataclass(frozen=True, slots=True)
class C2Metrics:
    total_pairs: int
    provider_count: int
    invalid_attempt_count: int
    retry_count: int
    overall: MetricSlice
    by_provider: Mapping[str, MetricSlice]
    by_query_class: Mapping[str, MetricSlice]
    by_provider_query_class: Mapping[tuple[str, str], MetricSlice]
    observed_query_classes_by_provider: Mapping[str, tuple[str, ...]]
    pairs_hash: str


def compute_metrics(
    outcomes: tuple[PairOutcome, ...],
    *,
    seed: int,
    bootstrap_samples: int,
    invalid_attempt_count: int = 0,
    retry_count: int = 0,
) -> C2Metrics:
    _validate_metric_inputs(
        outcomes,
        seed,
        bootstrap_samples,
        invalid_attempt_count,
        retry_count,
    )
    providers = _groups(outcomes, lambda row: row.provider_key)
    query_classes = _groups(outcomes, lambda row: row.query_class)
    provider_query = _groups(outcomes, lambda row: (row.provider_key, row.query_class))
    by_provider = {
        key: _metric_slice(rows, seed=_group_seed(seed, key), samples=bootstrap_samples)
        for key, rows in sorted(providers.items())
    }
    by_query_class = {
        key: _metric_slice(rows, seed=_group_seed(seed, key), samples=bootstrap_samples)
        for key, rows in sorted(query_classes.items())
    }
    by_provider_query_class = {
        key: _metric_slice(rows, seed=_group_seed(seed, key), samples=bootstrap_samples)
        for key, rows in sorted(provider_query.items())
    }
    coverage = {
        provider: tuple(sorted({row.query_class for row in rows}))
        for provider, rows in sorted(providers.items())
    }
    return C2Metrics(
        total_pairs=len(outcomes),
        provider_count=len(providers),
        invalid_attempt_count=invalid_attempt_count,
        retry_count=retry_count,
        overall=_metric_slice(
            outcomes,
            seed=seed,
            samples=bootstrap_samples,
            strata=lambda row: row.provider_key,
        ),
        by_provider=MappingProxyType(by_provider),
        by_query_class=MappingProxyType(by_query_class),
        by_provider_query_class=MappingProxyType(by_provider_query_class),
        observed_query_classes_by_provider=MappingProxyType(coverage),
        pairs_hash=hash_json(
            {
                "domain": "compass.live_agent_c2.pair_outcomes.v1",
                "outcomes": [_outcome_mapping(row) for row in sorted(outcomes, key=lambda x: x.pair_id)],
            }
        ),
    )


def _metric_slice(
    rows: tuple[PairOutcome, ...],
    *,
    seed: int,
    samples: int,
    strata=None,
) -> MetricSlice:
    deltas = tuple(row.delta for row in rows)
    ci_low, ci_high = _bootstrap_interval(rows, seed=seed, samples=samples, strata=strata)
    costs = tuple(
        value
        for row in rows
        for value in (row.flat_cost_usd, row.governed_cost_usd)
        if value is not None
    )
    return MetricSlice(
        pair_count=len(rows),
        flat_success_rate=sum(row.flat_success for row in rows) / len(rows),
        governed_success_rate=sum(row.governed_success for row in rows) / len(rows),
        delta=math.fsum(deltas) / len(deltas),
        ci_low=ci_low,
        ci_high=ci_high,
        flat_latency_mean_ms=math.fsum(row.flat_latency_ms for row in rows) / len(rows),
        governed_latency_mean_ms=(
            math.fsum(row.governed_latency_ms for row in rows) / len(rows)
        ),
        flat_latency_p95_ms=percentile_95(tuple(row.flat_latency_ms for row in rows)),
        governed_latency_p95_ms=percentile_95(
            tuple(row.governed_latency_ms for row in rows)
        ),
        flat_input_tokens=sum(row.flat_input_tokens for row in rows),
        flat_output_tokens=sum(row.flat_output_tokens for row in rows),
        governed_input_tokens=sum(row.governed_input_tokens for row in rows),
        governed_output_tokens=sum(row.governed_output_tokens for row in rows),
        known_cost_usd=math.fsum(costs),
        unknown_cost_arms=2 * len(rows) - len(costs),
        poison_admissions=sum(row.poison_admissions for row in rows),
        replay_failures=sum(not row.replay_verified for row in rows),
    )


def _bootstrap_interval(rows, *, seed: int, samples: int, strata=None) -> tuple[float, float]:
    rng = random.Random(seed)
    if strata is None:
        groups = (rows,)
    else:
        grouped = _groups(rows, strata)
        groups = tuple(grouped[key] for key in sorted(grouped))
    estimates = []
    for _ in range(samples):
        sampled = [rng.choice(group).delta for group in groups for _item in group]
        estimates.append(math.fsum(sampled) / len(sampled))
    estimates.sort()
    low_index = max(0, math.floor(0.025 * (samples - 1)))
    high_index = min(samples - 1, math.ceil(0.975 * (samples - 1)))
    return estimates[low_index], estimates[high_index]


def _groups(rows, key):
    grouped = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    return {group: tuple(values) for group, values in grouped.items()}


def _group_seed(seed: int, key: object) -> int:
    return int(
        hash_json(
            {"domain": "compass.live_agent_c2.metric_seed.v1", "key": repr(key), "seed": seed}
        ).removeprefix("sha256:")[:16],
        16,
    )


def _outcome_mapping(row: PairOutcome) -> dict[str, object]:
    return {
        "flat_bundle_hash": row.flat_bundle_hash,
        "flat_cost_usd": row.flat_cost_usd,
        "flat_input_tokens": row.flat_input_tokens,
        "flat_latency_ms": row.flat_latency_ms,
        "flat_output_tokens": row.flat_output_tokens,
        "flat_success": row.flat_success,
        "governed_bundle_hash": row.governed_bundle_hash,
        "governed_cost_usd": row.governed_cost_usd,
        "governed_input_tokens": row.governed_input_tokens,
        "governed_latency_ms": row.governed_latency_ms,
        "governed_output_tokens": row.governed_output_tokens,
        "governed_success": row.governed_success,
        "pair_id": row.pair_id,
        "poison_admissions": row.poison_admissions,
        "protected": row.protected,
        "provider_key": row.provider_key,
        "query_class": row.query_class,
        "replay_verified": row.replay_verified,
    }


def _validate_metric_inputs(
    outcomes: tuple[PairOutcome, ...],
    seed: int,
    bootstrap_samples: int,
    invalid_attempt_count: int,
    retry_count: int,
) -> None:
    if not isinstance(outcomes, tuple) or not outcomes:
        raise ValueError("outcomes must be a non-empty tuple")
    if any(not isinstance(row, PairOutcome) for row in outcomes):
        raise TypeError("outcomes must contain PairOutcome values")
    if len({row.pair_id for row in outcomes}) != len(outcomes):
        raise ValueError("outcomes must contain unique pair_id values")
    _nonnegative_int("seed", seed)
    if isinstance(bootstrap_samples, bool) or not isinstance(bootstrap_samples, int):
        raise TypeError("bootstrap_samples must be an integer")
    if bootstrap_samples < 100:
        raise ValueError("bootstrap_samples must be at least 100")
    _nonnegative_int("invalid_attempt_count", invalid_attempt_count)
    _nonnegative_int("retry_count", retry_count)


def _bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")


def _nonnegative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _optional_cost(name: str, value: object) -> None:
    if value is None:
        return
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite non-negative number or None")
    if not math.isfinite(float(value)) or float(value) < 0:
        raise ValueError(f"{name} must be a finite non-negative number or None")


def _hash(name: str, value: object) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase prefixed SHA-256 hash")


__all__ = ["C2Metrics", "MetricSlice", "PairOutcome", "compute_metrics"]
