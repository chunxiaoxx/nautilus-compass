"""order_fsm.core — 订单状态机迁移判定(骨架:由实现者填充)。"""
from __future__ import annotations


def can_transition(current: str, action: str) -> bool:
    """判定 current 状态+action 是否允许迁移(§1-§4)。骨架待实现。"""
    raise NotImplementedError("FSM-2026-1025-P102: implement me")
