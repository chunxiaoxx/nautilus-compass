"""S3 集成线1 · 读 FDE 前台专家库(RGDK v06_行业专家)单价 → 结算应付真算.

跨对话框有机整合第一根线(只读 FDE 表·写我自己的结算·零撞车)。
design: _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260615_organic_integration_alignment.md §6。

🔴 immutable:price_settlement 返新 dict,不改入参。
🔴 诚实:专家不在名册 / 工时未知 → 应付保持 None(不臆造金额·charter §2)。
"""
from __future__ import annotations


def _num(v) -> float | None:
    """飞书字段值 → float(容忍字符串/None/空)。"""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def parse_expert_rates(rows: list[dict]) -> dict[str, float]:
    """FDE v06_行业专家 行 → {姓名: 工时单价}。缺名/缺价行跳过。"""
    rates: dict[str, float] = {}
    for row in rows or []:
        name = str(row.get("姓名") or "").strip()
        rate = _num(row.get("工时单价_元每小时"))
        if not name or rate is None:
            continue
        rates[name] = rate
    return rates


def compute_payable(rate: float | None, hours) -> float | None:
    """应付 = 单价 × 工时。任一缺失或工时≤0 → None(不臆造)。"""
    h = _num(hours)
    if rate is None or h is None or h <= 0:
        return None
    return round(float(rate) * h, 2)


def price_settlement(record: dict, rates: dict[str, float], hours=None) -> dict:
    """结算记录 + 专家名册单价 + 工时 → 填应付的新记录(immutable)。

    专家在名册 + 工时已知 → payable_amount=单价×工时·status='computed'。
    否则 → payable_amount=None·status='pending'·带 payable_reason(诚实暴露为何没算)。
    """
    out = dict(record)
    expert = str(record.get("expert") or "").strip()
    rate = rates.get(expert)
    if rate is None:
        out["payable_amount"] = None
        out["payable_status"] = "pending"
        out["payable_reason"] = "expert_not_in_roster"
        return out
    payable = compute_payable(rate, hours)
    if payable is None:
        out["payable_amount"] = None
        out["payable_status"] = "pending"
        out["payable_reason"] = "hours_unknown"
        return out
    out["payable_amount"] = payable
    out["payable_rate"] = rate
    out["payable_hours"] = hours
    out["payable_status"] = "computed"
    return out
