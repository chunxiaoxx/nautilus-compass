"""C.2 · should_fire_drift multi-signal vote tests.

Verifies the new firing logic raises specificity over the old OR-vote:
  - strong score alone fires
  - strong neg-hit alone fires
  - weak signals must corroborate (both required)
  - legacy=True kwarg restores OR-vote semantics
"""
import sys
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from drift.firing import should_fire_drift


# ── Strong signals fire alone ──────────────────────────────────────
def test_strong_negative_score_fires_alone():
    assert should_fire_drift(score=-0.06, max_neg_hit=0.30) is True


def test_strong_neg_hit_fires_alone():
    assert should_fire_drift(score=0.05, max_neg_hit=0.72) is True


# ── Weak signals require corroboration ─────────────────────────────
def test_weak_score_alone_does_not_fire():
    """5/27 anti-pattern · score=-0.03 with no anti-anchor hit shouldn't alarm."""
    assert should_fire_drift(score=-0.03, max_neg_hit=0.30) is False


def test_weak_hit_alone_does_not_fire():
    """Single weak anti-anchor cosine shouldn't alarm without drift score."""
    assert should_fire_drift(score=0.00, max_neg_hit=0.55) is False


def test_weak_combo_fires():
    """Both weak signals together → fire (corroborated)."""
    # score=-0.03 ≤ WEAK_SCORE (-0.02) ✓ · hit=0.60 ≥ WEAK_HIT (0.56) ✓
    assert should_fire_drift(score=-0.03, max_neg_hit=0.60) is True


# ── Boundary inclusivity ───────────────────────────────────────────
def test_threshold_boundary_inclusive_score():
    """score == STRONG_SCORE fires (boundary inclusive)."""
    assert should_fire_drift(score=-0.05, max_neg_hit=0.0) is True


def test_threshold_boundary_inclusive_hit():
    """max_neg_hit == STRONG_HIT fires (boundary inclusive)."""
    assert should_fire_drift(score=0.0, max_neg_hit=0.70) is True


def test_below_all_thresholds_no_fire():
    """No signal strong enough · no corroborated weak → no fire."""
    assert should_fire_drift(score=-0.01, max_neg_hit=0.40) is False


# ── Legacy OR-vote A/B path ────────────────────────────────────────
def test_legacy_or_vote_via_kwarg():
    """legacy=True restores OR-vote semantics."""
    # Old logic: score < -0.032 OR max_neg_hit >= 0.538
    # score=-0.03 NOT < -0.032 · max_neg_hit=0.55 >= 0.538 ✓ → fire
    assert should_fire_drift(score=-0.03, max_neg_hit=0.55, legacy=True) is True
    # score=-0.04 < -0.032 ✓ → fire
    assert should_fire_drift(score=-0.04, max_neg_hit=0.30, legacy=True) is True
    # score=-0.01 NOT < -0.032 · max_neg_hit=0.40 NOT >= 0.538 → no fire
    assert should_fire_drift(score=-0.01, max_neg_hit=0.40, legacy=True) is False


# ── Plan §C.2 spec compatibility ───────────────────────────────────
def test_plan_spec_case_no_fire_at_minus_003_055():
    """Plan §C.2 negative case · score=-0.03 + max_neg_hit=0.55 → must NOT fire.

    With WEAK_HIT=0.56 default: max_neg_hit=0.55 < 0.56 · weak combo fails ·
    no other signal strong enough · no fire. ✓
    """
    assert should_fire_drift(score=-0.03, max_neg_hit=0.55) is False


def test_plan_spec_case_fires_at_minus_005_062():
    """Plan §C.2 positive case · score=-0.05 + max_neg_hit=0.62 → must fire.

    score=-0.05 ≤ STRONG_SCORE (-0.05) ✓ → fire on strong score alone.
    """
    assert should_fire_drift(score=-0.05, max_neg_hit=0.62) is True
