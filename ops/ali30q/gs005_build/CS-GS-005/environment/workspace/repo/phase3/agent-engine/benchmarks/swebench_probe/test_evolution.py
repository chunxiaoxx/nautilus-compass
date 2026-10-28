"""Tests for the soul-fitness evolution selection rule (Probe 3 Task 1).

The heart of "evolution by external fitness": a candidate agent-prompt is accepted
ONLY if its resolve outcomes lopsidedly beat the current-best on the SAME probe
instances (escape-noise gate) AND its mean resolve-rate is higher. A single lucky
edit within noise is rejected — anti-Goodhart, anti-over-claim.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from evolution import EvolutionState, consider_candidate


def _items(pattern):
    """pattern: list of bool -> {iN: bool}."""
    return {f"i{n}": v for n, v in enumerate(pattern)}


def test_accepts_lopsided_better_candidate():
    # 6 instances the base fails, the candidate fixes all -> 6-0 discordant,
    # sign-test p=0.03125 < 0.05 -> escapes noise (the strict gate's bar).
    base = _items([False] * 6)                         # 0/6
    cand = _items([True] * 6)                          # 6/6
    st = EvolutionState(best_prompt="P0", best_score=0.0, history=[])
    accepted, st2 = consider_candidate(st, "P1", cand, base)
    assert accepted is True
    assert st2.best_prompt == "P1"
    assert st2.best_score > st.best_score
    assert len(st2.history) == 1


def test_rejects_within_noise_candidate():
    base = _items([True, False, True, False])
    cand = _items([False, True, False, True])          # 2/4 vs 2/4, 4 discordant evenly split
    st = EvolutionState(best_prompt="P0", best_score=0.5, history=[])
    accepted, st2 = consider_candidate(st, "P1", cand, base)
    assert accepted is False
    assert st2.best_prompt == "P0"                     # best unchanged
    assert st2.best_score == st.best_score
    assert len(st2.history) == 1                       # cycle recorded even on reject


def test_rejects_equal_or_worse_mean():
    base = _items([True] * 6 + [False] * 2)            # 6/8
    cand = _items([True] * 3 + [False] * 5)            # 3/8 worse
    st = EvolutionState(best_prompt="P0", best_score=0.75, history=[])
    accepted, st2 = consider_candidate(st, "P1", cand, base)
    assert accepted is False
    assert st2.best_prompt == "P0"


def test_history_records_delta_and_verdict():
    base = _items([False] * 8)
    cand = _items([True] * 8)
    st = EvolutionState(best_prompt="P0", best_score=0.0, history=[])
    _, st2 = consider_candidate(st, "P1", cand, base)
    h = st2.history[-1]
    assert h["accepted"] is True
    assert h["cand_mean"] == 1.0
    assert h["base_mean"] == 0.0
    assert "escapes_noise" in h
