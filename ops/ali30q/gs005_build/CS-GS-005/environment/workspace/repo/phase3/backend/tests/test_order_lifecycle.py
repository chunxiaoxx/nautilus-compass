# -*- coding: utf-8 -*-
"""order_lifecycle 单测:任务单生命周期阶段推导(F4/kairos 案例抽象)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.order_lifecycle import derive_stage, is_overdue  # noqa: E402

T = dict(id=100, trace_id="f4-fuel-20260902", to_agent="flywheel",
         deadline="2026-09-02 07:45:00", ack_at=None)


def test_dispatched_when_lone():
    assert derive_stage(T, replies=[], accepted=False) == "DISPATCHED"


def test_claimed_on_ack_or_reply():
    assert derive_stage({**T, "ack_at": "x"}, [], False) == "CLAIMED"
    assert derive_stage(T, [dict(id=101, title="认领", body="")], False) == "CLAIMED"


def test_delivered_on_commit_hash_in_reply():
    r = [dict(id=102, title="F4 交付", body="commit a8ebeee 配方执行")]
    assert derive_stage(T, r, False) == "DELIVERED"


def test_accepted_on_acceptance_letter():
    r = [dict(id=102, title="交付", body="hash 0917745")]
    acc = [dict(id=103, title="[验收合格] F4", body="")]
    assert derive_stage(T, r, True, acceptance_letters=acc) == "ACCEPTED"


def test_closed_on_capability_or_void():
    r = [dict(id=102, title="交付", body="0917745")]
    assert derive_stage(T, r, True, cap_after=True) == "CLOSED"
    void = [dict(id=104, title="[销案] 作废", body="")]
    assert derive_stage(T, void, False, void_letters=void) == "CLOSED"


def test_overdue_only_when_open():
    assert is_overdue(T, "2026-09-03 10:00:00", "DISPATCHED") is True
    assert is_overdue(T, "2026-09-03 10:00:00", "CLOSED") is False
    assert is_overdue(T, "2026-09-02 06:00:00", "DISPATCHED") is False
