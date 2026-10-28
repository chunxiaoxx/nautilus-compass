"""W-5 临时 poller · compass read_buyer_tasks → 派单决策 → POST /api/platform/fde/dispatch.

平台侧兜底:V7 连接器(agent-first)没就位时,平台轮询 compass 的买方题读接口并派单。

turf 边界(G-turf):
  - **读** = compass(`read_buyer_tasks`,凭据网关 + feishu_client 在 compass)。
    平台**不**重造 feishu 读 —— compass 的 read 是一个注入的 `BuyerTaskSource`。
  - **派单决策** = 平台 own(`should_dispatch`)。不让 compass 主动 POST dispatch。
  - **连接器** = V7(就位后取代本 poller);本 poller 是临时兜底。

接线状态:compass 的 `read_buyer_tasks` 尚未在生产暴露(在 feature 分支 fde-feishu-settle)。
本模块的派单决策 + 去重 + fail-soft 逻辑已 TDD green;source 绑定 = dormant seam,
compass 就位即注入一个 `read_buyer_tasks()` 实现(MCP 或 HTTP adapter)。
"""
from __future__ import annotations

from typing import Callable, Iterable, Protocol


class BuyerTaskSource(Protocol):
    """compass 买方题读接口 (the compass-binding seam).

    每个 task 至少含 ``task_uid``,通常还有 ``title`` / ``description``。
    """

    def read_buyer_tasks(self) -> Iterable[dict]:  # pragma: no cover - protocol
        ...


def should_dispatch(task: dict) -> bool:
    """派单决策(平台 turf)。

    v1 policy:有 ``task_uid`` 即可派(实际去重交由 dispatch substrate idempotent +
    poller 的 already_dispatched 集合)。未来可加优先级 / 容量 / 时间窗策略。
    """
    return bool(task.get("task_uid"))


def poll_and_dispatch(
    source: BuyerTaskSource,
    dispatch_fn: Callable[[dict], object],
    already_dispatched: Iterable[str] | None = None,
) -> dict:
    """读买方题 → 去重(已派/批内重复)→ 派单决策 → 调 dispatch_fn。

    Args:
        source: compass read seam,提供 ``read_buyer_tasks()``。
        dispatch_fn: 把一个 task 派出去(POST /api/platform/fde/dispatch 的 in-proc
            或 HTTP 封装)。派单决策已在此函数内做完,dispatch_fn 只负责投递。
        already_dispatched: 已派过的 task_uid 集合(跨轮去重,幂等)。

    Returns:
        ``{"dispatched": [uid…], "skipped": [uid…], "failed": [uid…]}`` —— fail-soft,
        单个 task 派失败不中断整批。
    """
    seen = set(already_dispatched or ())
    dispatched: list[str] = []
    skipped: list[str] = []
    failed: list[str] = []

    for task in source.read_buyer_tasks():
        uid = task.get("task_uid")
        if not should_dispatch(task):
            skipped.append(uid)  # uid may be None for a task without one
            continue
        if uid in seen:
            skipped.append(uid)
            continue
        try:
            dispatch_fn(task)
        except Exception:  # fail-soft: 单题派失败不拖垮整批
            failed.append(uid)
            continue
        dispatched.append(uid)
        seen.add(uid)

    return {"dispatched": dispatched, "skipped": skipped, "failed": failed}
