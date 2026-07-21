"""Runtime policy for lifecycle recall signals.

Default is guarded: PoI/tier signals must have enough support before they are
allowed to affect ranking. Set COMPASS_RECALL_SIGNAL_POLICY=raw only when a
fresh policy gate permits raw lifecycle promotion.
"""
from __future__ import annotations

import os
from typing import Mapping

try:
    from ..proof.poi_memory_key import memory_key_from_path
except (ImportError, ValueError):
    from proof.poi_memory_key import memory_key_from_path  # type: ignore

SIGNAL_POLICIES = ("raw", "guarded")
DEFAULT_SIGNAL_POLICY = "guarded"
DEFAULT_MIN_SIGNAL_COUNT = 3
DEFAULT_MIN_SIGNAL_FRACTION = 0.02


def get_recall_signal_policy(env: Mapping[str, str] | None = None) -> str:
    env = env if env is not None else os.environ
    value = (env.get("COMPASS_RECALL_SIGNAL_POLICY") or DEFAULT_SIGNAL_POLICY).strip().lower()
    return value if value in SIGNAL_POLICIES else DEFAULT_SIGNAL_POLICY


def _has_support(count: int, total: int, min_count: int, min_fraction: float) -> bool:
    if total <= 0:
        return False
    return count >= min_count and (count / total) >= min_fraction


def _entry_path(entry: dict) -> str:
    return str(entry.get("fullpath") or entry.get("path") or "")


def count_poi_support(top_entries: list, snapshot: dict) -> int:
    count = 0
    for _, entry in top_entries:
        if not isinstance(entry, dict):
            continue
        path = _entry_path(entry)
        key = memory_key_from_path(path) if path else None
        value = snapshot.get(key, 0.0) if key is not None else entry.get("cumulative_impact", 0.0)
        try:
            if float(value) != 0.0:
                count += 1
        except (TypeError, ValueError):
            continue
    return count


def count_tier_support(top_entries: list) -> int:
    count = 0
    for _, entry in top_entries:
        if isinstance(entry, dict) and entry.get("tier", "working") != "working":
            count += 1
    return count


def should_apply_poi_weight(
    policy: str,
    top_entries: list,
    snapshot: dict,
    *,
    min_signal_count: int = DEFAULT_MIN_SIGNAL_COUNT,
    min_signal_fraction: float = DEFAULT_MIN_SIGNAL_FRACTION,
) -> bool:
    if policy == "raw":
        return True
    count = count_poi_support(top_entries, snapshot)
    return _has_support(count, len(top_entries), min_signal_count, min_signal_fraction)


def should_apply_tier_weight(
    policy: str,
    top_entries: list,
    *,
    min_signal_count: int = DEFAULT_MIN_SIGNAL_COUNT,
    min_signal_fraction: float = DEFAULT_MIN_SIGNAL_FRACTION,
) -> bool:
    if policy == "raw":
        return True
    count = count_tier_support(top_entries)
    return _has_support(count, len(top_entries), min_signal_count, min_signal_fraction)
