"""中心环 Q3 燃料率监控单测(2026-06-22)。"""
from __future__ import annotations

from services.distill_mint_runner import fuel_rate


def _rec(tid, strong, doubao, verified=True):
    return {"task_id": tid, "problem_statement": f"opt {tid}",
            "strong_solution": "def s(): ...",
            "strong_score": strong, "doubao_score": doubao,
            "strong_verified": verified}


def test_default_min_n_lowered_to_12_for_poc():
    # 首证阈值 20→12(ALE+qwen 真 A 类产率低·V5 估~10·用户拍 10-15·取 12)
    recs = [_rec(f"a{i}", 900.0, 100.0) for i in range(12)]
    r = fuel_rate(recs)   # 用默认 min_n
    assert r["min_n"] == 12
    assert r["enough_for_poc"] is True


def test_rate_and_enough():
    recs = [_rec(f"a{i}", 900.0, 100.0) for i in range(20)]  # 全 A 类
    r = fuel_rate(recs, min_n=20)
    assert r["a_bucket"] == 20
    assert r["a_rate"] == 1.0
    assert r["enough_for_poc"] is True


def test_not_enough_triggers_false():
    # 19 A 类 + 1 饱和拒 → 不够 min_n=20
    recs = [_rec(f"a{i}", 900.0, 100.0) for i in range(19)] + [_rec("sat", 850.0, 840.0)]
    r = fuel_rate(recs, min_n=20)
    assert r["a_bucket"] == 19
    assert r["rejected"] == 1
    assert r["enough_for_poc"] is False


def test_b_bucket_strong_unverified():
    recs = [_rec("x", 900.0, 100.0, verified=False)]
    r = fuel_rate(recs, min_n=20)
    assert r["b_bucket"] == 1
    assert r["a_bucket"] == 0
