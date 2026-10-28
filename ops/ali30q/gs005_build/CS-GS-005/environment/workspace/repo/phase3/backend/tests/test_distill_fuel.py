"""中心环 Phase 1:A 类燃料判定 + 蒸馏样本装配(2026-06-22)。

北极星中心环唯一 forcing function 的第一块(本地可 TDD·不依赖 cloud)。
A 类 = 强模型解 verified-correct + 弱模型(doubao)难倒 = 蒸馏燃料 + 买方交付物(一鱼两吃)。

🎯 ALE-primary(连续打分·首选 workhorse):A 类 = 强模型分 ≫ doubao 分(连续 gap·非二元)。
二元 SWE 保留为次选/对照:强解 verified + doubao pass@5 ≤ 0.6。
三态:True(A 类)/ False(饱和·无学习 gap·拒)/ None(强模型没真解=无 trace 可蒸)。
"""
from __future__ import annotations

import pytest

from services.distill_fuel import (
    is_a_bucket, build_distill_sample, accumulate_sample, load_fuel,
    instruction_for, swe_fuel_record_from_verify, INSTRUCTION_ALE, INSTRUCTION_SWE,
)


# ── ALE 连续打分(首选) ──────────────────────────────────────────────────

def test_ale_a_bucket_when_strong_beats_doubao_by_margin():
    # 强解 verified + 分数远高于 doubao(有可蒸 headroom)→ A 类
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 850.0, "doubao_score": 400.0}
    assert is_a_bucket(rec) is True


def test_ale_not_a_bucket_when_scores_saturated():
    # 强解≈doubao(gap 太小)= 没学习信号 = 饱和拒
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 850.0, "doubao_score": 840.0}
    assert is_a_bucket(rec) is False


def test_ale_none_when_strong_unverified():
    # 强模型的解没通过验证 = 没有正确 trace 可蒸 → None(不归 A 也不归 B-拒)
    rec = {"kind": "ale", "strong_verified": False, "strong_score": 900.0, "doubao_score": 100.0}
    assert is_a_bucket(rec) is None


def test_ale_rel_margin_configurable():
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 100.0, "doubao_score": 85.0}
    assert is_a_bucket(rec, ale_rel_margin=0.1) is True    # 15% lead ≥ 10%
    assert is_a_bucket(rec, ale_rel_margin=0.3) is False   # 15% lead < 30%


# ── 毒燃料守卫(V5 实测·strong=0 = 没解出 = 非 A 类·防训"没解出"毒料) ──────

def test_ale_not_a_bucket_when_strong_zero_double_loss():
    # 🔴 strong=0 doubao=0 双败(ahc003)= qwen 没解出 = 非 A 类(否则蒸"没解出"毒料)
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 0.0, "doubao_score": 0.0}
    assert is_a_bucket(rec) is False


def test_ale_not_a_bucket_when_strong_zero_even_if_doubao_scored():
    # 🔴 strong=0(qwen 没解出有效解)即便 doubao 有分(ahc001)→ 非 A 类(无正确 trace 可蒸)
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 0.0, "doubao_score": 33e9}
    assert is_a_bucket(rec) is False


# ── ALE 打分方向(minimize 题·分越低越好·2026-06-24 confound 修复) ──────────
# 🔴 AHC 题 score_type 有 maximize/minimize 两向。旧逻辑一律按"高=好"算 rel_gap,
# 对 minimize 题:真赢(strong<doubao)被误拒、真输(strong>doubao)被误纳为毒样本。
# 0 = 无效提交/没解出(非"最优"),与方向无关(见 strong=0 守卫测试)。

def test_ale_minimize_a_bucket_when_strong_lower_than_doubao():
    # minimize:strong 分更低(成本更小)= 更优 → A 类(旧逻辑误拒)
    rec = {"kind": "ale", "score_type": "minimize", "strong_verified": True,
           "strong_score": 100.0, "doubao_score": 500.0}
    assert is_a_bucket(rec) is True


def test_ale_minimize_reject_poison_when_strong_higher_than_doubao():
    # minimize:strong 分更高(成本更大)= 更差 → 拒(旧逻辑误纳为 A 类·毒样本)
    rec = {"kind": "ale", "score_type": "minimize", "strong_verified": True,
           "strong_score": 500.0, "doubao_score": 100.0}
    assert is_a_bucket(rec) is False


def test_ale_minimize_a_bucket_when_doubao_failed():
    # minimize:doubao=0(无效·难倒) + strong 有有效解 → A 类(ahc027 实例)
    rec = {"kind": "ale", "score_type": "minimize", "strong_verified": True,
           "strong_score": 1.07e9, "doubao_score": 0.0}
    assert is_a_bucket(rec) is True


def test_ale_minimize_reject_when_strong_failed():
    # minimize:strong=0(没解出)→ 拒,无视 doubao(ahc017 实例)
    rec = {"kind": "ale", "score_type": "minimize", "strong_verified": True,
           "strong_score": 0.0, "doubao_score": 114e9}
    assert is_a_bucket(rec) is False


def test_ale_minimize_saturated_reject():
    # minimize:strong≈doubao(gap < margin)= 饱和拒
    rec = {"kind": "ale", "score_type": "minimize", "strong_verified": True,
           "strong_score": 480.0, "doubao_score": 500.0}
    assert is_a_bucket(rec) is False


def test_ale_default_maximize_when_score_type_absent():
    # 缺 score_type → 默认 maximize(向后兼容旧 records/测试)
    rec = {"kind": "ale", "strong_verified": True, "strong_score": 850.0, "doubao_score": 400.0}
    assert is_a_bucket(rec) is True


# ── 二元 SWE(次选/对照) ────────────────────────────────────────────────

def test_swe_a_bucket_strong_pass_verified_doubao_fail():
    rec = {"kind": "swe", "strong_verified": True, "strong_pass": True, "doubao_pass_at5": 0.2}
    assert is_a_bucket(rec) is True


def test_swe_not_a_bucket_when_doubao_also_passes():
    rec = {"kind": "swe", "strong_verified": True, "strong_pass": True, "doubao_pass_at5": 0.8}
    assert is_a_bucket(rec) is False  # doubao 也过 = 饱和易题


def test_swe_none_when_strong_unverified():
    rec = {"kind": "swe", "strong_verified": False, "strong_pass": True, "doubao_pass_at5": 0.0}
    assert is_a_bucket(rec) is None


# ── 蒸馏样本装配(SFT 格式) ─────────────────────────────────────────────

def test_build_distill_sample_shape():
    sample = build_distill_sample(
        task_id="ahc001_seed3", problem_statement="最小化配送总距离...",
        strong_solution="def solve(): ...", meta_extra={"benchmark": "ale", "strong_score": 850.0})
    assert sample["instruction"].strip()
    assert "最小化配送总距离" in sample["input"]
    assert sample["output"] == "def solve(): ..."
    assert sample["meta"]["task_id"] == "ahc001_seed3"
    assert sample["meta"]["benchmark"] == "ale"
    assert sample["meta"]["strong_score"] == 850.0
    assert sample["meta"]["kind"] == "ale"               # 默认 ale
    assert sample["instruction"] == INSTRUCTION_ALE


# ── SWE 同质料 eval 使能(2026-06-26·kind-threading 补齐·SWE LOO 解锁) ─────

def test_instruction_per_kind_distinct():
    # 训练/eval 同源·不同 kind 必不同措辞(防 train/eval skew)
    assert instruction_for("ale") == INSTRUCTION_ALE
    assert instruction_for("swe") == INSTRUCTION_SWE
    assert instruction_for("ale") != instruction_for("swe")
    assert instruction_for("unknown_kind") == INSTRUCTION_ALE   # 退 ALE


def test_build_distill_sample_swe_uses_swe_instruction_and_kind():
    sample = build_distill_sample(
        task_id="django__django-13220", problem_statement="QuerySet.none() ...",
        strong_solution="--- a/x.py\n+++ b/x.py\n@@ ...", kind="swe",
        meta_extra={"benchmark": "swe", "doubao_score": 0.0})
    assert sample["instruction"] == INSTRUCTION_SWE
    assert "diff" in sample["instruction"].lower()
    assert sample["meta"]["kind"] == "swe"
    assert sample["output"].startswith("--- a/x.py")


def test_swe_fuel_record_from_verify_is_a_bucket():
    # soul canonical verify 结果 → ingest-ready record → is_a_bucket(swe)=True
    rec = swe_fuel_record_from_verify(
        task_id="django__django-12113", problem_statement="bug ...",
        strong_diff="--- a\n+++ b\n@@", strong_resolved=True, doubao_resolved=False)
    assert rec["kind"] == "swe"
    assert rec["strong_verified"] is True
    assert rec["strong_pass"] is True
    assert rec["doubao_pass_at5"] == 0.0
    assert is_a_bucket(rec) is True                      # strong resolved + doubao failed = A 类


def test_swe_fuel_record_doubao_also_resolved_rejected():
    # doubao 也解出(太易)→ pass@5=1.0 > 0.6 → 饱和拒(非 A 类·判别性负例)
    rec = swe_fuel_record_from_verify(
        task_id="django__django-15498", problem_statement="bug ...",
        strong_diff="--- a", strong_resolved=True, doubao_resolved=True)
    assert rec["doubao_pass_at5"] == 1.0
    assert is_a_bucket(rec) is False


def test_swe_fuel_record_strong_not_resolved_none():
    # strong 没解对 → strong_verified=False → None(无 trace 可蒸)
    rec = swe_fuel_record_from_verify(
        task_id="x", problem_statement="bug", strong_diff="",
        strong_resolved=False, doubao_resolved=False)
    assert is_a_bucket(rec) is None


# ── 数据集累加器(jsonl·幂等去重·攒批) ──────────────────────────────────

def test_accumulate_dedups_by_task_id(tmp_path):
    p = str(tmp_path / "fuel.jsonl")
    s1 = {"meta": {"task_id": "a"}, "output": "x"}
    s2 = {"meta": {"task_id": "a"}, "output": "x2"}   # 同 task_id
    s3 = {"meta": {"task_id": "b"}, "output": "y"}
    assert accumulate_sample(p, s1) == 1
    assert accumulate_sample(p, s2) == 1              # 去重·不重复累加
    assert accumulate_sample(p, s3) == 2
    assert accumulate_sample(p, s3) == 2              # 幂等


def test_load_fuel_reads_back(tmp_path):
    p = str(tmp_path / "fuel.jsonl")
    accumulate_sample(p, {"meta": {"task_id": "a"}, "output": "x"})
    accumulate_sample(p, {"meta": {"task_id": "b"}, "output": "y"})
    rows = load_fuel(p)
    assert len(rows) == 2
    assert {r["meta"]["task_id"] for r in rows} == {"a", "b"}


def test_load_fuel_missing_file_returns_empty(tmp_path):
    assert load_fuel(str(tmp_path / "none.jsonl")) == []
