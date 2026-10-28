"""refund_service.core — 退款处理(骨架:由实现者填充)。"""
from __future__ import annotations


def process_refund(order: dict, refund_cents: int, history: list[dict],
                   refund_id: str = "") -> dict:
    """处理一笔退款申请(§1-§5)。骨架:签名与返回结构已定,逻辑由实现者完成。"""
    raise NotImplementedError("REFUND-2026-1025-P101: implement me")
