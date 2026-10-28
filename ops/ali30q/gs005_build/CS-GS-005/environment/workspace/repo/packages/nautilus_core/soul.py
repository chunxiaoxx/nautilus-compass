"""R3 · 真实人格 SoulInstance class

V1 禅心源 · class 不是 prompt
悉达多 vs 云栖是 2 个 class · 不是 2 个 system_prompt 字符串

6 方法 cycle(V1 SoulInstance/YunqiSoul 真原型):
    perceive → recall → think → compose → express → reflect

每个 Persona(L3 应用层)继承 SoulInstance · override 6 方法
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Perception:
    """perceive() 输出 · agent 对当前情境的真感知"""
    raw_input: str
    context: dict[str, Any] = field(default_factory=dict)
    drift_score: float | None = None
    active_stakes: list[dict] = field(default_factory=list)
    timestamp_ms: int = 0


@dataclass
class Memory:
    """recall() 返回的单条 memory · top-K 形式"""
    content: str
    similarity: float
    source: str
    age_seconds: float
    emotion_tag: str | None = None


@dataclass
class Plan:
    """think() 输出 · agent 决定下一步行动"""
    intent: str
    tool_name: str | None = None
    tool_args: dict[str, Any] = field(default_factory=dict)
    reasoning: str = ""


@dataclass
class Output:
    """compose() 输出 · agent 准备表达的内容"""
    text: str
    tone: str = "neutral"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class Insight:
    """reflect() 输出 · agent 从 outcome 学到的教训"""
    lesson: str
    confidence: float
    rule_candidate: str | None = None


class SoulInstance:
    """L1 核心 · 灵魂基类 · 6 方法 cycle 接口

    Persona 子类必须实现全部 6 方法。基类提供 stub 让 import 不崩。
    """

    def __init__(self, agent_id: str, persona_name: str = "default"):
        self.agent_id = agent_id
        self.persona_name = persona_name

    def perceive(self, raw_input: str, context: dict | None = None) -> Perception:
        """感知 · 把外部输入转成结构化 Perception

        子类 override 加入:drift_check、active stake 查询、时戳等。
        """
        raise NotImplementedError(f"{self.persona_name} must implement perceive()")

    def recall(self, query: str, top_k: int = 5) -> list[Memory]:
        """召回 · 从长期记忆(compass/zenmind-mem)取 top-K"""
        raise NotImplementedError(f"{self.persona_name} must implement recall()")

    def think(self, perception: Perception, memories: list[Memory]) -> Plan:
        """思考 · LLM call · 基于感知 + 记忆决定 Plan"""
        raise NotImplementedError(f"{self.persona_name} must implement think()")

    def compose(self, plan: Plan) -> Output:
        """编织 · 把 Plan 转成可表达的 Output(文字 + tone)"""
        raise NotImplementedError(f"{self.persona_name} must implement compose()")

    def express(self, output: Output) -> str:
        """表达 · Output → 真发出的字符串(stdout/telegram/HTTP response)"""
        raise NotImplementedError(f"{self.persona_name} must implement express()")

    def reflect(self, output: Output, outcome: dict) -> Insight:
        """反思 · 看 outcome(成功/失败/score)蒸馏 Insight + rule_candidate"""
        raise NotImplementedError(f"{self.persona_name} must implement reflect()")
