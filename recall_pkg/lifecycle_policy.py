"""Runtime policy for lifecycle recall signals.

Default is flat: PoI/tier signals are recorded but do not affect ranking until
a fresh policy gate recommends guarded or raw.
"""
from __future__ import annotations

import os
import re
from typing import Mapping

try:
    from ..proof.poi_memory_key import memory_key_from_path
except (ImportError, ValueError):
    from proof.poi_memory_key import memory_key_from_path  # type: ignore

SIGNAL_POLICIES = ("flat", "raw", "guarded", "routed")
DEFAULT_SIGNAL_POLICY = "flat"
DEFAULT_MIN_SIGNAL_COUNT = 3
DEFAULT_MIN_SIGNAL_FRACTION = 0.02
LIFECYCLE_QUERY_PATTERNS = (
    r"\bbenchmark\b",
    r"\bbench\b",
    r"\bpolicy[-_ ]?gate\b",
    r"\bpreflight\b",
    r"\brelease\b",
    r"\boutcome\b",
    r"\bexecution\b",
    r"\bdogfood\b",
    r"\brecall\b",
    r"\blifecycle\b",
    r"\bC[0-9]+\b",
)


def get_recall_signal_policy(env: Mapping[str, str] | None = None) -> str:
    env = env if env is not None else os.environ
    value = (env.get("COMPASS_RECALL_SIGNAL_POLICY") or DEFAULT_SIGNAL_POLICY).strip().lower()
    return value if value in SIGNAL_POLICIES else DEFAULT_SIGNAL_POLICY


def _has_support(count: int, total: int, min_count: int, min_fraction: float) -> bool:
    if total <= 0:
        return False
    return count >= min_count and (count / total) >= min_fraction


def is_lifecycle_query(query: str | None) -> bool:
    text = (query or "").strip()
    if not text:
        return False
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in LIFECYCLE_QUERY_PATTERNS)


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
    query: str | None = None,
    min_signal_count: int = DEFAULT_MIN_SIGNAL_COUNT,
    min_signal_fraction: float = DEFAULT_MIN_SIGNAL_FRACTION,
) -> bool:
    if policy == "flat":
        return False
    if policy == "raw":
        return True
    if policy == "routed" and not is_lifecycle_query(query):
        return False
    count = count_poi_support(top_entries, snapshot)
    return _has_support(count, len(top_entries), min_signal_count, min_signal_fraction)


def should_apply_tier_weight(
    policy: str,
    top_entries: list,
    *,
    query: str | None = None,
    min_signal_count: int = DEFAULT_MIN_SIGNAL_COUNT,
    min_signal_fraction: float = DEFAULT_MIN_SIGNAL_FRACTION,
) -> bool:
    if policy == "flat":
        return False
    if policy == "raw":
        return True
    if policy == "routed" and not is_lifecycle_query(query):
        return False
    count = count_tier_support(top_entries)
    return _has_support(count, len(top_entries), min_signal_count, min_signal_fraction)
