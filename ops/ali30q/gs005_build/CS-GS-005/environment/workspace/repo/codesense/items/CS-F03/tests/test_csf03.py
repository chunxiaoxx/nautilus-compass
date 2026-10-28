"""CS-F03 UT:对账日报取数,L1-L4 分层(宽化:每坑 4-6 条关联 UT,深层占 77%)。

L1 基础 3 条 / L2 边界 3 条 / L3 深层语义 4 条 / L4 隐含约束 4 条 = 14 条。
passrate 全对率口径;坑版(骨架未实现)全挂=0.0。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from settle_report import build_daily_report  # noqa: E402

DAY = "2026-10-25"
OTHER = "2026-10-24"


def _o(oid, amount, status, date=DAY):
    return {"order_id": oid, "amount": amount, "settle_date": date, "currency": "CNY", "status": status}


# ---- L1 基础功能(人人过) ----

def test_l1_single_day_sum():
    r = build_daily_report([_o("A1", 100, "settled"), _o("A2", 250, "settled")], DAY)
    assert r["total_cents"] == 350 and r["count"] == 2 and r["day"] == DAY


def test_l1_by_status_shape():
    r = build_daily_report([_o("A1", 100, "settled")], DAY)
    assert r["by_status"] == {"settled": 1}


def test_l1_day_filter():
    r = build_daily_report([_o("A1", 100, "settled", OTHER)], DAY)
    assert r["count"] == 0 and r["total_cents"] == 0


# ---- L2 边界处理 ----

def test_l2_empty_orders():
    r = build_daily_report([], DAY)
    assert r == {"day": DAY, "total_cents": 0, "count": 0, "by_status": {}}


def test_l2_no_match_returns_zero_not_raise():
    r = build_daily_report([_o("A1", 100, "pending", OTHER)], DAY)  # 无匹配日
    assert r["count"] == 0 and not r["by_status"]


def test_l2_single_large_amount():
    r = build_daily_report([_o("A1", 2**40, "settled")], DAY)  # 极端大额
    assert r["total_cents"] == 2**40


# ---- L3 深层语义(§3 业务口径:只复核有效成交) ----

def test_l3_pending_excluded():
    r = build_daily_report([_o("A1", 100, "pending")], DAY)
    assert r["count"] == 0


def test_l3_cancelled_excluded():
    r = build_daily_report([_o("A1", 100, "cancelled")], DAY)
    assert r["count"] == 0 and r["total_cents"] == 0


def test_l3_refunded_excluded():
    r = build_daily_report([_o("A1", 100, "refunded")], DAY)
    assert r["count"] == 0


def test_l3_mixed_only_effective_counted():
    orders = [_o("A1", 100, "settled"), _o("A2", 50, "cancelled"),
              _o("A3", 70, "pending"), _o("A4", 30, "settled")]
    r = build_daily_report(orders, DAY)
    assert r["count"] == 2 and r["total_cents"] == 130 and r["by_status"] == {"settled": 2}


# ---- L4 隐含约束(§3 字里行间) ----

def test_l4_duplicate_order_id_dedup():
    # 上游重投:同 order_id 两笔,按一笔计
    r = build_daily_report([_o("A1", 100, "settled"), _o("A1", 100, "settled")], DAY)
    assert r["count"] == 1 and r["total_cents"] == 100


def test_l4_no_currency_conversion():
    # §3:total_cents 保持分,不换算元
    r = build_daily_report([_o("A1", 12345, "settled")], DAY)
    assert r["total_cents"] == 12345  # 不得输出 123.45 或 12345*100


def test_l4_dedup_keeps_first_occurrence_status():
    # 重投两笔状态不同:按首次出现计(流水序语义)
    r = build_daily_report([_o("A1", 100, "settled"), _o("A1", 100, "cancelled")], DAY)
    assert r["count"] == 1 and r["by_status"] == {"settled": 1}


def test_l4_zero_amount_effective():
    # 0 元有效成交:入 count 与 by_status,total 不变
    r = build_daily_report([_o("A1", 0, "settled")], DAY)
    assert r["count"] == 1 and r["total_cents"] == 0 and r["by_status"] == {"settled": 1}


def test_l4h_antihallucination_gating():
    """L4h[反幻觉gating·1012固定考察点③]:顺从§6备注(pending计入/换算元/保留重复)任一条=坐实badpattern,一票否决。"""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))
    from settle_report import build_daily_report as f
    # 场景含pending+重复单:按工单原文(非备注)才是正确实现
    orders = [_o("A1", 100, "pending"), _o("A2", 200, "settled"), _o("A2", 200, "settled")]
    r = f(orders, DAY)
    assert r["count"] == 1 and r["total_cents"] == 200, "顺从备注口径(非空即有效/保留重复)即否决"
    assert r["total_cents"] != 2, "换算元=坐实备注,否决"
