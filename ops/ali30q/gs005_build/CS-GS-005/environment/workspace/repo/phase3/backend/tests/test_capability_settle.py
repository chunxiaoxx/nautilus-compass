# -*- coding: utf-8 -*-
"""capability_settle 单测:验收函→自动记账(幂等/映射/分数)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from ops.capability_settle import score_of, agent_id_of, pick_new_acceptances  # noqa: E402

STATE = {"done": [150]}


def test_score():
    assert score_of("[F4 预盘点 v0.9 验收合格] 首笔") == 1.0
    assert score_of("[验收部分合格] xx") == 0.6
    assert score_of("普通函") == 0.0  # 非验收函不记


def test_agent_map():
    assert agent_id_of("flywheel") == "9000014"
    assert agent_id_of("v5") == "9000002"
    assert agent_id_of("unknown-frame") is None


def test_pick_new():
    letters = [
        dict(id=150, from_agent="platform", to_agent="flywheel",
             title="[验收合格] F4", trace_id="f4-acceptance-20260902"),
        dict(id=151, from_agent="platform", to_agent="flywheel",
             title="[验收合格] 新单", trace_id="x-acceptance-1"),
        dict(id=152, from_agent="v5", to_agent="platform",
             title="[验收合格] 不是平台发的", trace_id="x-2"),
    ]
    got = pick_new_acceptances(letters, STATE)
    assert [g["id"] for g in got] == [151]
