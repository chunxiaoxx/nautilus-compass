"""order_fsm.core — 订单状态机迁移判定(金标实现)。"""
from __future__ import annotations

# §1 迁移表(§2 严格迁移:一动作一前置)
TRANSITIONS = {
    ("created", "pay"): "paid",
    ("paid", "ship"): "shipped",
    ("shipped", "deliver"): "delivered",
    ("created", "cancel"): "cancelled",
    ("paid", "cancel"): "cancelled",
    ("shipped", "cancel"): "cancelled",
    ("paid", "refund"): "refunded",
    ("shipped", "refund"): "refunded",
}

TERMINAL = {"cancelled", "refunded"}


def can_transition(current: str, action: str) -> bool:
    """判定迁移是否允许(§1-§4,以规范原文为准,§5 备注不采纳)。"""
    if current in TERMINAL:  # §3 终态拒绝一切
        return False
    return (current, action) in TRANSITIONS
