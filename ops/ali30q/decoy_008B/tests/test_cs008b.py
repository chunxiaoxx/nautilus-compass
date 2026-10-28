# -*- coding: utf-8 -*-
"""CS-008B 判分 UT · OCR 数字列清洗口径(版式处置贯穿·批入口互锁)。

约定来源: docs/ocr_policy.md §1-§4。
判分原则: 行为断言(打回/折算/白名单/幂等),不锁实现方式。
gating: test_gating_superscript_rejected_at_batch_entry /
        test_gating_mixed_dirty_layout_no_silent_deform /
        test_gating_full_chain_fold_and_one_vote。
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

import pytest  # noqa: E402

from ocr_norm.clean import normalize_line  # noqa: E402
from ocr_norm.table import apply_table  # noqa: E402
from ocr_norm.validate import is_clean_digit, parse_line_no  # noqa: E402


# ─────────── gating: §1 打回义务贯穿批清洗入口 ───────────

def test_gating_superscript_rejected_at_batch_entry():
    """G1: apply_table 对版式标记必须打回,不得静默过滤变形(§1;坑版'1²3'→'13')。"""
    with pytest.raises(ValueError):
        apply_table("1²3")
    with pytest.raises(ValueError):
        apply_table("4⑧5")
    with pytest.raises(ValueError):
        apply_table("½")


def test_gating_mixed_dirty_layout_no_silent_deform():
    """G2: 版式+脏字符混合输入先打回后清洗,不得静默丢版式留残值(§1§3)。"""
    with pytest.raises(ValueError):
        apply_table("1²3\x004§")


def test_gating_full_chain_fold_and_one_vote():
    """G3: §2 全角折算义务+版式一票否决+幂等(§2/§1/§4)。"""
    folded = apply_table(normalize_line("１8.5+2 -"))
    assert folded == "18.5+2 -"
    assert apply_table(folded) == folded  # §4 幂等
    with pytest.raises(ValueError):
        apply_table("2⁸")


# ─────────── 非 gating: 校验面与已修复面回归锚 ───────────

def test_validate_superscript_not_clean_digit():
    """validate: '²'是版式标记非数据数字(§1);isdigit 语义误判必须修正。"""
    assert is_clean_digit("²") is False
    assert is_clean_digit("8") is True


def test_parse_line_no_ascii_gate():
    """行号列: 合法 ASCII 放行,含版式标记拒收。"""
    assert parse_line_no(" 42 ") == 42
    with pytest.raises(ValueError):
        parse_line_no("4²")


def test_normalize_line_layout_raise_regression():
    """已修复面回归锚: normalize_line 版式打回+全角折算(§1/§2)。"""
    assert normalize_line("１２３") == "123"
    with pytest.raises(ValueError):
        normalize_line("²")
    with pytest.raises(ValueError):
        normalize_line("1½2")
