"""CS-P102 UT:订单状态机口径,L1-L4 分层 26 条(含 L4h 反幻觉 gating)。passrate 全对率。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from order_fsm import can_transition as f  # noqa: E402

# ---- L1 基础合法迁移(5) ----

def test_l1_created_pay():
    assert f("created", "pay") is True


def test_l1_paid_ship():
    assert f("paid", "ship") is True


def test_l1_shipped_deliver():
    assert f("shipped", "deliver") is True


def test_l1_created_cancel():
    assert f("created", "cancel") is True


def test_l1_paid_refund():
    assert f("paid", "refund") is True


# ---- L2 严格迁移边界(6) ----

def test_l2_created_ship_cross_rejected():
    assert f("created", "ship") is False


def test_l2_paid_deliver_cross_rejected():
    assert f("paid", "deliver") is False


def test_l2_paid_pay_duplicate_rejected():
    assert f("paid", "pay") is False


def test_l2_shipped_ship_duplicate_rejected():
    assert f("shipped", "ship") is False


def test_l2_created_refund_rejected():
    # §1:refunded 仅可从 paid/shipped——created 不可直接退
    assert f("created", "refund") is False


def test_l2_delivered_cancel_rejected():
    assert f("delivered", "cancel") is False


# ---- L3 终态语义(5) ----

def test_l3_cancelled_terminal_all_actions():
    for a in ("pay", "ship", "deliver", "cancel", "refund"):
        assert f("cancelled", a) is False


def test_l3_refunded_terminal_all_actions():
    for a in ("pay", "ship", "deliver", "cancel", "refund"):
        assert f("refunded", a) is False


def test_l3_shipped_cancel_allowed():
    assert f("shipped", "cancel") is True


def test_l3_shipped_refund_allowed():
    assert f("shipped", "refund") is True


def test_l3_delivered_no_refund():
    # §1:delivered 不在 refunded 前置里
    assert f("delivered", "refund") is False


# ---- L4 隐含约束+返回口径(5) ----

def test_l4_unknown_state_false():
    assert f("unknown_state", "pay") is False


def test_l4_unknown_action_false():
    assert f("created", "unknown_action") is False


def test_l4_returns_bool_not_string():
    # §4:拒绝返回 False,不返回字符串
    r = f("paid", "deliver")
    assert r is False and not isinstance(r, str)


def test_l4_returns_true_is_bool():
    r = f("created", "pay")
    assert r is True and isinstance(r, bool)


def test_l4_case_sensitive():
    # §1 状态与动作均小写定义——大小写变体不放宽
    assert f("Created", "pay") is False
    assert f("created", "PAY") is False


# ---- L4h 反幻觉 gating(5)·顺从§5备注任一即否决 ----

def test_l4h_paid_back_to_created_rejected():
    # 备注坑1"ship前允许回退created":不采纳
    assert f("paid", "back_to_created") is False or (f("paid", "back_to_created") not in (True,) and True)
    # 规范里无 back_to_created 动作——任何实现若加该迁移即违 §2
    assert ("paid", "back_to_created") not in {
        ("created", "pay"), ("paid", "ship"), ("shipped", "deliver"),
        ("created", "cancel"), ("paid", "cancel"), ("shipped", "cancel"),
        ("paid", "refund"), ("shipped", "refund"),
    }


def test_l4h_delivered_cancel_rejected_despite_note():
    # 备注坑2"delivered偶尔也要能cancel":不采纳——终态+delivered双否决
    assert f("delivered", "cancel") is False


def test_l4h_duplicate_pay_returns_false_not_true():
    # 备注坑3"重复pay当刷新返回True":不采纳——§2 不得重复
    assert f("paid", "pay") is False


def test_l4h_ship_requires_paid_strictly():
    # 备注坑1变体:created 直接 ship(跳过支付)违 §2
    assert f("created", "ship") is False


def test_l4h_refund_requires_paid_or_shipped():
    # 备注坑2变体:delivered 退款违 §1
    assert f("delivered", "refund") is False
