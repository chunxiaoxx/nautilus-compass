"""S4 module 2 · poi_calculator smoke tests · pure arithmetic."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from proof.poi_schema import ProofOfImpact
from proof.poi_calculator import (
    OUTCOME_WEIGHT, cite_factor,
    drift_penalty_from_paths, compute_impact_score, compute_with_drift,
)


def _poi(outcome="success", cites=None):
    return ProofOfImpact(
        action_id="b-test",
        agent_id="agent-1",
        cited_memory_paths=cites if cites is not None else ["s_1.md"],
        action_outcome=outcome,
        timestamp_action="2026-05-21T12:00:00Z",
        timestamp_outcome="2026-05-21T12:05:00Z",
    )


def test_1_outcome_weights():
    assert OUTCOME_WEIGHT["success"] == 1.0
    assert OUTCOME_WEIGHT["failure"] == -0.5
    assert OUTCOME_WEIGHT["partial"] == 0.5
    assert OUTCOME_WEIGHT["pending"] == 0.0
    print("OK 1 outcome weights match SPEC")


def test_2_cite_factor():
    assert cite_factor(0) == 0.0
    assert cite_factor(1) == 1/3.0
    assert cite_factor(3) == 1.0
    assert cite_factor(10) == 1.0  # capped
    print("OK 2 cite_factor SPEC §4")


def test_3_score_success_1_cite():
    poi = _poi(outcome="success", cites=["s_1.md"])
    score = compute_impact_score(poi)
    # success(+1.0) * cite_factor(1/3) * drift(1.0) = 0.3333
    assert abs(score - 1/3.0) < 1e-3
    assert poi.impact_score == score
    print("OK 3 success+1cite → 0.33")


def test_4_score_success_3_cites():
    poi = _poi(outcome="success", cites=["a.md", "b.md", "c.md"])
    score = compute_impact_score(poi)
    assert score == 1.0
    print("OK 4 success+3cites → 1.0")


def test_5_score_failure():
    poi = _poi(outcome="failure", cites=["a.md", "b.md"])
    score = compute_impact_score(poi)
    # -0.5 * 2/3 = -0.333
    assert abs(score + 1/3.0) < 1e-3
    print("OK 5 failure+2cites → -0.33")


def test_6_score_pending_zero():
    poi = _poi(outcome="pending", cites=["a.md", "b.md", "c.md", "d.md"])
    score = compute_impact_score(poi)
    assert score == 0.0
    print("OK 6 pending → 0.0")


def test_7_drift_penalty_red():
    with tempfile.TemporaryDirectory() as t:
        red = Path(t) / "red.md"
        red.write_text("---\nname: r\ndrift: red\n---\nbody", encoding="utf-8")
        green = Path(t) / "green.md"
        green.write_text("---\nname: g\ndrift: green\n---\nbody", encoding="utf-8")
        dp = drift_penalty_from_paths([str(red), str(green)])
        assert dp == 0.1
    print("OK 7 drift penalty red → 0.1")


def test_8_drift_penalty_yellow():
    with tempfile.TemporaryDirectory() as t:
        y = Path(t) / "y.md"
        y.write_text("---\nname: y\ndrift: yellow\n---\n", encoding="utf-8")
        dp = drift_penalty_from_paths([str(y)])
        assert dp == 0.5
    print("OK 8 drift penalty yellow → 0.5")


def test_9_drift_penalty_all_green():
    with tempfile.TemporaryDirectory() as t:
        g = Path(t) / "g.md"
        g.write_text("---\nname: g\ndrift: green\n---\n", encoding="utf-8")
        dp = drift_penalty_from_paths([str(g)])
        assert dp == 1.0
    print("OK 9 drift penalty all green → 1.0")


def test_10_compute_with_drift_red_penalty():
    with tempfile.TemporaryDirectory() as t:
        red = Path(t) / "r.md"
        red.write_text("---\ndrift: red\n---\n", encoding="utf-8")
        poi = _poi(outcome="success", cites=[str(red)])
        score = compute_with_drift(poi)
        # 1.0 * (1/3) * 0.1 = 0.0333
        assert abs(score - 0.0333) < 1e-3
    print("OK 10 compute_with_drift red penalty applied")


if __name__ == "__main__":
    tests = [test_1_outcome_weights, test_2_cite_factor, test_3_score_success_1_cite,
             test_4_score_success_3_cites, test_5_score_failure, test_6_score_pending_zero,
             test_7_drift_penalty_red, test_8_drift_penalty_yellow,
             test_9_drift_penalty_all_green, test_10_compute_with_drift_red_penalty]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} poi_calculator smoke pass")
