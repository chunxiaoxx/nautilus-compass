"""R2 · 情绪引擎 17 种 · 0ms 规则路径(V1 禅心移植 · emotion-recognition.ts)

V1 教训:LLM-only emotion 太慢(>500ms)+ 不稳。禅心方案:**双路径**
- 主路径:0ms 规则引擎(关键词 + 模式匹配)· 立即返
- 副路径:LLM fire-and-forget 缓存(异步 · 下次同 query 命中)

17 种(4 维度 × 3 强度 + 5 其他):
    愉悦/平静/低落/愤怒 × 强/中/弱   →  12 种
    其他:好奇/敬畏/恐惧/羞愧/无聊  →   5 种
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class Emotion(Enum):
    # 4 维度 × 3 强度
    JOY_HIGH = "joy_high"           # 愉悦.强
    JOY_MID = "joy_mid"             # 愉悦.中
    JOY_LOW = "joy_low"             # 愉悦.弱
    CALM_HIGH = "calm_high"         # 平静.强
    CALM_MID = "calm_mid"           # 平静.中
    CALM_LOW = "calm_low"           # 平静.弱
    SAD_HIGH = "sad_high"           # 低落.强
    SAD_MID = "sad_mid"             # 低落.中
    SAD_LOW = "sad_low"             # 低落.弱
    ANGER_HIGH = "anger_high"       # 愤怒.强
    ANGER_MID = "anger_mid"         # 愤怒.中
    ANGER_LOW = "anger_low"         # 愤怒.弱
    # 5 其他
    CURIOUS = "curious"             # 好奇
    AWE = "awe"                     # 敬畏
    FEAR = "fear"                   # 恐惧
    SHAME = "shame"                 # 羞愧
    BORED = "bored"                 # 无聊
    # fallback
    NEUTRAL = "neutral"             # 中性 · 无信号


@dataclass(frozen=True)
class EmotionReading:
    emotion: Emotion
    confidence: float       # 0.0-1.0
    matched_keywords: tuple[str, ...]
    via: str = "rules"      # "rules" | "llm" | "neutral"


# 关键词 → 情绪映射(中英混 · 简洁版 · L3 应用层可扩展)
RULES: dict[Emotion, tuple[str, ...]] = {
    Emotion.JOY_HIGH:   ("太好了", "棒极了", "amazing", "ecstatic", "love it"),
    Emotion.JOY_MID:    ("开心", "happy", "great", "高兴", "yay"),
    Emotion.JOY_LOW:    ("还行", "ok", "不错", "fine", "decent"),
    Emotion.CALM_HIGH:  ("非常平静", "deeply calm", "至静", "serene"),
    Emotion.CALM_MID:   ("平静", "calm", "稳", "steady"),
    Emotion.CALM_LOW:   ("一般", "meh", "平平"),
    Emotion.SAD_HIGH:   ("绝望", "崩溃", "devastated", "hopeless"),
    Emotion.SAD_MID:    ("难过", "sad", "失落", "depressed"),
    Emotion.SAD_LOW:    ("有点失望", "disappointed", "微伤"),
    Emotion.ANGER_HIGH: ("怒", "愤怒", "furious", "气炸了", "outrage"),
    Emotion.ANGER_MID:  ("生气", "angry", "烦", "annoyed"),
    Emotion.ANGER_LOW:  ("不爽", "uneasy", "微恼"),
    Emotion.CURIOUS:    ("好奇", "想知道", "curious", "wonder", "为什么"),
    Emotion.AWE:        ("敬畏", "awe", "wow", "震撼"),
    Emotion.FEAR:       ("害怕", "恐惧", "scared", "afraid", "worried"),
    Emotion.SHAME:      ("羞愧", "ashamed", "尴尬", "embarrassed"),
    Emotion.BORED:      ("无聊", "bored", "乏味", "tedious"),
}


class EmotionEngine:
    """0ms 规则路径 · LLM 异步缓存留 R2.2 后续"""

    def __init__(self, custom_rules: dict[Emotion, tuple[str, ...]] | None = None):
        self.rules = {**RULES, **(custom_rules or {})}

    def detect(self, text: str) -> EmotionReading:
        """0ms 规则匹配 · 返第一命中 + 命中关键词数为 confidence 输入"""
        if not text:
            return EmotionReading(Emotion.NEUTRAL, 0.0, (), via="neutral")
        lower = text.lower()
        best: tuple[Emotion, list[str]] | None = None
        for emotion, kws in self.rules.items():
            hits = [kw for kw in kws if kw.lower() in lower]
            if not hits:
                continue
            if best is None or len(hits) > len(best[1]):
                best = (emotion, hits)
        if best is None:
            return EmotionReading(Emotion.NEUTRAL, 0.0, (), via="neutral")
        emotion, hits = best
        confidence = min(1.0, 0.3 + 0.2 * len(hits))
        return EmotionReading(emotion, confidence, tuple(hits), via="rules")

    def detect_all(self, text: str, threshold: float = 0.3) -> list[EmotionReading]:
        """返 ≥ threshold 的所有命中 · 用于多情绪并存场景"""
        if not text:
            return []
        lower = text.lower()
        results = []
        for emotion, kws in self.rules.items():
            hits = [kw for kw in kws if kw.lower() in lower]
            if not hits:
                continue
            confidence = min(1.0, 0.3 + 0.2 * len(hits))
            if confidence >= threshold:
                results.append(EmotionReading(emotion, confidence, tuple(hits), via="rules"))
        return sorted(results, key=lambda r: -r.confidence)
