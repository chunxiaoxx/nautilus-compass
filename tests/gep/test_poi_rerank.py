import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from gep.poi_rerank import rerank_by_impact


def test_rerank_hits_by_impact_then_reward():
    hits = [
        {"item_id": "a", "reason": "low",  "reward": 1.0, "cumulative_impact": 0.1},
        {"item_id": "b", "reason": "high", "reward": 1.0, "cumulative_impact": 0.9},
    ]
    out = rerank_by_impact(hits)
    assert out[0]["item_id"] == "b"      # 高 impact 优先


def test_rerank_reward_as_tiebreak():
    hits = [
        {"item_id": "a", "reward": 0.5, "cumulative_impact": 0.5},
        {"item_id": "b", "reward": 1.0, "cumulative_impact": 0.5},
    ]
    assert rerank_by_impact(hits)[0]["item_id"] == "b"   # 同 impact·高 reward 先


def test_rerank_missing_fields_safe():
    assert rerank_by_impact([]) == []
    assert rerank_by_impact([{"item_id": "x", "reason": "r"}])[0]["item_id"] == "x"


def test_rerank_stable_for_equal_scores():
    # 同 impact 同 reward → 稳定排序保持原序
    hits = [
        {"item_id": "a", "reward": 0.5, "cumulative_impact": 0.5},
        {"item_id": "b", "reward": 0.5, "cumulative_impact": 0.5},
        {"item_id": "c", "reward": 0.5, "cumulative_impact": 0.5},
    ]
    out = rerank_by_impact(hits)
    assert [h["item_id"] for h in out] == ["a", "b", "c"]


def test_rerank_non_numeric_fields_coerced_to_zero():
    # 非数值字段不崩，当 0 处理
    hits = [
        {"item_id": "a", "reward": "bad", "cumulative_impact": None},
        {"item_id": "b", "reward": 1.0, "cumulative_impact": 0.5},
    ]
    out = rerank_by_impact(hits)
    assert out[0]["item_id"] == "b"   # b 有真实分数排前，a 当 0


def test_rerank_does_not_mutate_input_dicts():
    hits = [
        {"item_id": "a", "reward": 1.0, "cumulative_impact": 0.1},
        {"item_id": "b", "reward": 1.0, "cumulative_impact": 0.9},
    ]
    snapshot = [dict(h) for h in hits]
    rerank_by_impact(hits)
    assert hits == snapshot   # 原 dict 内容不变


def test_rerank_never_raises_on_garbage():
    # 极端非法输入也不抛
    assert rerank_by_impact([{}]) == [{}]
    weird = [{"cumulative_impact": float("nan")}, {"item_id": "ok", "cumulative_impact": 0.5}]
    out = rerank_by_impact(weird)
    assert len(out) == 2
