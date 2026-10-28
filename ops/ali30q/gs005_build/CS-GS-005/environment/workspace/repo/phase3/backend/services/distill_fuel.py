"""中心环 Phase 1:A 类燃料判定 + 蒸馏样本装配(2026-06-22)。

北极星唯一中心环(`docs/NORTH_STAR_20260622.md`)forcing function 的写端第一块:
把"强模型解 verified-correct + 弱模型(doubao)难倒"的题判为 A 类,装配成蒸馏 SFT 样本。
A 类 trace = 蒸馏燃料 + 买方交付物(一鱼两吃)。纯逻辑·无 DB/IO·本地可 TDD。

🎯 ALE-primary(连续打分·首选 workhorse·arXiv 2506.09050):A 类 = 强模型分 ≫ doubao 分
(连续 gap·解 reward 饱和·原生 RSI headroom)。二元 SWE 次选/对照:强解 verified +
doubao pass@5 ≤ 0.6(买方口径)。

三态(诚实):
  True  = A 类(强解 verified + 有可蒸学习 gap)
  False = 拒(饱和·doubao 也好·无学习信号)
  None  = 强模型没真解对(无正确 trace 可蒸·归 B 类/丢·非 A 非"饱和拒")
"""
from __future__ import annotations

import json
import os
from typing import Optional

# 买方口径(charter §1.3):第3类难倒 = pass@5 ≤ 0.6 on doubao 2.0
_DOUBAO_STUMP_PASS_AT5 = 0.6
# ALE 默认相对 gap 门(强模型分至少领先 doubao 20%·有可蒸 headroom)
_DEFAULT_ALE_REL_MARGIN = 0.2

# 🔴 蒸馏 prompt instruction(单一来源·训练/eval 共用·防 train/eval skew):
# 2026-06-23 实证 KILLED 假象根因 = 训练用 A、eval 用 B → 条件分布对不上吐不出记住的解。
# build_distill_sample(训练写端)与 _distill_runtime.generate_solution(eval 推理端)都从
# 此处取 instruction → 同一 kind 必同措辞。SWE = 修 bug 输出 unified diff;ALE = 优化题。
INSTRUCTION_ALE = ("Solve the following algorithm engineering / optimization problem. "
                   "Produce a correct, high-scoring solution.")
INSTRUCTION_SWE = ("Fix the software bug described in the issue below. "
                   "Output a unified diff (git patch) that resolves it.")
_INSTRUCTION_BY_KIND = {"ale": INSTRUCTION_ALE, "swe": INSTRUCTION_SWE}


def instruction_for(kind: str) -> str:
    """kind → 蒸馏 instruction(训练/eval 共用·未知 kind 退 ALE)。"""
    return _INSTRUCTION_BY_KIND.get(kind, INSTRUCTION_ALE)


def is_a_bucket(
    rec: dict,
    ale_rel_margin: float = _DEFAULT_ALE_REL_MARGIN,
    doubao_stump_pass_at5: float = _DOUBAO_STUMP_PASS_AT5,
) -> Optional[bool]:
    """判 A 类(三态)。kind='ale'(连续·首选)/ 'swe'(二元·次选)。

    None = 强模型未 verified(无正确 trace 可蒸)。先判,与 kind 无关。
    """
    if not rec.get("strong_verified"):
        return None

    kind = rec.get("kind", "ale")

    if kind == "ale":
        strong = float(rec.get("strong_score") or 0.0)
        doubao = float(rec.get("doubao_score") or 0.0)
        # AHC 题有 maximize/minimize 两向;缺省 maximize(向后兼容旧 records)。
        # 0 = 无效提交/没解出(非"最优"),与方向无关。
        score_type = rec.get("score_type", "maximize")
        if strong <= 0:
            return False  # strong 没解出有效解 → 无正确 trace 可蒸
        if doubao <= 0:
            return True   # strong 解出 + doubao 失败(0=无效·难倒)→ A 类·方向无关
        # 两侧都有有效解 → 按方向算相对 gap:strong 须明显更优才有可蒸 headroom
        if score_type == "minimize":
            rel_gap = (doubao - strong) / doubao   # minimize:strong 分越低越优
        else:
            rel_gap = (strong - doubao) / strong   # maximize:strong 分越高越优
        return rel_gap >= ale_rel_margin

    if kind == "swe":
        if not rec.get("strong_pass"):
            return False
        doubao_pass = float(rec.get("doubao_pass_at5") or 0.0)
        # doubao 难倒(pass@5 ≤ 阈值)= A 类;doubao 也过 = 饱和拒
        return doubao_pass <= doubao_stump_pass_at5

    # 未知 kind 保守拒(不冤枉成 A 类)
    return False


def build_distill_sample(
    task_id: str,
    problem_statement: str,
    strong_solution: str,
    meta_extra: Optional[dict] = None,
    kind: str = "ale",
) -> dict:
    """A 类题 → 蒸馏 SFT 样本(instruction/input/output/meta)。

    output = 强模型 verified 解(蒸进开源小模型的目标)。
    kind 决定 instruction(SWE=修 bug→diff·ALE=优化题)·并写入 meta 供 held-out eval
    按 kind 分派打分(ALE scorer vs SWE docker)。instruction 与 eval 推理端同源(instruction_for)。
    """
    return {
        "instruction": instruction_for(kind),
        "input": problem_statement,
        "output": strong_solution,
        "meta": {"task_id": task_id, "kind": kind, **(meta_extra or {})},
    }


def swe_fuel_record_from_verify(
    task_id: str,
    problem_statement: str,
    strong_diff: str,
    strong_resolved: bool,
    doubao_resolved: bool,
    doubao_diff: str = "",
) -> dict:
    """canonical-verified SWE 结果 → ingest_fuel_records 可吃的 record(soul turf 归一化)。

    V5 producer 输出只有 task_id/strong_solution/doubao_solution/kind。soul canonical verify
    (verify_pathA_one·官方 docker)定出 strong/doubao 是否 resolved → 此处补 is_a_bucket(swe)
    所需字段(strong_verified/strong_pass/doubao_pass_at5)。doubao 二元:resolved→pass@5=1.0
    (≥0.6 会被判饱和拒·正确)·failed→0.0。doubao_score=0.0(SWE 二元·held-out doubao 分)。
    """
    return {
        "task_id": task_id,
        "kind": "swe",
        "problem_statement": problem_statement,
        "strong_solution": strong_diff,
        "doubao_solution": doubao_diff,
        "strong_verified": bool(strong_resolved),
        "strong_pass": bool(strong_resolved),
        "doubao_pass_at5": 1.0 if doubao_resolved else 0.0,
        "doubao_score": 0.0,
        "judge_version": "swebench",
    }


# ── 数据集累加器(jsonl·按 meta.task_id 幂等去重) ───────────────────────

def load_fuel(path: str) -> list[dict]:
    """读 A 类燃料 jsonl → list。缺文件 → []。"""
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def accumulate_sample(path: str, sample: dict) -> int:
    """append A 类样本到 jsonl·按 meta.task_id 去重·返回累计总数(幂等)。"""
    rows = load_fuel(path)
    seen = {r.get("meta", {}).get("task_id") for r in rows}
    tid = sample.get("meta", {}).get("task_id")
    if tid not in seen:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(sample, ensure_ascii=False) + "\n")
        return len(rows) + 1
    return len(rows)
