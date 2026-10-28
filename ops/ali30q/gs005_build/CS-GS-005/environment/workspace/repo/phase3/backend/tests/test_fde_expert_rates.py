"""S3 集成线1 · 结算读 FDE 前台专家库单价 → 应付真算(跨 app 只读·零撞车).

design: _OUTBOUND_FROM_PLATFORM_SOUL_TO_FDE_20260615_organic_integration_alignment.md §6 线1。
FDE v06_行业专家(RGDK base)字段:姓名 / 工时单价_元每小时 / 累计工时 ...
🔴 只读 FDE 表·写我自己的结算·应付=单价×工时;缺专家/工时则保持 None(不臆造)。
"""
from services.fde_expert_rates import (
    parse_expert_rates,
    compute_payable,
    price_settlement,
)


def _roster_rows():
    return [
        {"姓名": "张工", "工时单价_元每小时": 300, "累计工时": 40},
        {"姓名": "李博士", "工时单价_元每小时": 500, "累计工时": 12},
        {"姓名": "", "工时单价_元每小时": 200},          # 缺名 → 跳过
        {"姓名": "王律师", "工时单价_元每小时": None},     # 缺单价 → 跳过
    ]


def test_parse_expert_rates_builds_name_to_rate_map():
    rates = parse_expert_rates(_roster_rows())
    assert rates == {"张工": 300.0, "李博士": 500.0}   # 缺名/缺价行被跳过


def test_parse_expert_rates_tolerates_string_numbers():
    rates = parse_expert_rates([{"姓名": "赵工", "工时单价_元每小时": "350"}])
    assert rates == {"赵工": 350.0}


def test_compute_payable_rate_times_hours():
    assert compute_payable(300.0, 8) == 2400.0
    assert compute_payable(500.0, 1.5) == 750.0


def test_compute_payable_none_when_missing_or_nonpositive():
    assert compute_payable(None, 8) is None
    assert compute_payable(300.0, None) is None
    assert compute_payable(300.0, 0) is None
    assert compute_payable(300.0, -2) is None


def _settlement(expert="张工"):
    return {"task_uid": "expert_t2_x", "expert": expert, "line": "2",
            "payable_amount": None, "payable_status": "pending",
            "status": "delivered_provisional"}


def test_price_settlement_fills_payable_when_expert_and_hours_known():
    rates = {"张工": 300.0}
    r = price_settlement(_settlement("张工"), rates, hours=8)
    assert r["payable_amount"] == 2400.0
    assert r["payable_rate"] == 300.0 and r["payable_hours"] == 8
    assert r["payable_status"] == "computed"      # 已算出·待付(非凭空 None)


def test_price_settlement_stays_pending_when_expert_not_in_roster():
    # 🔴 诚实:专家不在 FDE 名册(如 drift 任务无 assignee)→ 应付仍 None·不臆造
    r = price_settlement(_settlement("无名氏"), {"张工": 300.0}, hours=8)
    assert r["payable_amount"] is None
    assert r["payable_status"] == "pending"
    assert r["payable_reason"] == "expert_not_in_roster"


def test_price_settlement_stays_pending_when_hours_unknown():
    r = price_settlement(_settlement("张工"), {"张工": 300.0}, hours=None)
    assert r["payable_amount"] is None
    assert r["payable_status"] == "pending"
    assert r["payable_reason"] == "hours_unknown"


def test_price_settlement_does_not_mutate_input():
    rec = _settlement("张工")
    price_settlement(rec, {"张工": 300.0}, hours=8)
    assert rec["payable_amount"] is None   # 原 record 不被改(immutable)
