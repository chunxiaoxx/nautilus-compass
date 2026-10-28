# -*- coding: utf-8 -*-
"""名册读数纯函数单测:三色判定/信号合并/行组装(v5-part 服务语义)。"""
from ops.agent_roster import build_row, merge_signals, status_from_age

NOW = 1_000_000_000.0
H = 3600.0


# --- status_from_age ---

def test_status_none_is_red():
    assert status_from_age(None) == "RED"


def test_status_thresholds():
    assert status_from_age(10) == "GREEN"
    assert status_from_age(24.1) == "WARN"
    assert status_from_age(48.1) == "RED"


# --- merge_signals ---

def test_merge_takes_most_recent():
    src, h = merge_signals({"mail_out": NOW - 5 * H, "audit": NOW - 1 * H}, NOW)
    assert src == "audit" and h == 1.0


def test_merge_all_none():
    assert merge_signals({"mail_out": None, "audit": None}, NOW) == (None, None)


def test_merge_ignores_none():
    src, h = merge_signals({"mail_out": NOW - 2 * H, "audit": None}, NOW)
    assert src == "mail_out" and h == 2.0


# --- build_row ---

def test_dialog_row_uses_production_signals_only():
    cfg = {"kind": "dialog", "services": ["x.service"], "repo": None}
    row = build_row("t", cfg, {"mail_out": NOW - 3 * H, "audit": None},
                    {"x.service": "active"}, NOW)
    # 服务 active 不计入 dialog 信号(跑着≠产出)
    assert row["best_source"] == "mail_out" and row["status"] == "GREEN"


def test_dialog_no_signals_red_even_if_service_up():
    cfg = {"kind": "dialog", "services": ["x.service"], "repo": None}
    row = build_row("t", cfg, {"mail_out": None, "audit": None},
                    {"x.service": "active"}, NOW)
    assert row["status"] == "RED" and row["best_source"] is None


def test_v5_part_service_active_is_signal():
    cfg = {"kind": "v5-part", "services": ["k.service"], "repo": None}
    row = build_row("k", cfg, {"mail_out": None}, {"k.service": "active"}, NOW)
    assert row["status"] == "GREEN" and row["best_source"] == "service"


def test_v5_part_service_down_red():
    cfg = {"kind": "v5-part", "services": ["k.service"], "repo": None}
    row = build_row("k", cfg, {"mail_out": None}, {"k.service": "failed"}, NOW)
    assert row["status"] == "RED"
