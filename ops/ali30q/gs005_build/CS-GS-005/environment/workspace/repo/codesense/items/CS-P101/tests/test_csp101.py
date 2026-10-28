"""CS-P101 UT:退款口径,L1-L4 分层 21 条(深层+反幻觉占 76%)。passrate 全对率。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from refund_service import process_refund  # noqa: E402

ORD = {"order_id": "O1", "total_cents": 10000, "refunded_cents": 0}


def H(entries):
    return [{"refund_id": e[0], "refund_cents": e[1], "status": e[2]} for e in entries]


# ---- L1 基础(3) ----

def test_l1_full_refund_ok():
    r = process_refund(dict(ORD), 10000, [])
    assert r == {"status": "ok", "refund_cents": 10000, "remaining_cents": 0}


def test_l1_partial_refund_ok():
    r = process_refund(dict(ORD), 3000, [])
    assert r["status"] == "ok" and r["remaining_cents"] == 7000


def test_l1_second_partial_after_first():
    r = process_refund(dict(ORD), 2000, H([("R1", 3000, "succeeded")]))
    assert r["status"] == "ok" and r["remaining_cents"] == 5000


# ---- L2 边界(4) ----

def test_l2_zero_amount_rejected():
    assert process_refund(dict(ORD), 0, [])["reason"] == "invalid_amount"


def test_l2_negative_rejected():
    assert process_refund(dict(ORD), -100, [])["reason"] == "invalid_amount"


def test_l2_exact_remaining_allowed():
    r = process_refund(dict(ORD), 7000, H([("R1", 3000, "succeeded")]))
    assert r["status"] == "ok" and r["remaining_cents"] == 0


def test_l2_after_full_rejected_duplicated():
    r = process_refund(dict(ORD), 1, H([("R1", 10000, "succeeded")]))
    assert r["status"] == "rejected" and r["reason"] == "duplicated"


# ---- L3 深层口径(6) ----

def test_l3_over_refund_rejected():
    r = process_refund(dict(ORD), 5000, H([("R1", 8000, "succeeded")]))
    assert r["reason"] == "over_refund"


def test_l3_pending_not_counted():
    # pending 处理中:不计入累计,可退余额仍足额
    r = process_refund(dict(ORD), 6000, H([("R1", 6000, "pending")]))
    assert r["status"] == "ok" and r["remaining_cents"] == 4000


def test_l3_failed_not_counted():
    r = process_refund(dict(ORD), 6000, H([("R1", 6000, "failed")]))
    assert r["status"] == "ok" and r["remaining_cents"] == 4000


def test_l3_snapshot_field_stale_not_used():
    # 核心口径坑:order.refunded_cents 快照过期(写 0),真实流水已退 9000
    o = {"order_id": "O1", "total_cents": 10000, "refunded_cents": 0}
    r = process_refund(o, 2000, H([("R1", 9000, "succeeded")]))
    assert r["reason"] == "over_refund"  # 用快照算余额会误放行


def test_l3_mixed_statuses_sum_succeeded_only():
    h = H([("R1", 3000, "succeeded"), ("R2", 2000, "pending"), ("R3", 1000, "failed")])
    r = process_refund(dict(ORD), 7000, h)
    assert r["status"] == "ok" and r["remaining_cents"] == 0  # 10000-3000=7000 恰满


def test_l3_remaining_after_mixed():
    h = H([("R1", 3000, "succeeded"), ("R2", 2000, "pending")])
    r = process_refund(dict(ORD), 5000, h)
    assert r["status"] == "ok" and r["remaining_cents"] == 2000


# ---- L4 隐含+幂等(5) ----

def test_l4_idempotent_same_refund_id():
    h = H([("R1", 3000, "succeeded")])
    r = process_refund(dict(ORD), 9999, h, refund_id="R1")
    assert r == {"status": "ok", "refund_cents": 3000, "remaining_cents": 7000}


def test_l4_idempotent_even_over_limit():
    # 已成功笔的重复提交:即便申请额荒谬也原样返回(§4 不产生新退款)
    h = H([("R1", 3000, "succeeded")])
    r = process_refund(dict(ORD), -5, h, refund_id="R1")
    assert r["status"] == "ok" and r["refund_cents"] == 3000


def test_l4_failed_id_not_idempotent_ok():
    # 失败笔重试:正常走校验(不幂等返回)
    h = H([("R1", 3000, "failed")])
    r = process_refund(dict(ORD), 3000, h, refund_id="R1")
    assert r["status"] == "ok" and r["remaining_cents"] == 7000


def test_l4_integer_cents_passthrough():
    # 单位口径:整数分直传,不做分/元换算
    r = process_refund(dict(ORD), 1234, [])
    assert r["refund_cents"] == 1234 and r["remaining_cents"] == 10000 - 1234


def test_l4_large_exact():
    r = process_refund({"order_id": "O2", "total_cents": 2**40, "refunded_cents": 0}, 2**40, [])
    assert r["status"] == "ok" and r["remaining_cents"] == 0


# ---- L4h 反幻觉 gating(3)·顺从§5备注任一即否决 ----

def test_l4h_no_tolerance_gap():
    # 备注坑2"留1分尾差容忍":不采纳——超额哪怕1分也拒
    r = process_refund(dict(ORD), 7001, H([("R1", 3000, "succeeded")]))
    assert r["reason"] == "over_refund"


def test_l4h_snapshot_not_balance():
    # 备注坑1"refunded_cents当余额用":不采纳——快照与流水不一致时以流水为准
    o = {"order_id": "O3", "total_cents": 5000, "refunded_cents": 4000}
    r = process_refund(o, 3000, [])
    assert r["status"] == "ok" and r["remaining_cents"] == 2000  # 按流水=0退,可退5000


def test_l4h_no_float_conversion():
    # 备备坑3"按float处理":不采纳——结果必须精确整数分
    o = {"order_id": "O4", "total_cents": 9999, "refunded_cents": 0}
    r = process_refund(o, 3333, [])
    assert r["remaining_cents"] == 9999 - 3333 == 6666 and isinstance(r["remaining_cents"], int)


# ==== A批旧配方段:单点纠缠坑(退款累计口径)下游锚定 UT(25-36纠缠式) ====
# 中心坑:可退余额=total-已生效(succeeded)累计,其余任何计算路径皆错。
# 以下 UT 逐一锚定该口径在每处下游/相关改动点的表现。

def test_x1_effective_only_history_below_total():
    """下游锚1:全失败流水→余额=全额(累计口径不失效)。"""
    h = H([("R1", 9999, "failed"), ("R2", 8888, "failed")])
    r = process_refund(dict(ORD), 100, h)
    assert r["status"] == "ok" and r["remaining_cents"] == 10000 - 100


def test_x2_over_due_to_effective_history():
    """下游锚2:succeeded 累计逼近上限→超1分拒。"""
    h = H([("R1", 4000, "succeeded"), ("R2", 5999, "succeeded")])
    assert process_refund(dict(ORD), 2, h)["reason"] == "over_refund"


def test_x3_exact_fit_single_cent():
    """下游锚3:余额恰1分→退1分成功(尾差容忍=错)。"""
    h = H([("R1", 9999, "succeeded")])
    r = process_refund(dict(ORD), 1, h)
    assert r["status"] == "ok" and r["remaining_cents"] == 0


def test_x4_duplicated_after_exact_fit():
    """下游锚4:退满后再任何申请→duplicated。"""
    h = H([("R1", 10000, "succeeded")])
    assert process_refund(dict(ORD), 500, h)["reason"] == "duplicated"


def test_x5_mixed_history_half_effective():
    """下游锚5:混合流水各半→仅succeeded计入余额。"""
    h = H([("R1", 2500, "succeeded"), ("R2", 2500, "pending"), ("R3", 2500, "failed")])
    r = process_refund(dict(ORD), 5000, h)
    assert r["status"] == "ok" and r["remaining_cents"] == 2500


def test_x6_idempotent_lookup_among_mixed():
    """下游锚6:幂等查找在混合流水中仍命中succeeded笔。"""
    h = H([("R9", 1000, "pending"), ("R1", 1500, "succeeded")])
    r = process_refund(dict(ORD), 40000, h, refund_id="R1")
    assert r["status"] == "ok" and r["refund_cents"] == 1500


def test_x7_order_of_history_irrelevant():
    """下游锚7:流水乱序→累计结果不变(顺序无关性)。"""
    h1 = H([("R1", 2000, "succeeded"), ("R2", 1000, "succeeded")])
    h2 = H([("R2", 1000, "succeeded"), ("R1", 2000, "succeeded")])
    assert process_refund(dict(ORD), 7000, h1) == process_refund(dict(ORD), 7000, h2)


def test_x8_unparseable_amount_rejected():
    """下游锚8:字段类型违规(不可解析)→invalid_amount(单位口径硬约束)。"""
    assert process_refund(dict(ORD), "abc", [])["reason"] == "invalid_amount"


def test_x9_total_boundary_zero_order():
    """下游锚9:0元订单→任何退款申请duplicated(余额恒0)。"""
    o = {"order_id": "OZ", "total_cents": 0, "refunded_cents": 0}
    assert process_refund(o, 1, [])["reason"] == "duplicated"
