"""Phase 2.I.1 · tier promotion calculator · TDD RED first.

Tiers (canonical agentmemory naming · ranked low→high):
  working → episodic → semantic → procedural

Promotion rule:
  cumulative_impact  >  1.0  → one tier up
  cumulative_impact  < -0.5  → one tier down
  otherwise                  → same tier
  top/bottom tiers clamp.

Finding G note (2026-05-30): plan §I.1 spec used "L1/L2/L3" tier names · those
do not exist in production (l2_distiller.py:138 hard-codes "semantic" ·
stop_hook v1.7.1 lifecycle hooks use working/episodic/semantic/procedural ·
those names are canonical). Tests below use canonical names and the
test_invalid_tier_raises check pins the plan misnomer as a hard-error case.
"""
import pytest


# --- Promote (impact > 1.0) ---

def test_promote_working_to_episodic():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="working", cumulative_impact=1.1) == "episodic"


def test_promote_episodic_to_semantic():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="episodic", cumulative_impact=1.5) == "semantic"


def test_promote_semantic_to_procedural():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="semantic", cumulative_impact=2.0) == "procedural"


def test_promote_clamped_at_procedural():
    """procedural is top · no further promotion regardless of impact."""
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="procedural", cumulative_impact=5.0) == "procedural"


# --- Demote (impact < -0.5) ---

def test_demote_episodic_to_working():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="episodic", cumulative_impact=-0.6) == "working"


def test_demote_semantic_to_episodic():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="semantic", cumulative_impact=-1.0) == "episodic"


def test_demote_procedural_to_semantic():
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="procedural", cumulative_impact=-2.0) == "semantic"


def test_demote_clamped_at_working():
    """working is bottom · no further demotion regardless of negative impact."""
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="working", cumulative_impact=-5.0) == "working"


# --- In-band (no change) ---

def test_in_band_positive_no_change():
    """0 ≤ impact ≤ 1.0 stays · boundary at 1.0 inclusive."""
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="semantic", cumulative_impact=0.5) == "semantic"
    assert calculate_new_tier(current_tier="episodic", cumulative_impact=1.0) == "episodic"
    assert calculate_new_tier(current_tier="working", cumulative_impact=0.0) == "working"


def test_in_band_negative_no_change():
    """-0.5 ≤ impact ≤ 0 stays · boundary at -0.5 inclusive."""
    from proof.tier_promotion import calculate_new_tier
    assert calculate_new_tier(current_tier="episodic", cumulative_impact=-0.4) == "episodic"
    assert calculate_new_tier(current_tier="semantic", cumulative_impact=-0.5) == "semantic"


# --- Invalid input ---

def test_invalid_tier_name_raises():
    """plan §I.1 used 'L2' · this is not a valid tier and must fail loud."""
    from proof.tier_promotion import calculate_new_tier
    with pytest.raises(ValueError, match="invalid tier"):
        calculate_new_tier(current_tier="L2", cumulative_impact=1.5)
    with pytest.raises(ValueError, match="invalid tier"):
        calculate_new_tier(current_tier="L3", cumulative_impact=1.5)
    with pytest.raises(ValueError, match="invalid tier"):
        calculate_new_tier(current_tier="", cumulative_impact=0.0)
    with pytest.raises(ValueError, match="invalid tier"):
        calculate_new_tier(current_tier="archived", cumulative_impact=0.0)
