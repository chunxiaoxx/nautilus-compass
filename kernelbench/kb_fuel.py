"""KernelBench → 6-key 分数制燃料适配器。镜像 nautilus-v5/fde_capsule/ale_fuel_batch.py
的契约,把 KernelBench 加速比 eval 桥成蒸馏合池的 6-key record。GPU seam 后续单独加。"""
from __future__ import annotations

FUEL_KEYS = ("task_id", "problem_statement", "strong_solution",
             "strong_score", "doubao_score", "strong_verified")


def build_kb_fuel_sample(task_id, problem_statement, strong_result, doubao_speedup,
                         judge_version=None) -> dict:
    """纯:KernelBench 单题强解结果 + doubao 加速比 → 6-key 样本。
    strong_result = {"solution": str, "speedup": float, "verified": bool}。
    score_type 恒 "maximize"(加速比越大越好)。"""
    return {
        "task_id": str(task_id),
        "problem_statement": str(problem_statement),
        "strong_solution": str(strong_result.get("solution", "")),
        "strong_score": float(strong_result.get("speedup", 0.0)),
        "doubao_score": float(doubao_speedup),
        "strong_verified": bool(strong_result.get("verified", False)),
        "score_type": "maximize",
        "judge_version": str(judge_version) if judge_version else "",
    }


def is_a_class(sample: dict, rel_margin: float = 0.1) -> bool:
    """A 类(maximize·镜像 V5 ale_fuel_batch.is_a_class 语义):
    strong_verified ∧ strong>0 ∧ strong != doubao ∧ strong >= doubao*(1+rel_margin)。
    退化守卫:同分(双败)/ strong=0(没真解出)= 非 A 类(防毒燃料)。"""
    if not sample.get("strong_verified"):
        return False
    strong = float(sample["strong_score"])
    doubao = float(sample["doubao_score"])
    if strong == doubao:
        return False
    return strong > 0 and strong >= doubao * (1.0 + rel_margin)


def accumulate_kb_fuel(samples: list, existing: list) -> list:
    """纯·幂等:按 task_id dedup(同 id 取 strong_score 更高者)。不改入参。"""
    by, order = {}, []
    for s in list(existing) + list(samples):
        tid = s["task_id"]
        if tid not in by:
            by[tid] = s
            order.append(tid)
        elif float(s["strong_score"]) > float(by[tid]["strong_score"]):
            by[tid] = s
    return [by[tid] for tid in order]
