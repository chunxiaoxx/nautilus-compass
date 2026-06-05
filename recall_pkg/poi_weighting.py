"""v1.7.1 · S4 module 6 · PoI weighting · recall ranking boost from cumulative impact.

Memories with positive cumulative_impact are boosted in recall rank.
Memories with negative cumulative_impact are demoted (caused failures).

Asymptotic boost · capped to prevent unbounded ranking takeover.
NO LLM. Pure arithmetic.

Reference: paper/SPEC_PROOF_OF_IMPACT.md section 7.
"""
from __future__ import annotations

import math

try:
    from ..proof.l1_grouper_compat import parse_session_frontmatter_safe
except (ImportError, ValueError):
    from proof.l1_grouper_compat import parse_session_frontmatter_safe  # type: ignore

try:
    from ..proof.poi_memory_key import memory_key_from_path
except (ImportError, ValueError):
    from proof.poi_memory_key import memory_key_from_path  # type: ignore

BOOST_FACTOR_DEFAULT = 0.1
BOOST_CAP = 1.0  # max +1.0 → result = base × 2.0
BOOST_FLOOR = -0.5  # min -0.5 → result = base × 0.5


def _parse_cumulative_impact(frontmatter: dict) -> float:
    try:
        return float(frontmatter.get("cumulative_impact", "0") or 0)
    except (ValueError, TypeError):
        return 0.0


def apply_poi_boost(cosine_score: float, memory_frontmatter: dict,
                    boost_factor: float = BOOST_FACTOR_DEFAULT) -> float:
    """Boost cosine score by memory's cumulative_impact · capped asymptotically.

    Args:
        cosine_score: base recall score (0.0-1.0 typically)
        memory_frontmatter: dict from parse_session_frontmatter_safe
        boost_factor: multiplier on cumulative_impact (default 0.1)

    Returns:
        boosted_score = cosine_score × (1.0 + clamped_boost)
        Where clamped_boost ∈ [BOOST_FLOOR, BOOST_CAP]
    """
    cumulative = _parse_cumulative_impact(memory_frontmatter)
    boost = max(BOOST_FLOOR, min(BOOST_CAP, cumulative * boost_factor))
    return cosine_score * (1.0 + boost)


def boost_top_k(top_entries: list, boost_factor: float = BOOST_FACTOR_DEFAULT) -> list:
    """Re-rank a top-K list by applying PoI boost to each entry's score.

    Args:
        top_entries: list of (score, entry_dict) where entry has 'path' field

    Returns:
        Re-sorted list of (boosted_score, entry_dict) descending
    """
    boosted = []
    for score, entry in top_entries:
        if not isinstance(entry, dict):
            boosted.append((score, entry))
            continue
        path = entry.get("path", "")
        if not path:
            boosted.append((score, entry))
            continue
        front = parse_session_frontmatter_safe(path)
        new_score = apply_poi_boost(score, front, boost_factor=boost_factor)
        boosted.append((new_score, entry))
    boosted.sort(key=lambda x: x[0], reverse=True)
    return boosted


def apply_poi_boost_value(cosine_score: float, cumulative: float,
                          boost_factor: float = BOOST_FACTOR_DEFAULT) -> float:
    """Boost from a raw cumulative value (snapshot path). NaN/inf-safe."""
    if not math.isfinite(cumulative):
        return cosine_score
    boost = max(BOOST_FLOOR, min(BOOST_CAP, cumulative * boost_factor))
    out = cosine_score * (1.0 + boost)
    return out if math.isfinite(out) else cosine_score


def boost_top_k_with_snapshot(top_entries: list, snapshot: dict,
                              boost_factor: float = BOOST_FACTOR_DEFAULT) -> list:
    """Re-rank using central-credit snapshot dict (memory_key -> cumulative).
    Miss → fall back to frontmatter read (transition). Never raises."""
    boosted = []
    for score, entry in top_entries:
        if not isinstance(entry, dict):
            boosted.append((score, entry))
            continue
        path = entry.get("fullpath") or entry.get("path") or ""
        mk = memory_key_from_path(path) if path else None
        if mk is not None and mk in snapshot:
            new_score = apply_poi_boost_value(score, snapshot[mk], boost_factor)
        else:
            front = parse_session_frontmatter_safe(path) if path else {}
            new_score = apply_poi_boost(score, front, boost_factor=boost_factor)
        boosted.append((new_score, entry))
    boosted.sort(key=lambda x: x[0], reverse=True)
    return boosted
