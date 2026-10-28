"""score_reconcile 测试 — 双判分互核对账(转移线②前置件,v4 翻案人肉对账的固化)。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))

from score_reconcile import parse_scores, reconcile  # noqa: E402


def test_parse_and_aggregate():
    lines = ["train g2b1:aaa True", "train g2b1:aaa False", "train g2b1:aaa True",
             "hold g2b1:bbb False"]
    agg = parse_scores(lines)
    assert agg[("train", "g2b1:aaa")] == (2, 3)   # (passes, attempts)
    assert agg[("hold", "g2b1:bbb")] == (0, 1)


def test_reconcile_agree():
    a = {("train", "x"): (2, 3)}
    b = {("train", "x"): (2, 3)}
    out = reconcile(a, b)
    assert out["agree"] == 1 and out["differ"] == 0 and not out["diffs"]


def test_reconcile_diff_flagged():
    a = {("train", "x"): (1, 3), ("hold", "y"): (0, 3)}
    b = {("train", "x"): (0, 3), ("hold", "y"): (0, 3)}
    out = reconcile(a, b)
    assert out["differ"] == 1
    assert out["diffs"] == [{"split": "train", "task": "x", "a": [1, 3], "b": [0, 3]}]


def test_reconcile_only_in_one_side():
    a = {("train", "x"): (1, 3)}
    b = {}
    out = reconcile(a, b)
    assert out["only_a"] == [("train", "x")] and out["only_b"] == []
