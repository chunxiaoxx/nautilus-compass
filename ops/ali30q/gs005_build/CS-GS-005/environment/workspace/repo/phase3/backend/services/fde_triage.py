"""S-诊断 三桶分类器(RSI 蒸馏飞轮 gate · 2026-06-14 设计 §1+§4 · platform-soul turf)。

纯函数 · 无外部依赖。消费 compass benchmark_verifier 产的 doubao pass@大k 聚合,
分成决定后续路线的四桶。这一步是 gate:"决定后面所有路线有没有意义"。

输入契约(每题·platform-soul 提出·compass 对齐):
  {
    "task_uid": str,
    "n_samples": int,            # doubao 高温采样数(50~250)
    "n_passed": int,             # 完整通过验证器(correctness + 所有门)
    "n_correct_but_gated": int,  # 答案正确但被非正确性门(perf >2×/format)拒 = 洗门信号
    "pass_at_1": float | None,   # 可选;缺省用 n_passed/n_samples 估
  }

四桶:
  true_wall     pass@大k=0 且无洗门          → 蒸馏候选(唯一破墙机制)
  pseudo_wall   pass@大k>0 但 pass@1 低       → best-of-N/verifier/RFT
  gate_artifact 0 真通过但有正确被门拒        → 实质 C·不喂蒸馏·挑出净增交付
  too_easy      pass 率 > 买方难倒线           → 丢
"""
from __future__ import annotations

from typing import Any

# 买方难倒口径:pass@5 ≤ 0.6 才算难倒 → pass 率 > 0.6 = 太易(C 类)
TOO_EASY_PASS_RATE = 0.6

BUCKETS = ("true_wall", "pseudo_wall", "gate_artifact", "too_easy")


def classify_task(diag: dict[str, Any]) -> dict[str, Any]:
    """把单题 pass@大k 聚合分到四桶之一。纯函数。"""
    n_samples = int(diag.get("n_samples", 0))
    n_passed = int(diag.get("n_passed", 0))
    n_gated = int(diag.get("n_correct_but_gated", 0))
    p1 = diag.get("pass_at_1")

    if n_samples <= 0:
        raise ValueError("n_samples 必须 > 0: %r" % diag.get("task_uid"))
    if n_passed > n_samples or n_passed < 0 or n_gated < 0:
        raise ValueError("n_passed/n_correct_but_gated 越界: %r" % diag.get("task_uid"))

    pass_rate = (p1 if p1 is not None else n_passed / n_samples)

    # 太易:pass 率超买方难倒线(显式 pass_at_1 优先)
    if pass_rate > TOO_EASY_PASS_RATE:
        bucket, reason = "too_easy", "pass率 %.3f > 难倒线 %.2f" % (pass_rate, TOO_EASY_PASS_RATE)
    # 洗门优先:0 真通过 + 有正确被门拒 → 表面"真墙"实为 harness 门伪装
    elif n_passed == 0 and n_gated > 0:
        bucket, reason = "gate_artifact", "0 真通过但 %d 样本正确被门拒(洗门·非真墙)" % n_gated
    # 真能力墙:从不通过 + 无洗门 → 蒸馏候选
    elif n_passed == 0:
        bucket, reason = "true_wall", "pass@大k=0 且无洗门 → 蒸馏候选"
    # 伪能力墙:偶尔通过(会但不稳)
    else:
        bucket, reason = "pseudo_wall", "pass率 %.3f(会但不稳)→ best-of-N/RFT" % pass_rate

    return {
        "task_uid": diag.get("task_uid"),
        "bucket": bucket,
        "reason": reason,
        "pass_rate": round(pass_rate, 4),
        "distill_candidate": bucket == "true_wall",
    }


def classify_distillation_fuel(diag: dict[str, Any],
                               strong_model_passed: bool | None) -> dict[str, Any]:
    """双门 true_wall 判定(6/17 实证·代码强制·防单门假阳性)。

    门 A(S-诊断)= classify_task 出 true_wall(良好 elicitation 下 doubao pass@k==0 且无洗门)。
    门 B(S-分拣)= strong_model_passed:≥1 个强模型在同 harness 解出。

    只有门 A ∧ 门 B 才是 distillation_fuel(蒸馏燃料·有正确 trace 可蒸)。
    门 A ∧ ¬门 B = buyer_stump(bucket-B·买方难倒题·非燃料·教师也解不出=p14 情形)。
    门 A 但门 B 未测(None)= true_wall_pending_strong_gate(诚实·不臆造燃料)。
    非门 A(doubao 能解/洗门/太易)= 透传 classify_task 桶·与门 B 无关。
    """
    base = classify_task(diag)
    if base["bucket"] != "true_wall":
        return base  # 门 A 不过:pseudo/gate_artifact/too_easy 透传·不进门 B

    if strong_model_passed is True:
        bucket, reason, cand = ("distillation_fuel",
                                "门A过(doubao pass@k=0)+门B过(强模型解出)→ 蒸馏燃料", True)
    elif strong_model_passed is False:
        bucket, reason, cand = ("buyer_stump",
                                "门A过但门B不过(强模型也解不出·无正确trace可蒸)→ 买方难倒题非燃料", False)
    else:
        bucket, reason, cand = ("true_wall_pending_strong_gate",
                                "门A过·门B(强模型先解)未测 → 不能宣称燃料·待 S-分拣", False)
    return {**base, "bucket": bucket, "reason": reason, "distill_candidate": cand,
            "gate_a_true_wall": True, "strong_model_passed": strong_model_passed}


def triage_batch(tasks: list[dict[str, Any]]) -> dict[str, Any]:
    """批量分桶 + 汇总。返回 {buckets:{bucket:[uid...]}, summary:{...}, details:[...]}。"""
    buckets: dict[str, list[str]] = {b: [] for b in BUCKETS}
    details = []
    for t in tasks:
        r = classify_task(t)
        buckets[r["bucket"]].append(r["task_uid"])
        details.append(r)

    summary = {b: len(buckets[b]) for b in BUCKETS}
    summary["total"] = len(tasks)
    summary["distill_candidates"] = summary["true_wall"]
    return {"buckets": buckets, "summary": summary, "details": details}
