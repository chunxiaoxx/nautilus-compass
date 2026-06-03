import math
from recall_pkg.poi_weighting import apply_poi_boost_value, boost_top_k_with_snapshot


def test_apply_value_basic():
    # cumulative=5 → boost=clamp(0.5)=0.5 → 0.8*1.5=1.2
    assert round(apply_poi_boost_value(0.8, 5.0), 4) == 1.2


def test_apply_value_clamp_cap():
    # cumulative=100 → boost capped at +1.0 → 0.5*2.0=1.0
    assert round(apply_poi_boost_value(0.5, 100.0), 4) == 1.0


def test_apply_value_clamp_floor():
    assert round(apply_poi_boost_value(0.5, -100.0), 4) == 0.25  # *0.5


def test_apply_value_nan_returns_base():
    assert apply_poi_boost_value(0.7, float("nan")) == 0.7
    assert apply_poi_boost_value(0.7, float("inf")) == 0.7


def test_boost_with_snapshot_reranks():
    snap = {"proj/hi.md": 5.0}
    top = [
        (0.50, {"path": "x", "fullpath": "/h/.claude/projects/proj/memory/lo.md"}),
        (0.45, {"path": "y", "fullpath": "/h/.claude/projects/proj/memory/hi.md"}),
    ]
    out = boost_top_k_with_snapshot(top, snap)
    # hi.md boosted 0.45*1.5=0.675 > lo.md 0.50 → reranked to top
    assert "hi.md" in out[0][1]["fullpath"]
