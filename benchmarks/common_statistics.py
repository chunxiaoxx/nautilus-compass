"""Dependency-free statistics shared by offline Compass benchmarks."""

from __future__ import annotations

import math
from collections.abc import Sequence


def percentile_95(values: Sequence[float]) -> float:
    materialized = sorted(float(value) for value in values)
    if not materialized:
        raise ValueError("percentile requires at least one value")
    if any(not math.isfinite(value) for value in materialized):
        raise ValueError("percentile values must be finite")
    index = max(0, math.ceil(0.95 * len(materialized)) - 1)
    return materialized[index]


__all__ = ["percentile_95"]
