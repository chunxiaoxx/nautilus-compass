# -*- coding: utf-8 -*-
"""fuel_settle 结算联动器纯函数测试(2026-10-04)——DB 行为云端首扫验证。"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ops.fuel_settle import (  # noqa: E402
    settle_amount, classify_source, rows_to_settle, resolve_agent_id,
    SOURCE_INTERNAL, SOURCE_EXTERNAL)


def test_settle_formula_matches_paid_history():
    # 11 笔实付实证:0.9→9, 0.78→8, 0.7→7, 0.55→6, 0.72→7, 0.5→5
    assert settle_amount(0.9) == 9
    assert settle_amount(0.78) == 8
    assert settle_amount(0.7) == 7
    assert settle_amount(0.55) == 6
    assert settle_amount(0.72) == 7
    assert settle_amount(0.5) == 5


def test_settle_zero_and_none():
    assert settle_amount(0) == 0
    assert settle_amount(None) == 0
    assert settle_amount(0.04) == 0


def test_source_classification():
    assert classify_source("v5", "v5") == SOURCE_INTERNAL
    assert classify_source("v5-turbo", "v5") == SOURCE_INTERNAL
    assert classify_source("v5", "nautilus-prime-001") == SOURCE_EXTERNAL
    assert classify_source(None, "nautilus-prime-001") == SOURCE_EXTERNAL


def test_rows_to_settle_filters():
    bounties = [
        {"bounty_id": "f-a", "posted_by": "v5", "claimed_by": "nautilus-prime-001", "score": 0.85},
        {"bounty_id": "f-b", "posted_by": "v5", "claimed_by": "v5", "score": 0.75},
        {"bounty_id": "f-c", "posted_by": "v5", "claimed_by": "x", "score": 0.0},   # 零分不结
        {"bounty_id": "f-d", "posted_by": "v5", "claimed_by": "x", "score": 0.9},   # 已结跳过
    ]
    out = rows_to_settle(bounties, {"f-d"})
    assert [r["bounty_id"] for r in out] == ["f-a", "f-b"]
    assert out[0]["amount"] == 8 and out[0]["source"] == SOURCE_EXTERNAL  # 0.85→8(f008/f014 实付实证)
    assert out[1]["amount"] == 8 and out[1]["source"] == SOURCE_INTERNAL


def test_resolve_agent_id_precise_and_fallback():
    roster = {"nautilus-prime-001": ["9000016", "9000020"], "v5-prime": ["9000018"]}
    assert resolve_agent_id("nautilus-prime-001", roster) == "9000016"  # 多行取最小
    assert resolve_agent_id("v5", roster) == "9000018"                  # 显式别名
    assert resolve_agent_id("ghost-agent", roster) is None              # 查不到不硬填
    assert resolve_agent_id(None, roster) is None
