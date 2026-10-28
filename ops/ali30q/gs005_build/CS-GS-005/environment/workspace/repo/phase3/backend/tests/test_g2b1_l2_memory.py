# -*- coding: utf-8 -*-
"""L2 纵向记忆实验单测(9/8 凌晨:三臂 A/B/C,预注册冻结)。

设计正本:docs/research/2026-09-07-coding域RSI深挖-从PathB到纵向记忆.md §5。
可测纯函数:检索打分(同文件>同目录>同 repo)/placebo 防同源/注入构造/
配对 sign test(6/9 仪器纪律的小样本版)。
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
if str(BACKEND / "tools") not in sys.path:
    sys.path.insert(0, str(BACKEND / "tools"))

import g2_b1_l2_memory_experiment as l2  # noqa: E402

TASK = {"repo_path": "C:/x/repo", "source_files": ["app/pay.py"],
        "reference_fix_commit": "aaa"}
MEM_SAME_FILE = {"source_rel": "app/pay.py", "repo_path": "C:/x/repo",
                 "reference_fix_commit": "bbb", "winning_diff": "d1",
                 "task": {"subject": "fix(pay)"}, "test_id": "t"}
MEM_SAME_DIR = {"source_rel": "app/refund.py", "repo_path": "C:/x/repo",
                "reference_fix_commit": "ccc", "winning_diff": "d2",
                "task": {"subject": "fix(refund)"}, "test_id": "t"}
MEM_OTHER_REPO = {"source_rel": "src/x.py", "repo_path": "C:/y/other",
                  "reference_fix_commit": "ddd", "winning_diff": "d3",
                  "task": {"subject": "fix(x)"}, "test_id": "t"}


def test_score_prefers_same_file_over_dir_over_repo():
    assert l2.score_memory(TASK, MEM_SAME_FILE) > l2.score_memory(TASK, MEM_SAME_DIR)
    assert l2.score_memory(TASK, MEM_SAME_DIR) > l2.score_memory(TASK, MEM_OTHER_REPO)


def test_pick_memory_excludes_self_and_prefers_top():
    pool = [MEM_OTHER_REPO, MEM_SAME_DIR, MEM_SAME_FILE,
            {**MEM_SAME_FILE, "reference_fix_commit": "aaa", "winning_diff": "SELF"}]
    pick = l2.pick_memory(TASK, pool)
    assert pick["winning_diff"] == "d1"  # 最高分,且自身(同 ref)被排除


def test_pick_memory_empty_pool_returns_none():
    assert l2.pick_memory(TASK, []) is None


def test_pick_placebo_never_same_repo_or_file():
    pool = [MEM_SAME_FILE, MEM_SAME_DIR, MEM_OTHER_REPO]
    p = l2.pick_placebo(TASK, pool, seed=42)
    assert p["repo_path"] != TASK["repo_path"]
    assert Path(p["source_rel"]).name != "pay.py"


def test_pick_placebo_deterministic_same_seed():
    pool = [MEM_OTHER_REPO, {**MEM_OTHER_REPO, "winning_diff": "d4"}]
    a = l2.pick_placebo(TASK, pool, seed=7)
    b = l2.pick_placebo(TASK, pool, seed=7)
    assert a["winning_diff"] == b["winning_diff"]


def test_injection_mentions_pattern_not_verbatim():
    s = l2.build_injection(MEM_SAME_FILE)
    assert "do NOT apply this diff verbatim" in s
    assert "d1" in s
    assert "fix(pay)" in s


def test_sign_test_two_sided():
    # 11/12 同向:双侧 p = 2 * P(X>=11), X~Bin(12, .5) = 2*(13/4096)≈0.00635
    got = l2.sign_test_p([1] * 11 + [-1])
    want = 2 * (math.comb(12, 11) + math.comb(12, 12)) / 2 ** 12
    assert abs(got - want) < 1e-12
    assert l2.sign_test_p([1, -1, 0, 1]) == 1.0  # 平局不算向,1/2 无差异→不显著
