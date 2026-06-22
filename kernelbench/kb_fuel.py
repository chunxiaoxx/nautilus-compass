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
