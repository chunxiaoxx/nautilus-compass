"""齿轮③ verdict 语义守卫单测(2026-06-22)。

compass 实测齿轮③语义混:两套口径混用同一 overall_pass。
- stump_gate(难倒门 pass):score=0 + pass=true 合法(doubao pass@k=0=最难倒·买方 stump 验收)。
- solver_correctness(解对 pass):score=0 必 pass=false(bvh_001 类 bug:解错却 pass=true)。

守卫:solver_correctness 路径强制 score=0→pass=false;stump_gate 不动;无 verdict_kind 不臆断。
"""
from __future__ import annotations

from services.fde_verdict_guard import apply_verdict_kind_guard


def test_solver_correctness_score0_forces_pass_false():
    body = {"verdict_kind": "solver_correctness", "score": 0, "overall_pass": True}
    out = apply_verdict_kind_guard(dict(body))
    assert out["overall_pass"] is False        # bvh 类不再发生


def test_solver_correctness_nonzero_score_unchanged():
    body = {"verdict_kind": "solver_correctness", "score": 0.8, "overall_pass": True}
    out = apply_verdict_kind_guard(dict(body))
    assert out["overall_pass"] is True


def test_stump_gate_score0_pass_true_is_valid_unchanged():
    # 难倒门:score=0(doubao 全败=最难倒)+ pass=true 合法·不动
    body = {"verdict_kind": "stump_gate", "score": 0, "overall_pass": True}
    out = apply_verdict_kind_guard(dict(body))
    assert out["overall_pass"] is True


def test_no_verdict_kind_backward_compat_unchanged():
    # 无 verdict_kind(历史 verdict)→ 不臆断·不动
    body = {"score": 0, "overall_pass": True}
    out = apply_verdict_kind_guard(dict(body))
    assert out["overall_pass"] is True


def test_solver_correctness_already_false_unchanged():
    body = {"verdict_kind": "solver_correctness", "score": 0, "overall_pass": False}
    out = apply_verdict_kind_guard(dict(body))
    assert out["overall_pass"] is False
