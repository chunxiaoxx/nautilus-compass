"""R6 · 痛苦真驱动 · feel_think = 工具实际失败率(V3 helix/tension.py 移植)

V3 早期教训:feel_think 用关键词匹配 → 正反馈死循环(右脑说"痛苦" → 被扫描
→ 更痛苦)。修复后:pain 只反映真实工具失败率(`success=False` 比例)。

3 维:
- harmony: 0.0(全失败)→ 1.0(全成功)
- pain:    0.0(无痛)→ 1.0(全痛 · agent 应改方向)
- pace:    slow / normal / fast(基于 last N 调用平均耗时)

prompt 注入:`[pain 0.18(低) · harmony 0.82(高) · pace fast]` ≤ 30 token
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class TensionReading:
    harmony: float       # 0.0-1.0
    pain: float          # 0.0-1.0(= 1 - harmony · 显式存以便 prompt 注入)
    pace: str            # "slow" | "normal" | "fast"
    sample_size: int     # 实际采样 tool_call 数(≤ window)
    avg_elapsed_ms: float

    def prompt_hint(self) -> str:
        """≤ 30 token 紧凑形式 · 进 helix block prompt 注入"""
        h_label = "高" if self.harmony >= 0.7 else "中" if self.harmony >= 0.4 else "低"
        p_label = "低" if self.pain < 0.3 else "中" if self.pain < 0.6 else "高"
        return f"pain {self.pain:.2f}({p_label}) · harmony {self.harmony:.2f}({h_label}) · pace {self.pace}"


class ToolCallSource(Protocol):
    """抽象 tool_calls 数据源 · 解耦 PG · 便于测试"""
    def fetch_recent(self, agent_id: str, window: int) -> list[dict]:
        """返 list of dicts · 至少含 success(bool)+ elapsed_ms(int)"""
        ...


class TensionMeter:
    """L1 · 真张力测量 · 接 agent_tool_calls 表(或任何 ToolCallSource)"""

    SLOW_THRESHOLD_MS = 5000
    FAST_THRESHOLD_MS = 1500

    def __init__(self, agent_id: str, source: ToolCallSource, window: int = 50):
        self.agent_id = agent_id
        self.source = source
        self.window = window

    def measure(self) -> TensionReading:
        """从 source 取 last N · 算 success_rate / avg_elapsed / pace"""
        rows = self.source.fetch_recent(self.agent_id, self.window)
        if not rows:
            # 无数据 · 假设中性(harmony=0.5 · pace=normal)
            return TensionReading(
                harmony=0.5, pain=0.5, pace="normal", sample_size=0, avg_elapsed_ms=0.0
            )

        successes = sum(1 for r in rows if r.get("success"))
        harmony = successes / len(rows)
        pain = 1.0 - harmony

        elapsed_values = [r.get("elapsed_ms", 0) or 0 for r in rows]
        avg_elapsed = sum(elapsed_values) / len(elapsed_values) if elapsed_values else 0.0

        if avg_elapsed >= self.SLOW_THRESHOLD_MS:
            pace = "slow"
        elif avg_elapsed <= self.FAST_THRESHOLD_MS:
            pace = "fast"
        else:
            pace = "normal"

        return TensionReading(
            harmony=harmony, pain=pain, pace=pace,
            sample_size=len(rows), avg_elapsed_ms=avg_elapsed,
        )


class StaticToolCallSource:
    """测试用 · 静态 list 注入 · 不连 PG"""
    def __init__(self, rows: list[dict]):
        self._rows = rows

    def fetch_recent(self, agent_id: str, window: int) -> list[dict]:
        return self._rows[:window]
