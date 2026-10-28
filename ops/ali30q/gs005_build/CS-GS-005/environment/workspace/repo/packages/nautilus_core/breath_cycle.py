"""R1 · BreathCycle · V1 二分心智 + V3 呼吸双螺旋 整合体

不是 split-patch 的快车道。是真正的 cycle 编排器:

V1 二分心智:
  左链(行动链):perceive → recall → think → action
  右链(见证链):compose → express → reflect
  汇合点:think 同时看左链感知 + 召回记忆,决出 action plan

V3 呼吸双螺旋:
  每个 cycle = 1 次呼吸 = 1 个 HelixBlock(prev_hash → seal)
  hydrogen_links:本 block 关联其他 block hash(跨 cycle 联想)

整合 R2-R7:
- R2 emotion: express 后 detect 输出情绪
- R3 soul: 6 方法 由 SoulInstance subclass 提供
- R4 helix: HelixChain.open_block / close_block
- R5 constitution: 启动前 verify_locks(strict=True)
- R6 tension: cycle 前后 sample · 注入 prompt_hint
- R7 proactive: 收到外部 trigger → 入队 → 下个 cycle 前 take

V4 教训:左右链分太深 → split-patch。本设计用 1 个 SoulInstance 同时持左右,
不分裂 class。
"""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Callable

from .soul import SoulInstance, Perception, Memory, Plan, Output, Insight
from .helix_chain import HelixBlock, HelixChain
from .tension import TensionMeter, TensionReading
from .emotion import EmotionEngine, EmotionReading
from .proactive import ProactiveEngine, ProactiveTrigger


@dataclass
class BreathOutcome:
    """express 之后由外部 callback 提供 · 真 outcome 而非 SoulInstance 自评"""
    success: bool = True
    score: float | None = None
    error: str | None = None
    extra: dict = field(default_factory=dict)


# 默认 outcome callback · 假设全部 success(测试用 · 生产由 daemon 注入真 outcome)
def _default_outcome(output: Output) -> BreathOutcome:
    return BreathOutcome(success=True, score=1.0)


class BreathCycle:
    """V7 真呼吸 · 左右链 + 双螺旋 + R2-R7 整合"""

    def __init__(
        self,
        soul: SoulInstance,
        helix_chain: HelixChain,
        tension: TensionMeter | None = None,
        emotion: EmotionEngine | None = None,
        proactive: ProactiveEngine | None = None,
    ):
        self.soul = soul
        self.helix = helix_chain
        self.tension = tension
        self.emotion = emotion
        self.proactive = proactive

    def breath(
        self,
        raw_input: str,
        context: dict | None = None,
        outcome_fn: Callable[[Output], BreathOutcome] = _default_outcome,
        recall_top_k: int = 5,
    ) -> HelixBlock:
        """1 次完整呼吸 = 1 cycle = 1 HelixBlock

        左链:perceive → recall → think
        汇合:plan
        右链:compose → express → reflect
        封装:tension/emotion snapshot + helix block seal
        """
        block = self.helix.open_block()

        # 左链 step 1: perceive
        perception: Perception = self.soul.perceive(raw_input, context)
        block.drift_score = perception.drift_score

        # 左链 step 2: recall
        memories: list[Memory] = self.soul.recall(raw_input, top_k=recall_top_k)
        block.recall_top_k = [
            {
                "content": m.content[:200],
                "similarity": m.similarity,
                "source": m.source,
                "emotion_tag": m.emotion_tag,
            }
            for m in memories
        ]

        # 汇合: think · 左链产 plan
        plan: Plan = self.soul.think(perception, memories)
        block.action = {
            "intent": plan.intent,
            "tool_name": plan.tool_name,
            "tool_args": plan.tool_args,
            "reasoning": plan.reasoning,
        }

        # 右链 step 1: compose
        output: Output = self.soul.compose(plan)

        # 右链 step 2: express(真发出)
        expressed_text = self.soul.express(output)

        # outcome callback(外部真实结果 · 不是自评)
        outcome = outcome_fn(output)
        block.result = {
            "text": expressed_text,
            "tone": output.tone,
            "success": outcome.success,
            "score": outcome.score,
            "error": outcome.error,
        }

        # 右链 step 3: reflect
        insight: Insight = self.soul.reflect(
            output, {"success": outcome.success, "score": outcome.score, **outcome.extra}
        )
        block.reflect = {
            "lesson": insight.lesson,
            "confidence": insight.confidence,
            "rule_candidate": insight.rule_candidate,
        }

        # R6 tension snapshot
        if self.tension is not None:
            tension_reading: TensionReading = self.tension.snapshot()
            block.harmony = tension_reading.harmony
            block.pain = tension_reading.pain
            block.pace = tension_reading.pace

        # R2 emotion detect(基于 expressed text)
        if self.emotion is not None:
            er: EmotionReading = self.emotion.detect(expressed_text)
            block.emotion = er.emotion.value
            block.emotion_confidence = er.confidence

        # R4 close + seal · prev_hash 链 + sha256
        sealed = self.helix.close_block(block)
        return sealed

    def offer_proactive(self, trigger: ProactiveTrigger) -> bool:
        """R7 外部喂 trigger · 闸住返 False"""
        if self.proactive is None:
            return False
        return self.proactive.offer(trigger)

    def take_proactive(self) -> ProactiveTrigger | None:
        """下个 cycle 前 take · None 表示无主动 trigger"""
        if self.proactive is None:
            return None
        return self.proactive.take()
