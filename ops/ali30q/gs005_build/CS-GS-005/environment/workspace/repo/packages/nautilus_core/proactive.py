"""R7 · 主动性 design pattern · event-driven + priority + rate limit + cooldown

不是节气推送 · 是 agent 自决何时主动出声(L1 core · L3 应用层定 trigger 类型)。

核心:
- ProactiveTrigger: kind/priority/payload · 一次潜在主动事件
- ProactiveEngine: offer(入队检查) + take(出队最优) + has_pending
- RateLimiter: token bucket · 单位时间最多 N 次主动
- Cooldown: 同 kind 在 X 秒内不重复

V4 教训:主动 = 噪音生产机。设计闸:rate + priority + cooldown 三道。
"""
from __future__ import annotations
import heapq
import time
from dataclasses import dataclass, field
from typing import Any


@dataclass(order=True)
class ProactiveTrigger:
    """一次潜在主动事件 · order 用 -priority 实现 max-heap"""
    sort_key: float = field(init=False, repr=False)
    kind: str = ""                    # "watcher_event" / "timer_tick" / "user_inactive" / "low_balance" 等
    priority: int = 0                 # 越高越先 · 0-100
    payload: dict = field(default_factory=dict)
    enqueued_at: float = field(default_factory=time.time)

    def __post_init__(self):
        # heapq 是 min-heap · 用 -priority 实现 max-heap; 同 priority 则 enqueue 早的先
        self.sort_key = (-self.priority, self.enqueued_at)


class TokenBucket:
    """token bucket rate limiter"""
    def __init__(self, capacity: int, refill_per_sec: float):
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = float(capacity)
        self.last = time.time()

    def try_take(self, n: int = 1) -> bool:
        now = time.time()
        elapsed = now - self.last
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)
        self.last = now
        if self.tokens >= n:
            self.tokens -= n
            return True
        return False


class ProactiveEngine:
    """主动性决策器 · L1 core · 应用层定义 kind 类型"""

    def __init__(
        self,
        rate_capacity: int = 5,
        rate_refill_per_sec: float = 1 / 60,  # 默认 1/min
        cooldown_sec: float = 30.0,
    ):
        self._heap: list[ProactiveTrigger] = []
        self._limiter = TokenBucket(rate_capacity, rate_refill_per_sec)
        self._cooldown_sec = cooldown_sec
        self._last_taken_at: dict[str, float] = {}

    def offer(self, trigger: ProactiveTrigger) -> bool:
        """尝试入队 · 返 True 已入队 · False 被 cooldown/rate 闸住

        - cooldown:同 kind 在 cooldown_sec 内已 take 过 → 拒
        - rate:全局 token bucket 拒(超频)→ 拒
        - 否则入 heap
        """
        last = self._last_taken_at.get(trigger.kind, 0.0)
        if time.time() - last < self._cooldown_sec:
            return False
        if not self._limiter.try_take(1):
            return False
        heapq.heappush(self._heap, trigger)
        return True

    def take(self) -> ProactiveTrigger | None:
        """出队最高优先级 · 无则 None · 标记该 kind cooldown 起点"""
        if not self._heap:
            return None
        t = heapq.heappop(self._heap)
        self._last_taken_at[t.kind] = time.time()
        return t

    def has_pending(self) -> bool:
        return bool(self._heap)

    def pending_count(self) -> int:
        return len(self._heap)

    def reset_cooldown(self, kind: str) -> None:
        """测试用 · 强制清 cooldown"""
        self._last_taken_at.pop(kind, None)
