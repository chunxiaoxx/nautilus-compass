"""S4 module 6 · recall_pkg/poi_weighting smoke tests."""
import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from recall_pkg.poi_weighting import (
    apply_poi_boost, boost_top_k,
    BOOST_FACTOR_DEFAULT, BOOST_CAP, BOOST_FLOOR,
)


def _make_memory(tmp: Path, name: str, cumulative_impact: str = "0") -> Path:
    p = tmp / name
    p.write_text(
        f"---\nname: {name}\ncumulative_impact: {cumulative_impact}\n---\nbody\n",
        encoding="utf-8",
    )
    return p


def test_1_zero_impact_no_change():
    out = apply_poi_boost(0.5, {"cumulative_impact": "0"})
    assert out == 0.5
    print("OK 1 zero impact no change")


def test_2_positive_impact_boost():
    # cumulative=2 · factor=0.1 → boost=0.2 → 0.5*1.2=0.6
    out = apply_poi_boost(0.5, {"cumulative_impact": "2"})
    assert abs(out - 0.6) < 1e-3
    print("OK 2 positive impact boosts")


def test_3_negative_impact_demote():
    # cumulative=-3 · factor=0.1 → boost=-0.3 → 0.5*0.7=0.35
    out = apply_poi_boost(0.5, {"cumulative_impact": "-3"})
    assert abs(out - 0.35) < 1e-3
    print("OK 3 negative impact demotes")


def test_4_boost_cap_2x():
    """Even huge cumulative caps at 2x base."""
    out = apply_poi_boost(0.5, {"cumulative_impact": "9999"})
    assert abs(out - 1.0) < 1e-3
    print("OK 4 boost cap at 2x base")


def test_5_boost_floor_half():
    """Huge negative caps at -0.5 boost → 0.5x base."""
    out = apply_poi_boost(0.5, {"cumulative_impact": "-9999"})
    assert abs(out - 0.25) < 1e-3
    print("OK 5 boost floor at 0.5x base")


def test_6_missing_field_no_change():
    out = apply_poi_boost(0.5, {})
    assert out == 0.5
    print("OK 6 missing field no change")


def test_7_corrupt_value_treated_zero():
    out = apply_poi_boost(0.5, {"cumulative_impact": "not_a_number"})
    assert out == 0.5
    print("OK 7 corrupt value graceful")


def test_8_boost_top_k_resort():
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        m1 = _make_memory(tmp, "high_impact.md", cumulative_impact="5")
        m2 = _make_memory(tmp, "low_impact.md", cumulative_impact="0")
        # Initial order: m2 wins by cosine
        entries = [(0.6, {"path": str(m2)}), (0.5, {"path": str(m1)})]
        out = boost_top_k(entries)
        # After boost · m1 should overtake (0.5 * 1.5 = 0.75 > 0.6 * 1.0 = 0.6)
        assert out[0][1]["path"] == str(m1)
    print("OK 8 boost_top_k re-sorts by boosted score")


def test_9_constants_match_spec():
    assert BOOST_FACTOR_DEFAULT == 0.1
    assert BOOST_CAP == 1.0
    assert BOOST_FLOOR == -0.5
    print("OK 9 constants match SPEC")


if __name__ == "__main__":
    tests = [test_1_zero_impact_no_change, test_2_positive_impact_boost,
             test_3_negative_impact_demote, test_4_boost_cap_2x,
             test_5_boost_floor_half, test_6_missing_field_no_change,
             test_7_corrupt_value_treated_zero, test_8_boost_top_k_resort,
             test_9_constants_match_spec]
    failures = []
    for t in tests:
        try:
            t()
        except Exception as e:
            failures.append((t.__name__, str(e)))
            print(f"FAIL {t.__name__}: {e}")
    if failures:
        sys.exit(1)
    print(f"\nOK {len(tests)}/{len(tests)} poi_weighting smoke pass")
