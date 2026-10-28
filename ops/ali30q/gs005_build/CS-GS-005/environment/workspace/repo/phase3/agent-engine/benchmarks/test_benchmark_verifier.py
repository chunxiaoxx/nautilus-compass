"""W-V soul benchmark verifier底座 — the compass-callable judging interface.

The 验证器 + 判分 the buyer calls "核心资产": judge one solution trajectory pass/fail
(RUBRIC checklist OR SWE-bench resolve), aggregate N attempts into the unbiased
pass@k estimator (Chen et al. 2021), and mark "难倒模型" tasks (e.g. doubao 2.0
pass ≤ 3/5). Reuses escape_noise_stats for the paired arm comparison; this module
adds the pass@k + hard-task layer compass benchmark env plugs into.
"""
from __future__ import annotations

import math

from benchmark_verifier import (
    pass_at_k,
    pass_at_k_from_results,
    judge_trajectory,
    is_hard_for_model,
    aggregate_task,
)


# ── pass@k (unbiased estimator) ───────────────────────────────────────────

def test_pass_at_k_all_correct_is_one():
    assert pass_at_k(n=5, c=5, k=1) == 1.0
    assert pass_at_k(n=5, c=5, k=5) == 1.0


def test_pass_at_k_none_correct_is_zero():
    assert pass_at_k(n=5, c=0, k=1) == 0.0
    assert pass_at_k(n=5, c=0, k=5) == 0.0


def test_pass_at_1_equals_pass_rate():
    assert pass_at_k(n=5, c=1, k=1) == 0.2
    assert pass_at_k(n=5, c=2, k=1) == 0.4


def test_pass_at_k_unbiased_value():
    # n=5, c=1, k=5: can't avoid the one correct → 1.0
    assert pass_at_k(n=5, c=1, k=5) == 1.0
    # n=4, c=1, k=2: 1 - C(3,2)/C(4,2) = 1 - 3/6 = 0.5
    assert math.isclose(pass_at_k(n=4, c=1, k=2), 0.5, rel_tol=1e-9)


def test_pass_at_k_k_larger_than_n_clamps_to_n():
    # asking pass@10 with only 5 samples → evaluate at k=n=5
    assert pass_at_k(n=5, c=1, k=10) == 1.0
    assert pass_at_k(n=5, c=0, k=10) == 0.0


def test_pass_at_k_from_results_bools():
    results = [True, False, False, False, False]  # 1/5 correct
    assert pass_at_k_from_results(results, k=1) == 0.2
    assert pass_at_k_from_results(results, k=5) == 1.0


# ── judge_trajectory (unify RUBRIC + resolve into pass/fail) ───────────────

def test_judge_trajectory_resolve_mode():
    assert judge_trajectory(True, mode="resolve")["pass"] is True
    assert judge_trajectory(False, mode="resolve")["pass"] is False


def test_judge_trajectory_rubric_mode_reads_overall_pass():
    scored = {"overall_pass": True, "veto_failed": False, "score": 1.0}
    assert judge_trajectory(scored, mode="rubric")["pass"] is True
    vetoed = {"overall_pass": False, "veto_failed": True, "score": 0.5}
    assert judge_trajectory(vetoed, mode="rubric")["pass"] is False


def test_judge_trajectory_unknown_mode_raises():
    try:
        judge_trajectory(True, mode="nonsense")
        assert False, "should raise on unknown mode"
    except ValueError:
        pass


# ── 难倒标注 (hard-for-model) ──────────────────────────────────────────────

def test_is_hard_when_pass_count_at_or_below_threshold():
    # buyer: doubao 2.0 pass ≤ 3/5 → 难倒 (hard)
    assert is_hard_for_model(c=3, n=5, max_pass=3) is True
    assert is_hard_for_model(c=2, n=5, max_pass=3) is True
    assert is_hard_for_model(c=0, n=5, max_pass=3) is True


def test_is_not_hard_when_pass_count_above_threshold():
    assert is_hard_for_model(c=4, n=5, max_pass=3) is False
    assert is_hard_for_model(c=5, n=5, max_pass=3) is False


# ── aggregate_task (per-task verdict the compass env consumes) ─────────────

def test_aggregate_task_resolve_results():
    # 5 attempts, 1 resolved → pass@1=0.2, pass@5=1.0, hard (1≤3)
    agg = aggregate_task("swe_001", [True, False, False, False, False],
                         mode="resolve", k_values=(1, 5), max_pass=3)
    assert agg["task_uid"] == "swe_001"
    assert agg["n"] == 5 and agg["c"] == 1
    assert agg["pass_at_k"]["1"] == 0.2
    assert agg["pass_at_k"]["5"] == 1.0
    assert agg["hard_for_model"] is True


def test_aggregate_task_rubric_results():
    trajectories = [
        {"overall_pass": True, "score": 1.0},
        {"overall_pass": False, "veto_failed": True, "score": 0.5},
        {"overall_pass": True, "score": 0.9},
    ]
    agg = aggregate_task("data_002", trajectories, mode="rubric",
                         k_values=(1,), max_pass=1)
    assert agg["n"] == 3 and agg["c"] == 2
    assert math.isclose(agg["pass_at_k"]["1"], 2 / 3, rel_tol=1e-9)
    assert agg["hard_for_model"] is False  # c=2 > max_pass=1


def test_aggregate_task_empty_is_safe():
    agg = aggregate_task("empty", [], mode="resolve")
    assert agg["n"] == 0 and agg["c"] == 0
    assert agg["pass_at_k"]["1"] == 0.0
    assert agg["hard_for_model"] is True  # 0 ≤ default threshold → 难倒


# ── mode='score' (连续 reward → pass@k + 保留连续分布 · cnt_c1 compass 提案) ──

def test_judge_trajectory_score_mode_binarizes_at_threshold():
    assert judge_trajectory(0.6, mode="score", threshold=0.5)["pass"] is True
    assert judge_trajectory(0.4, mode="score", threshold=0.5)["pass"] is False
    assert judge_trajectory(0.5, mode="score", threshold=0.5)["pass"] is True  # >=
    assert judge_trajectory(0.282, mode="score", threshold=0.5)["reward"] == 0.282


def test_aggregate_task_score_mode_passk_and_reward_stats():
    # AutoLab radix_sort compass 实测三候选 reward: 0.0 / 0.204 / 0.282
    agg = aggregate_task("autolab_radix_sort", [0.0, 0.204, 0.282],
                         mode="score", k_values=(1, 3), max_pass=3, threshold=0.5)
    assert agg["n"] == 3 and agg["c"] == 0          # 无一达 0.5 强人类锚
    assert agg["pass_at_k"]["1"] == 0.0
    assert agg["hard_for_model"] is True
    rs = agg["reward_stats"]
    assert math.isclose(rs["mean"], (0.0 + 0.204 + 0.282) / 3, rel_tol=1e-9)
    assert rs["best"] == 0.282
    assert rs["min"] == 0.0
    assert rs["per_reward"] == [0.0, 0.204, 0.282]
    assert rs["threshold"] == 0.5


def test_aggregate_task_score_lower_threshold_passes_more():
    # 低门 reward>0(compass 二值化曾用)→ c=2
    agg = aggregate_task("t", [0.0, 0.204, 0.282], mode="score",
                         k_values=(1,), threshold=0.0001)
    assert agg["c"] == 2


def test_aggregate_task_resolve_unaffected_no_reward_stats():
    # 向后兼容:resolve 不受新 threshold 参数影响·无 reward_stats
    agg = aggregate_task("swe", [True, False], mode="resolve", k_values=(1,))
    assert agg["c"] == 1
    assert "reward_stats" not in agg
