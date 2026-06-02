"""Phase 2.I.1 (2026-05-30) · tier promotion calculator · impact-based.

Companion to the access-based promote_after schema (see stop_hook.py
_TIER_DEFAULT_PROMOTE which counts access events). This module triggers tier
moves by cumulative_impact from PoI emissions · see
`proof/poi_emitter.py:update_frontmatter_cumulative` for where
cumulative_impact is incremented per memory file.

Tier ladder (low → high):
    working → episodic → semantic → procedural

Promotion rule (impact-based · this module):
    cumulative_impact >  PROMOTE_THRESHOLD (1.0)  → one tier up
    cumulative_impact < DEMOTE_THRESHOLD  (-0.5)  → one tier down
    otherwise                                      → unchanged
    top/bottom tiers clamp · no error.

Used by `scripts/tier_promotion_driver.py` (Task I.2 · daily cron).

Reference:
- docs/plans/2026-05-29-compass-comprehensive-uplift-implementation-plan.md §I.1
- Finding G (2026-05-30): plan §I.1 spec used "L1/L2/L3" tier names which
  do not exist in production. l2_distiller.py:138 hard-codes "semantic" ·
  v1.7.1 stop_hook lifecycle hooks (HOOK_DISPATCH _TIER_DEFAULT_PROMOTE) use
  working/episodic/semantic/procedural. Those are canonical. Invalid tier
  names (including "L1"/"L2"/"L3") raise ValueError.

NO LLM. Pure arithmetic.
"""
from __future__ import annotations

# Canonical tier ladder · low → high · agentmemory naming.
TIERS: tuple[str, ...] = ("working", "episodic", "semantic", "procedural")

# Threshold band · strict `>` and `<` so boundary values stay in current tier.
PROMOTE_THRESHOLD: float = 1.0
DEMOTE_THRESHOLD: float = -0.5


def calculate_new_tier(current_tier: str, cumulative_impact: float) -> str:
    """Return new tier given current tier and cumulative impact.

    Args:
        current_tier: one of TIERS (canonical agentmemory naming)
        cumulative_impact: float · running sum of PoI impact_score for the memory

    Returns:
        The new tier name (same as input if no threshold crossed · clamped at
        top/bottom of ladder).

    Raises:
        ValueError: if current_tier is not in TIERS · pins Finding G plan
                    misnomer (L1/L2/L3) as a hard-error case.
    """
    if current_tier not in TIERS:
        raise ValueError(
            f"invalid tier: {current_tier!r} "
            f"(must be one of {TIERS})"
        )
    idx = TIERS.index(current_tier)
    if cumulative_impact > PROMOTE_THRESHOLD:
        return TIERS[min(idx + 1, len(TIERS) - 1)]
    if cumulative_impact < DEMOTE_THRESHOLD:
        return TIERS[max(idx - 1, 0)]
    return current_tier
