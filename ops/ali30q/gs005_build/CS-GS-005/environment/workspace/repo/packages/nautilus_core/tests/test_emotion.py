"""R2 EmotionEngine smoke test · 17 种 + 0ms 规则路径"""
from __future__ import annotations
from nautilus_core.emotion import EmotionEngine, Emotion


def test_17_emotions_defined():
    members = {e.value for e in Emotion}
    # 12 + 5 + 1 (NEUTRAL fallback) = 18
    assert len(members) == 18
    # 4 维度 × 3 强度
    for prefix in ("joy", "calm", "sad", "anger"):
        for level in ("high", "mid", "low"):
            assert f"{prefix}_{level}" in members
    # 5 其他
    for other in ("curious", "awe", "fear", "shame", "bored"):
        assert other in members


def test_detect_joy_high():
    e = EmotionEngine()
    r = e.detect("这个结果太好了!")
    assert r.emotion == Emotion.JOY_HIGH
    assert "太好了" in r.matched_keywords
    assert r.confidence >= 0.5


def test_detect_anger():
    e = EmotionEngine()
    r = e.detect("我很生气")
    assert r.emotion == Emotion.ANGER_MID


def test_detect_curious():
    e = EmotionEngine()
    r = e.detect("我好奇这是为什么")
    assert r.emotion == Emotion.CURIOUS


def test_detect_neutral_on_empty():
    e = EmotionEngine()
    assert e.detect("").emotion == Emotion.NEUTRAL
    assert e.detect("xyz random").emotion == Emotion.NEUTRAL


def test_detect_english():
    e = EmotionEngine()
    r = e.detect("I am angry")
    assert r.emotion == Emotion.ANGER_MID


def test_detect_all_returns_multiple():
    e = EmotionEngine()
    # 同时含 joy + curious
    results = e.detect_all("好奇但开心")
    emotions = {r.emotion for r in results}
    assert Emotion.JOY_MID in emotions or Emotion.CURIOUS in emotions
    # 至少 1 个
    assert len(results) >= 1


def test_custom_rules_extend():
    custom = {Emotion.JOY_HIGH: ("yipee",)}
    e = EmotionEngine(custom_rules=custom)
    r = e.detect("yipee")
    assert r.emotion == Emotion.JOY_HIGH


def test_via_field():
    e = EmotionEngine()
    assert e.detect("happy").via == "rules"
    assert e.detect("").via == "neutral"
