"""中心环 Phase 1 Task 3:A 类燃料 minting 编排(2026-06-22)。

纯编排核心(注入 seam·effect 在工厂里):基准实例 → 强模型解+验证 → doubao 难倒度
→ `is_a_bucket` 三态 → A 类装 SFT 样本 sink。三桶计数 + fail-soft per 实例。

复用现成分拣口径(`services.distill_fuel.is_a_bucket`)·不重写。ALE-primary(连续打分·
强分≫doubao 分)+ SWE(二元·doubao pass@5≤0.6)两路由 kind 选。

生产 seam(strong_fn/doubao_fn/problem_fn)在 runner 工厂注入(强模型 API/doubao ARK/
benchmark scorer)·本编排核可纯单测、无 IO/GPU。
"""
from __future__ import annotations

from typing import Callable, Iterable, Optional

from services.distill_fuel import is_a_bucket, build_distill_sample


def _build_rec(kind: str, strong: dict, doubao: dict) -> dict:
    """强模型 + doubao 结果 → is_a_bucket 输入 rec。"""
    rec = {"kind": kind, "strong_verified": bool(strong.get("verified"))}
    if kind == "ale":
        rec["strong_score"] = strong.get("score")
        rec["doubao_score"] = doubao.get("score")
    else:  # swe 二元
        rec["strong_pass"] = bool(strong.get("passed") or strong.get("pass"))
        rec["doubao_pass_at5"] = doubao.get("pass_at5")
    return rec


def mint_batch(
    instances: Iterable[str],
    strong_fn: Callable[[str], dict],
    doubao_fn: Callable[[str], dict],
    kind: str = "ale",
    problem_fn: Callable[[str], str] = lambda i: "",
    sink: Callable[[dict], None] = lambda s: None,
    ale_rel_margin: float = 0.2,
) -> dict:
    """对实例批跑 minting pass → A 类装样本 sink。三桶 + fail-soft。

    Args:
        instances: 基准实例 id 列表(ALE seed / SWE instance_id)。
        strong_fn: ``i -> {solution, score|passed, verified}``(强模型解+验证)。
        doubao_fn: ``i -> {score|pass_at5}``(弱模型难倒度)。
        kind: 'ale'(连续·首选)/ 'swe'(二元)。
        problem_fn: ``i -> problem_statement``(装样本 input 用)。
        sink: A 类样本回调(accumulate_sample 包一层)。

    Returns:
        ``{a_bucket:[id…], rejected:[id…](饱和), b_bucket:[id…](强未解·无trace),
           errored:[id…](异常)}``。
    """
    a_bucket: list[str] = []
    rejected: list[str] = []
    b_bucket: list[str] = []
    errored: list[str] = []

    for inst in instances:
        try:
            strong = strong_fn(inst)
            doubao = doubao_fn(inst)
            rec = _build_rec(kind, strong, doubao)
            verdict = is_a_bucket(rec, ale_rel_margin=ale_rel_margin)
        except Exception:  # fail-soft: 一道崩不中断整批
            errored.append(inst)
            continue

        if verdict is True:
            sample = build_distill_sample(
                task_id=inst,
                problem_statement=problem_fn(inst),
                strong_solution=strong.get("solution", ""),
                meta_extra={"benchmark": kind, **{k: strong.get(k)
                            for k in ("score", "passed") if k in strong}},
            )
            sink(sample)
            a_bucket.append(inst)
        elif verdict is False:
            rejected.append(inst)
        else:  # None = 强模型没真解 verified = 无 trace 可蒸 = B 桶(护城河非燃料)
            b_bucket.append(inst)

    return {"a_bucket": a_bucket, "rejected": rejected,
            "b_bucket": b_bucket, "errored": errored}


def ingest_fuel_records(
    records: Iterable[dict],
    kind: str = "ale",
    sink: Callable[[dict], None] = lambda s: None,
    ale_rel_margin: float = 0.2,
) -> dict:
    """消费**预算好的** producer 输出 record(V5 ALE harness 格式)→ A 类装样本。

    V5 `_run_ale_2turn` 批量 harness 每题输出:
      ``{task_id, problem_statement, strong_solution, strong_score, doubao_score, strong_verified}``
    (SWE 对照轨:strong_pass/doubao_pass_at5)。与 mint_batch 不同:records 已含强解+分数,
    无需 fn 回调,直接判定累加。复用 is_a_bucket / build_distill_sample。三桶 + fail-soft。
    """
    a_bucket: list[str] = []
    rejected: list[str] = []
    b_bucket: list[str] = []
    errored: list[str] = []

    for r in records:
        try:
            tid = r["task_id"]
            k = r.get("kind", kind)   # per-record kind(多基准合池)·缺则整批默认
            rec = {"kind": k, "strong_verified": r.get("strong_verified")}
            if k == "ale":
                rec["strong_score"] = r.get("strong_score")
                rec["doubao_score"] = r.get("doubao_score")
            else:
                rec["strong_pass"] = r.get("strong_pass") or r.get("passed")
                rec["doubao_pass_at5"] = r.get("doubao_pass_at5")
            verdict = is_a_bucket(rec, ale_rel_margin=ale_rel_margin)
        except Exception:  # fail-soft: 坏 record 不中断
            errored.append(r.get("task_id"))
            continue

        if verdict is True:
            sample = build_distill_sample(
                task_id=tid,
                problem_statement=r.get("problem_statement", ""),
                strong_solution=r.get("strong_solution", ""),
                kind=k,
                meta_extra={"benchmark": k,
                            "strong_score": r.get("strong_score"),
                            "doubao_score": r.get("doubao_score"),
                            # 全链锁同版审计锚:燃料 minting 的 judge_version 必须 ==
                            # distill_eval 的 judge_version(否则分数 delta 不可比)。
                            "judge_version": r.get("judge_version"),
                            "score_type": r.get("score_type")},
            )
            sink(sample)
            a_bucket.append(tid)
        elif verdict is False:
            rejected.append(tid)
        else:
            b_bucket.append(tid)

    return {"a_bucket": a_bucket, "rejected": rejected,
            "b_bucket": b_bucket, "errored": errored}


def fuel_rate(records, kind: str = "ale",
              margin: float = 0.2, min_n: int = 12) -> dict:
    """中心环 Q3:records → A 类燃料率 + 是否够首证(纯·薄包 ingest_fuel_records)。

    min_n=12:首证阈值(2026-06-22 降 20→12·ALE+qwen 真 A 类产率低 ~1/4·V5 估~10·
    用户拍 10-15·取 12)。首证看 distill_eval delta 方向(证/杀)·不必卡满 20。
    enough_for_poc=False → 燃料不够,扩题/调 margin/换 producer。
    """
    recs = list(records)
    res = ingest_fuel_records(recs, kind=kind, ale_rel_margin=margin)
    n_a = len(res["a_bucket"])
    total = len(recs)
    return {
        "total": total,
        "a_bucket": n_a,
        "rejected": len(res["rejected"]),
        "b_bucket": len(res["b_bucket"]),
        "errored": len(res["errored"]),
        "a_rate": (n_a / total) if total else 0.0,
        "min_n": min_n,
        "enough_for_poc": n_a >= min_n,
        "a_task_ids": res["a_bucket"],
    }
