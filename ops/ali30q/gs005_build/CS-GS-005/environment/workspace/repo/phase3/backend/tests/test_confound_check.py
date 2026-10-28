"""confound-check 旁注单测(2026-06-23·V5 confound-check 观测原则落地)。

任何 KILLED/失败 verdict 信之前先过 confound-check(4 次救命:adapter没存/seq截断/进程死/
prompt-skew)。本模块纯逻辑·各阶段守卫顺手填·conductor pulse 汇聚。
"""
from __future__ import annotations

import pytest

from services.confound_check import (
    eval_confound_checks,
    token_truncate_flags,
    unresolved_confounds,
)


# ── eval 阶段:adapter 生效 + 解非空 ──────────────────────────────────────

def test_eval_confound_adapter_effective_when_distilled_differs():
    # distilled 解 ≠ base 解(长度不同)= adapter 真加载了
    row = {"task_id": "ahc015", "base_len": 1345, "distilled_len": 4655,
           "base": 0.0, "distilled": 17872786.0}
    c = eval_confound_checks(row)
    assert c["adapter_effective"]["ok"] is True
    assert c["solution_nonempty"]["ok"] is True


def test_eval_confound_flags_adapter_noop_when_identical():
    # distilled_len == base_len 逐字符相同 = adapter 没生效(2026-06-22 真 bug)
    row = {"task_id": "x", "base_len": 1345, "distilled_len": 1345,
           "base": 0.0, "distilled": 0.0}
    c = eval_confound_checks(row)
    assert c["adapter_effective"]["ok"] is False


def test_eval_confound_flags_empty_solution():
    row = {"task_id": "x", "base_len": 1200, "distilled_len": 3,
           "base": 0.0, "distilled": 0.0}
    c = eval_confound_checks(row)
    assert c["solution_nonempty"]["ok"] is False


# ── 燃料阶段:token 截断风险(训练前过滤超长题) ─────────────────────────

def test_token_truncate_flags_marks_overlong():
    # prob+sol token > max_seq → 解尾被截(ahc008 6170>4096 真案例)
    recs = [
        {"task_id": "ahc015", "problem_statement": "x" * 7301, "strong_solution": "y" * 4269},
        {"task_id": "ahc008", "problem_statement": "x" * 11000, "strong_solution": "y" * 10278},
    ]
    flags = token_truncate_flags(recs, max_seq=4096, chars_per_tok=3.48)
    by_id = {f["task_id"]: f for f in flags}
    assert by_id["ahc008"]["truncate_risk"] is True       # ~6000 tok > 4096
    assert by_id["ahc015"]["truncate_risk"] is False       # ~3300 tok < 4096


# ── 汇聚:未排除的 confound(conductor pulse 用) ──────────────────────────

def test_unresolved_confounds_lists_failed_checks():
    eval_result = {"verdict": "KILLED", "per_task": [
        {"task_id": "x", "confound_checks": {
            "adapter_effective": {"ok": False, "note": "distilled==base"},
            "solution_nonempty": {"ok": True, "note": ""}}},
    ]}
    unresolved = unresolved_confounds(eval_result)
    assert any("adapter_effective" in u for u in unresolved)
    assert len(unresolved) == 1


def test_unresolved_confounds_empty_when_all_ok():
    eval_result = {"verdict": "KILLED", "per_task": [
        {"task_id": "x", "confound_checks": {
            "adapter_effective": {"ok": True, "note": ""},
            "solution_nonempty": {"ok": True, "note": ""}}},
    ]}
    assert unresolved_confounds(eval_result) == []
