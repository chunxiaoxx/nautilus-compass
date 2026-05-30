"""C.2 · Drift firing decision · multi-signal vote · raises specificity.

Replaces inline OR-vote firing logic (sig < -0.032 OR max_neg_hit >= 0.538)
that was in recall.py:1429 and daemon.py:457. The old OR-vote led to the
estimated ~90% FP rate observed 2026-05-27 (457 alerts fired · only 2
manually marked FP · agents tuned out → detection ≠ intervention).

Multi-signal vote semantics:
  Strong single signal → fire
    score <= STRONG_SCORE (-0.05)        → fire (severe drift)
    max_neg_hit >= STRONG_HIT (0.70)     → fire (clear anti-anchor hit)
  Weak combo signal → fire
    score <= WEAK_SCORE (-0.02) AND
    max_neg_hit >= WEAK_HIT (0.56)       → fire (corroborated weak)
  Otherwise → no fire

Defaults chosen to approximate <5% FP rate per 5/27 design intent.

WEAK_HIT tuned to 0.56 (slightly above the old NEG_ANCHOR_HIT_THRESHOLD
0.538) so that a borderline weak case (score=-0.03, max_neg_hit=0.55)
does NOT fire under the new vote · this is the canonical plan §C.2
negative spec case. Choice of 0.56 (vs alternative WEAK_SCORE=-0.04)
keeps the weak_score boundary close to the historical -0.032 alert
threshold so we lose minimal genuine weak-drift detection.

Env vars override:
  COMPASS_DRIFT_STRONG_SCORE  default -0.05
  COMPASS_DRIFT_STRONG_HIT    default 0.70
  COMPASS_DRIFT_WEAK_SCORE    default -0.02
  COMPASS_DRIFT_WEAK_HIT      default 0.56

Set COMPASS_DRIFT_LEGACY_OR=1 to fall back to old OR-vote (for A/B testing).
"""
import os

STRONG_SCORE = float(os.environ.get("COMPASS_DRIFT_STRONG_SCORE", "-0.05"))
STRONG_HIT = float(os.environ.get("COMPASS_DRIFT_STRONG_HIT", "0.70"))
WEAK_SCORE = float(os.environ.get("COMPASS_DRIFT_WEAK_SCORE", "-0.02"))
WEAK_HIT = float(os.environ.get("COMPASS_DRIFT_WEAK_HIT", "0.56"))
LEGACY = os.environ.get("COMPASS_DRIFT_LEGACY_OR") == "1"


def should_fire_drift(score: float, max_neg_hit: float,
                      strong_score: float = None, strong_hit: float = None,
                      weak_score: float = None, weak_hit: float = None,
                      legacy: bool = None) -> bool:
    """Multi-signal drift firing vote.

    Args:
        score: drift score (negative = misaligned · range roughly [-1, 1])
        max_neg_hit: highest cosine to any negative anchor (range [0, 1])
        strong_score, strong_hit, weak_score, weak_hit: per-call overrides
            (None → use module-level defaults from env)
        legacy: if True (or None and COMPASS_DRIFT_LEGACY_OR=1), use the
            old OR-vote semantics for A/B comparison

    Returns:
        True if should fire drift alert · False otherwise.
    """
    if (legacy if legacy is not None else LEGACY):
        # Legacy OR-vote · for A/B comparison only
        return score <= -0.032 or max_neg_hit >= 0.538
    ss = strong_score if strong_score is not None else STRONG_SCORE
    sh = strong_hit if strong_hit is not None else STRONG_HIT
    ws = weak_score if weak_score is not None else WEAK_SCORE
    wh = weak_hit if weak_hit is not None else WEAK_HIT
    if score <= ss:
        return True
    if max_neg_hit >= sh:
        return True
    if score <= ws and max_neg_hit >= wh:
        return True
    return False
