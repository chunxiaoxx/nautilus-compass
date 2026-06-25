"""GEP P1/P2 预备 — 结构化胶囊 schema。

给 compass 记忆胶囊的"裸 learning 行"加结构化边界字段(何时召回/在什么
环境验证过/置信度/失败边界),使召回的经验指导更精准(GEP 精度进化)。

GEP 复用决策 = B(对齐开源协议规范·非自创):开源 evolver
(github.com/EvoMap/evolver)是 Node CLI/GPL-3.0,不能 pip import。本模块按其
Capsule 数据模型规范在 Python 实现对应字段(字段命名/语义对齐),不碰 GPL 代码。

预备态:schema 纯 compass 侧定义。端到端生效 gated on V5 写端产结构化经验
+ serving 存这些字段。本模块只交 schema + 测试,不接 serving。

向后兼容:to_content() 必含裸 `learning` 键,老消费者只读 learning 仍工作;
新消费者额外读 triggers/env_fingerprint/confidence/when_not_to_use 边界字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StructuredCapsule:
    learning: str
    triggers: List[str] = field(default_factory=list)
    env_fingerprint: str = ""
    confidence: float = 1.0
    when_not_to_use: List[str] = field(default_factory=list)

    def to_content(self) -> dict:
        """序列化成 compass write_learning 的 content dict。

        向后兼容:必含 `learning` 键(裸正文)。其余结构化字段作附加键。
        """
        return {
            "learning": self.learning,
            "triggers": list(self.triggers),
            "env_fingerprint": self.env_fingerprint,
            "confidence": self.confidence,
            "when_not_to_use": list(self.when_not_to_use),
        }


def from_content(d: dict) -> StructuredCapsule:
    """从 content dict 反序列化(缺字段用默认),与 to_content round-trip。"""
    return StructuredCapsule(
        learning=d["learning"],
        triggers=list(d.get("triggers", [])),
        env_fingerprint=d.get("env_fingerprint", ""),
        confidence=d.get("confidence", 1.0),
        when_not_to_use=list(d.get("when_not_to_use", [])),
    )
