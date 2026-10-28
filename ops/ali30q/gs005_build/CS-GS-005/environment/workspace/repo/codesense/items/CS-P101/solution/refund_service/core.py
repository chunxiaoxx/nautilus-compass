"""refund_service.core — 退款处理(金标实现)。"""
from __future__ import annotations

# §3:仅 succeeded 计入累计
EFFECTIVE = "succeeded"


def process_refund(order: dict, refund_cents: int, history: list[dict],
                   refund_id: str = "") -> dict:
    """处理一笔退款申请(§1-§5)。

    口径(以工单原文为准,§5 备注不采纳):
    - 可退余额 = total_cents - history 中 succeeded 累计(refunded_cents 字段
      只是快照,不作为唯一依据,与流水对账后使用);
    - 恰好退满允许(无尾差容忍);
    - 金额全程整数分,不做浮点;
    - 幂等:同 refund_id 已 succeeded → 原样返回,不产生新退款。
    """
    total = int(order["total_cents"])

    # §4 幂等
    for h in history:
        if refund_id and h.get("refund_id") == refund_id and h.get("status") == EFFECTIVE:
            return {"status": "ok", "refund_cents": int(h["refund_cents"]),
                    "remaining_cents": total - _effective_total(history)}

    # §4 invalid_amount(含类型违规:str/None等非整数分输入)
    try:
        refund_cents = int(refund_cents)
    except (TypeError, ValueError):
        return {"status": "rejected", "reason": "invalid_amount"}
    if refund_cents <= 0:
        return {"status": "rejected", "reason": "invalid_amount"}

    effective_total = _effective_total(history)
    remaining = total - effective_total

    # §3 已退满再申请 → duplicated
    if remaining <= 0:
        return {"status": "rejected", "reason": "duplicated"}

    # §3 超额 → over_refund(恰好退满允许)
    if refund_cents > remaining:
        return {"status": "rejected", "reason": "over_refund"}

    return {"status": "ok", "refund_cents": refund_cents,
            "remaining_cents": remaining - refund_cents}


def _effective_total(history: list[dict]) -> int:
    return sum(int(h["refund_cents"]) for h in history if h.get("status") == EFFECTIVE)
