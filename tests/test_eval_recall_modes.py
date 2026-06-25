#!/usr/bin/env python3
"""TDD · benchmark mode switch for eval_recall (D0 flat / D1 poi / D2 tier / D3 gemini).

Verifies the `rerank(mode, entries)` pure function actually switches ranking
behaviour per mode, using a tiny in-memory fixture (no embedder, no disk).
The metadata-driven re-rank is faithful to production:
  · poi  → apply_poi_boost_value (same value-path boost the snapshot recall uses)
  · tier → apply_tier_weight     (the lifecycle additive rank bonus)
  · gemini affects ONLY the upstream query, so its rerank == tier.
"""
from __future__ import annotations

import os
import sys
import pathlib

os.environ.setdefault("PYTHONUTF8", "1")
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tests.eval_recall import rerank  # noqa: E402


def _e(idx, impact=0.0, tier="working"):
    return {"idx": idx, "impact": impact, "tier": tier}


def _order(out):
    return [e["idx"] for _, e in out]


def test_flat_is_pure_cosine_ignoring_metadata():
    # idx0 has huge impact + top tier but LOWER cosine → flat must keep cosine order
    entries = [(0.50, _e(0, impact=99.0, tier="procedural")), (0.60, _e(1))]
    assert _order(rerank("flat", entries)) == [1, 0]


def test_poi_boosts_high_impact_above_higher_cosine():
    # idx0 lower cosine (0.50) but big impact 10.0 → boosted to ~1.0 > idx1 0.55
    entries = [(0.50, _e(0, impact=10.0)), (0.55, _e(1, impact=0.0))]
    assert _order(rerank("poi", entries))[0] == 0


def test_poi_noop_when_no_impact_equals_flat():
    entries = [(0.55, _e(1)), (0.50, _e(0))]
    assert _order(rerank("poi", entries)) == _order(rerank("flat", entries))


def test_tier_breaks_near_tie_by_lifecycle_rank():
    # equal cosine · idx1 higher tier (procedural) → idx1 ranks first
    entries = [(0.50, _e(0, tier="working")), (0.50, _e(1, tier="procedural"))]
    assert _order(rerank("tier", entries))[0] == 1


def test_gemini_rerank_identical_to_tier():
    entries = [(0.50, _e(0, tier="working")), (0.50, _e(1, tier="semantic"))]
    assert _order(rerank("gemini", entries)) == _order(rerank("tier", entries))


def test_unknown_mode_raises():
    try:
        rerank("bogus", [(0.5, _e(0))])
    except ValueError:
        return
    raise AssertionError("expected ValueError for unknown mode")
