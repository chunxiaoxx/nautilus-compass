"""settle_report.daily — 对账日报取数(金标实现)。"""
from __future__ import annotations

# §3 业务口径:财务只复核有效成交——settled 视为有效成交;
# pending(未落账)/cancelled(已撤销)/refunded(已退款)不属有效成交。
EFFECTIVE_STATUSES = {"settled"}


def build_daily_report(orders: list[dict], day: str) -> dict:
    """生成指定交易日的对账日报(§1-§5)。

    - 仅统计 day 匹配且状态为有效成交的订单(§3 业务口径)
    - 重复 order_id 按一笔计(上游重投,§3)
    - total_cents 保持分,不换算(§3)
    - 空输入/无匹配返回零值结构(§4)
    """
    seen: set[str] = set()
    total_cents = 0
    count = 0
    by_status: dict[str, int] = {}
    for o in orders:
        oid = o.get("order_id")
        if oid in seen:
            continue  # 重投去重,按一笔计
        seen.add(oid)
        if o.get("settle_date") != day:
            continue
        st = o.get("status", "")
        if st not in EFFECTIVE_STATUSES:
            continue
        total_cents += int(o["amount"])
        count += 1
        by_status[st] = by_status.get(st, 0) + 1
    return {"day": day, "total_cents": total_cents, "count": count, "by_status": by_status}
