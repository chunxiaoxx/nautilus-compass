"""R1 BreathCycle smoke test · V1 二分心智 + V3 呼吸双螺旋整合体"""
from __future__ import annotations
from nautilus_core.breath_cycle import BreathCycle, BreathOutcome
from nautilus_core.soul import (
    SoulInstance, Perception, Memory, Plan, Output, Insight,
)
from nautilus_core.helix_chain import HelixChain, InMemoryStorage
from nautilus_core.emotion import EmotionEngine
from nautilus_core.proactive import ProactiveEngine, ProactiveTrigger


class StubSoul(SoulInstance):
    """测试用 stub · 6 方法返固定值"""

    def perceive(self, raw_input, context=None):
        return Perception(
            raw_input=raw_input, context=context or {},
            drift_score=0.15, timestamp_ms=1000,
        )

    def recall(self, query, top_k=5):
        return [
            Memory(content="过去类似经验", similarity=0.8, source="zenmind", age_seconds=3600, emotion_tag="curious"),
            Memory(content="另一条记忆", similarity=0.6, source="zenmind", age_seconds=7200),
        ]

    def think(self, perception, memories):
        return Plan(
            intent="回应用户",
            tool_name="reply",
            tool_args={"text": "ok"},
            reasoning="基于召回的记忆,回复"
        )

    def compose(self, plan):
        return Output(text="好的,我明白了。", tone="calm")

    def express(self, output):
        return output.text

    def reflect(self, output, outcome):
        return Insight(
            lesson="保持简洁回答",
            confidence=0.7,
            rule_candidate="if user asks brief → reply brief"
        )


def test_breath_returns_sealed_block():
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    cycle = BreathCycle(soul=soul, helix_chain=helix)
    block = cycle.breath("你好")
    assert block.hash != ""
    assert len(block.hash) == 64
    assert block.cycle_num == 0


def test_breath_left_chain_fields():
    """左链 perceive/recall/think 真填进 block"""
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    cycle = BreathCycle(soul=soul, helix_chain=helix)
    block = cycle.breath("hi")
    # perceive 填 drift
    assert block.drift_score == 0.15
    # recall 填 top_k
    assert len(block.recall_top_k) == 2
    assert block.recall_top_k[0]["similarity"] == 0.8
    # think 填 action
    assert block.action["intent"] == "回应用户"
    assert block.action["tool_name"] == "reply"


def test_breath_right_chain_fields():
    """右链 compose/express/reflect 真填进 block"""
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    cycle = BreathCycle(soul=soul, helix_chain=helix)
    block = cycle.breath("hi")
    # compose + express
    assert block.result["text"] == "好的,我明白了。"
    assert block.result["tone"] == "calm"
    # outcome callback
    assert block.result["success"] is True
    # reflect
    assert block.reflect["lesson"] == "保持简洁回答"
    assert block.reflect["rule_candidate"] is not None


def test_breath_with_emotion_engine():
    """R2 整合 · expressed text 触发 emotion detect"""
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    emotion = EmotionEngine()
    cycle = BreathCycle(soul=soul, helix_chain=helix, emotion=emotion)
    block = cycle.breath("hi")
    # "好的,我明白了。" 含"好的" → joy_low keyword "ok"? 试一下
    # Soul 输出 "好的,我明白了。" lower = "好的,我明白了。" → 不命中 "好的" 因为是中文
    # 不过 "ok" 也不命中 · 应该 neutral
    assert block.emotion in ("neutral", "joy_low", "joy_mid", "joy_high", "calm_mid")
    assert isinstance(block.emotion_confidence, float)


def test_breath_outcome_fn_writes_failure():
    """outcome_fn 注入失败时 · result.success = False"""
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    cycle = BreathCycle(soul=soul, helix_chain=helix)

    def fail_outcome(output):
        return BreathOutcome(success=False, score=0.0, error="tool timeout")

    block = cycle.breath("hi", outcome_fn=fail_outcome)
    assert block.result["success"] is False
    assert block.result["error"] == "tool timeout"


def test_multi_breath_links_chain():
    """连续 3 cycle · prev_hash 真链上"""
    soul = StubSoul(agent_id="test-1")
    storage = InMemoryStorage()
    helix = HelixChain(agent_id="test-1", storage=storage)
    cycle = BreathCycle(soul=soul, helix_chain=helix)
    blocks = [cycle.breath(f"input {i}") for i in range(3)]
    assert blocks[0].cycle_num == 0
    assert blocks[1].cycle_num == 1
    assert blocks[2].cycle_num == 2
    assert blocks[1].prev_hash == blocks[0].hash
    assert blocks[2].prev_hash == blocks[1].hash
    # verify integrity
    ok, viol = helix.verify_integrity()
    assert ok, f"violations: {viol}"


def test_proactive_offer_take_through_cycle():
    """R7 整合 · proactive trigger 入队/出队"""
    soul = StubSoul(agent_id="test-1")
    helix = HelixChain(agent_id="test-1", storage=InMemoryStorage())
    proactive = ProactiveEngine(rate_capacity=10, rate_refill_per_sec=10, cooldown_sec=0.0)
    cycle = BreathCycle(soul=soul, helix_chain=helix, proactive=proactive)

    assert cycle.offer_proactive(ProactiveTrigger(kind="evt", priority=5))
    t = cycle.take_proactive()
    assert t is not None
    assert t.kind == "evt"
    # 无 proactive 时 take 返 None
    cycle2 = BreathCycle(soul=soul, helix_chain=helix)
    assert cycle2.take_proactive() is None
