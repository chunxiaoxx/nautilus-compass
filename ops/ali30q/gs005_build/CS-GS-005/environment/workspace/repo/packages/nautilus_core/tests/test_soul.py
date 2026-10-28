"""R3 SoulInstance smoke test · 验证骨架 import + 6 方法签名"""
from __future__ import annotations
import pytest
from nautilus_core.soul import (
    SoulInstance, Perception, Memory, Plan, Output, Insight,
)


def test_dataclasses_construct():
    p = Perception(raw_input="hello", timestamp_ms=1234)
    assert p.raw_input == "hello"
    assert p.context == {}
    m = Memory(content="x", similarity=0.9, source="zenmind", age_seconds=10)
    assert m.similarity == 0.9
    plan = Plan(intent="research")
    assert plan.tool_args == {}
    out = Output(text="reply")
    assert out.tone == "neutral"
    insight = Insight(lesson="be careful", confidence=0.7)
    assert insight.confidence == 0.7


def test_soul_instance_base():
    s = SoulInstance(agent_id="ag-1", persona_name="test")
    assert s.agent_id == "ag-1"
    assert s.persona_name == "test"


def test_soul_instance_methods_raise_not_implemented():
    """基类不实现 · 子类必须 override"""
    s = SoulInstance(agent_id="ag-1")
    with pytest.raises(NotImplementedError):
        s.perceive("hi")
    with pytest.raises(NotImplementedError):
        s.recall("q")
    with pytest.raises(NotImplementedError):
        s.think(Perception(raw_input=""), [])
    with pytest.raises(NotImplementedError):
        s.compose(Plan(intent=""))
    with pytest.raises(NotImplementedError):
        s.express(Output(text=""))
    with pytest.raises(NotImplementedError):
        s.reflect(Output(text=""), {})


def test_subclass_can_override():
    class MinimalPersona(SoulInstance):
        def perceive(self, raw_input, context=None):
            return Perception(raw_input=raw_input)
        def recall(self, query, top_k=5):
            return [Memory(content=query, similarity=0.5, source="stub", age_seconds=0)]
        def think(self, perception, memories):
            return Plan(intent="echo")
        def compose(self, plan):
            return Output(text=plan.intent)
        def express(self, output):
            return output.text
        def reflect(self, output, outcome):
            return Insight(lesson="ok", confidence=1.0)

    p = MinimalPersona(agent_id="ag-2", persona_name="minimal")
    perc = p.perceive("hi")
    mems = p.recall("hi")
    plan = p.think(perc, mems)
    out = p.compose(plan)
    expr = p.express(out)
    insight = p.reflect(out, {})
    assert expr == "echo"
    assert insight.confidence == 1.0
