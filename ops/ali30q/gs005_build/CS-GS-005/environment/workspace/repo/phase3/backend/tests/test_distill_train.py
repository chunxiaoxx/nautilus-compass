"""齿轮⑦ 蒸馏训练/eval 纯逻辑单测(2026-06-22)· 中心环终点(从没跑过的硬事)。

蒸馏 PoC 的可 TDD 核心(无 torch/GPU):SFT 格式化 + 分数 delta + 证/杀判定。
真训练/推理(torch/peft on T4)是 GPU effect·gated·在 scripts/distill_qlora.py / distill_eval.py。
"""
from __future__ import annotations

import pytest

from services.distill_train import (
    format_sft_example,
    build_sft_texts,
    compute_score_delta,
    prove_or_kill_verdict,
    split_train_heldout,
    held_out_eval_record,
    cv_folds,
    aggregate_cv_results,
)
from services.distill_fuel import build_distill_sample


# ── held-out 按 kind 分派(SWE LOO 使能·2026-06-26):held-out record 必带 kind ──

def test_held_out_eval_record_carries_kind_swe():
    # SWE sample → held-out record 带 kind=swe(distill_eval/score_solution 据此走 docker)
    sample = build_distill_sample(
        task_id="django__django-13220", problem_statement="bug ...",
        strong_solution="--- a\n+++ b", kind="swe", meta_extra={"doubao_score": 0.0})
    rec = held_out_eval_record(sample)
    assert rec["task_id"] == "django__django-13220"
    assert rec["kind"] == "swe"
    assert rec["problem_statement"].startswith("bug")


def test_held_out_eval_record_defaults_ale():
    sample = build_distill_sample(
        task_id="ahc001", problem_statement="opt", strong_solution="def f(): ...")
    rec = held_out_eval_record(sample)
    assert rec["kind"] == "ale"


# ── held-out 设计(首证从 A 类 split·同分布甜点题·非难题测不出) ──────────

def test_split_train_heldout_deterministic_30pct():
    samples = [{"meta": {"task_id": f"t{i:02d}"}} for i in range(12)]
    train, held = split_train_heldout(samples)
    assert len(held) == 4 and len(train) == 8            # 30% of 12
    t2, h2 = split_train_heldout(samples)                # 确定性可复现
    assert [s["meta"]["task_id"] for s in held] == [s["meta"]["task_id"] for s in h2]
    assert not ({s["meta"]["task_id"] for s in train} &  # train/held 不重叠
                {s["meta"]["task_id"] for s in held})


def test_split_respects_min_heldout_for_tiny_set():
    samples = [{"meta": {"task_id": f"t{i}"}} for i in range(5)]   # 30%→2·但 min 3
    train, held = split_train_heldout(samples)
    assert len(held) == 3 and len(train) == 2


def test_held_out_eval_record_maps_sample_to_eval_format():
    # A 类 sample → distill_eval held-out 格式(task_id/problem_statement/doubao_score)
    s = {"input": "AHC opt problem", "output": "sol",
         "meta": {"task_id": "ahc015", "doubao_score": 0.0}}
    r = held_out_eval_record(s)
    assert r["task_id"] == "ahc015"
    assert r["problem_statement"] == "AHC opt problem"
    assert r["doubao_score"] == 0.0


# ── LOO / k-fold 交叉验证(稀缺料榨干 held-out 信号) ─────────────────────

def test_cv_folds_leave_one_out():
    samples = [{"meta": {"task_id": f"t{i}"}} for i in range(4)]
    folds = cv_folds(samples)                              # LOO(k=None)
    assert len(folds) == 4
    for train, held in folds:
        assert len(held) == 1 and len(train) == 3
    held_ids = sorted(h["meta"]["task_id"] for _, held in folds for h in held)
    assert held_ids == ["t0", "t1", "t2", "t3"]            # 每样本恰留出一次


def test_cv_folds_kfold():
    samples = [{"meta": {"task_id": f"t{i}"}} for i in range(6)]
    folds = cv_folds(samples, k=3)
    assert len(folds) == 3
    for train, held in folds:
        assert len(held) == 2 and len(train) == 4
    held_ids = sorted(h["meta"]["task_id"] for _, held in folds for h in held)
    assert held_ids == [f"t{i}" for i in range(6)]


def test_cv_folds_deterministic_and_too_few():
    samples = [{"meta": {"task_id": f"t{i}"}} for i in range(5)]
    assert cv_folds(samples, k=2) == cv_folds(samples, k=2)   # 确定性
    assert cv_folds([{"meta": {"task_id": "a"}}]) == []        # N<2 无法 CV


def test_aggregate_cv_results_flattens_and_scores():
    fold_results = [
        [{"task_id": "a", "distilled": 800, "base": 600, "doubao": 400}],
        [{"task_id": "b", "distilled": 900, "base": 700, "doubao": 500}],
    ]
    d = aggregate_cv_results(fold_results)
    assert d["n"] == 2                                     # N 折聚合 = N 评测
    assert d["win_rate_vs_base"] == pytest.approx(1.0)


# ── SFT 格式化 ──────────────────────────────────────────────────────────

def test_format_sft_example_has_instruction_input_response():
    sample = {"instruction": "Solve.", "input": "optimize X", "output": "def solve(): ..."}
    text = format_sft_example(sample)
    assert "Solve." in text
    assert "optimize X" in text
    assert "def solve(): ..." in text
    # response 段在 input 之后(训练目标在末尾)
    assert text.index("optimize X") < text.index("def solve(): ...")


def test_build_sft_texts_maps_all_rows():
    rows = [
        {"instruction": "i1", "input": "in1", "output": "out1"},
        {"instruction": "i2", "input": "in2", "output": "out2"},
    ]
    texts = build_sft_texts(rows)
    assert len(texts) == 2
    assert "out1" in texts[0] and "out2" in texts[1]


# ── 分数 delta(连续·ALE 友好) ──────────────────────────────────────────

def test_compute_score_delta_win_rate_and_uplift():
    # 3 题:蒸馏后都比 base 高 → win_rate=1.0·正 uplift
    per_task = [
        {"task_id": "a", "distilled": 800, "base": 600, "doubao": 400},
        {"task_id": "b", "distilled": 900, "base": 700, "doubao": 500},
        {"task_id": "c", "distilled": 750, "base": 700, "doubao": 600},
    ]
    d = compute_score_delta(per_task)
    assert d["win_rate_vs_base"] == pytest.approx(1.0)
    assert d["mean_rel_uplift_vs_base"] > 0
    assert d["win_rate_vs_doubao"] == pytest.approx(1.0)
    assert d["n"] == 3


def test_compute_score_delta_no_improvement():
    per_task = [
        {"task_id": "a", "distilled": 590, "base": 600, "doubao": 400},
        {"task_id": "b", "distilled": 700, "base": 700, "doubao": 500},
    ]
    d = compute_score_delta(per_task)
    assert d["win_rate_vs_base"] == pytest.approx(0.0)  # 没一题更高(< 或 =)


def test_compute_score_delta_empty():
    d = compute_score_delta([])
    assert d["n"] == 0
    assert d["win_rate_vs_base"] == 0.0
    assert d["distilled_valid_rate"] == 0.0          # graded 键也在(空)
    assert d["near_base_rate"] == 0.0


# ── graded 信号(6/23·held-out KILLED 教训·区分垃圾0分 vs 有效但低) ──────

def test_graded_distinguishes_garbage_from_partial_generalization():
    # 两个场景 win_rate_vs_base 都 = 0(没一题严格赢 base)·但 graded 截然不同:
    # 场景1=held-out KILLED(distilled 全 0·啥有效解都没产)
    killed = compute_score_delta([
        {"task_id": "a", "distilled": 0, "base": 500, "doubao": 400},
        {"task_id": "b", "distilled": 0, "base": 600, "doubao": 300},
    ])
    # 场景2=早期/部分泛化(distilled 产有效解·接近 base 但没超)
    partial = compute_score_delta([
        {"task_id": "a", "distilled": 450, "base": 500, "doubao": 400},
        {"task_id": "b", "distilled": 540, "base": 600, "doubao": 300},
    ])
    assert killed["win_rate_vs_base"] == 0.0 and partial["win_rate_vs_base"] == 0.0  # binary 一样
    # graded 区分开:
    assert killed["distilled_valid_rate"] == 0.0     # 全垃圾·没产有效解
    assert partial["distilled_valid_rate"] == 1.0    # 都产了有效解
    assert killed["near_base_rate"] == 0.0           # 离 base 远
    assert partial["near_base_rate"] == 1.0          # 都 ≥80% base = 部分泛化


def test_graded_valid_rate_and_base_valid_rate():
    d = compute_score_delta([
        {"task_id": "a", "distilled": 100, "base": 0, "doubao": 0},    # base 题本身没解出
        {"task_id": "b", "distilled": 0, "base": 200, "doubao": 0},    # distilled 没产
    ])
    assert d["distilled_valid_rate"] == 0.5
    assert d["base_valid_rate"] == 0.5


def test_graded_near_base_rate_only_over_base_positive():
    # near_base_rate 只在 base>0 题上算(base=0 题"接近"无意义)
    d = compute_score_delta([
        {"task_id": "a", "distilled": 90, "base": 100, "doubao": 0},   # 90>=80 → near
        {"task_id": "b", "distilled": 50, "base": 100, "doubao": 0},   # 50<80 → not
        {"task_id": "c", "distilled": 5, "base": 0, "doubao": 0},      # base=0·不计入分母
    ])
    assert d["near_base_rate"] == pytest.approx(0.5)   # 1/2(只 a,b 计入·a near)


# ── 证/杀判定(forcing function 决策门) ─────────────────────────────────

def test_verdict_proven_when_strong_uplift():
    delta = {"win_rate_vs_base": 0.8, "mean_rel_uplift_vs_base": 0.15, "n": 50}
    assert prove_or_kill_verdict(delta) == "PROVEN"


def test_verdict_killed_when_no_better_than_base():
    delta = {"win_rate_vs_base": 0.45, "mean_rel_uplift_vs_base": -0.01, "n": 50}
    assert prove_or_kill_verdict(delta) == "KILLED"


def test_verdict_inconclusive_middle():
    delta = {"win_rate_vs_base": 0.55, "mean_rel_uplift_vs_base": 0.02, "n": 50}
    assert prove_or_kill_verdict(delta) == "INCONCLUSIVE"


def test_verdict_inconclusive_when_too_few_samples():
    delta = {"win_rate_vs_base": 0.9, "mean_rel_uplift_vs_base": 0.2, "n": 3}
    # 样本太少 → 不下结论(诚实·不被小样本运气骗)
    assert prove_or_kill_verdict(delta, min_n=20) == "INCONCLUSIVE"
