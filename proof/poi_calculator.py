"""v1.7.1 · S4 module 2 · PoI deterministic impact score formula.

Formula (LLM-FREE · pure arithmetic):
  impact_score = outcome_weight * cite_factor * drift_penalty

  outcome_weight  = +1.0/+0.5/-0.5/0.0  for success/partial/failure/pending
  cite_factor     = min(1.0, len(cites) / 3.0)
  drift_penalty   = 1.0/0.5/0.1         for all-green/any-yellow/any-red

Reference: paper/SPEC_PROOF_OF_IMPACT.md section 4.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .poi_schema import ProofOfImpact
from .l1_grouper_compat import parse_session_frontmatter_safe

OUTCOME_WEIGHT = {
    "success": 1.0,
    "partial": 0.5,
    "failure": -0.5,
    "pending": 0.0,
}


def cite_factor(cited_count: int, max_credit_at: int = 3) -> float:
    """Spread credit across cites · n+ cites get full · single cite gets 1/n."""
    if cited_count <= 0:
        return 0.0
    return min(1.0, cited_count / float(max_credit_at))


def drift_penalty_from_paths(cited_paths: list, memory_root: Optional[Path] = None) -> float:
    """Read drift field from each cited memory frontmatter · return penalty multiplier.

    Returns: 1.0 if all green/none · 0.5 if any yellow · 0.1 if any red.
    Missing files default to 'none' (no penalty).
    """
    drifts = []
    for p in cited_paths:
        path = Path(p)
        if memory_root and not path.is_absolute():
            path = memory_root / path
        front = parse_session_frontmatter_safe(path)
        drifts.append(front.get("drift", "none").strip())
    if any(d == "red" for d in drifts):
        return 0.1
    if any(d == "yellow" for d in drifts):
        return 0.5
    return 1.0


def compute_impact_score(poi: ProofOfImpact, drift_penalty: float = 1.0) -> float:
    """Compute deterministic impact_score for a PoI event.

    Args:
        poi: ProofOfImpact instance (validated by dataclass post-init)
        drift_penalty: 1.0 / 0.5 / 0.1 (caller computes via drift_penalty_from_paths
                       or passes 1.0 if drift not yet checked)

    Returns:
        float in [-0.5, 1.0] · stored back to poi.impact_score
    """
    ow = OUTCOME_WEIGHT.get(poi.action_outcome, 0.0)
    cf = cite_factor(len(poi.cited_memory_paths))
    score = ow * cf * drift_penalty
    poi.impact_score = round(score, 4)
    return poi.impact_score


def compute_with_drift(poi: ProofOfImpact, memory_root: Optional[Path] = None) -> float:
    """Convenience · compute drift penalty from cited paths + impact score."""
    dp = drift_penalty_from_paths(poi.cited_memory_paths, memory_root=memory_root)
    return compute_impact_score(poi, drift_penalty=dp)
