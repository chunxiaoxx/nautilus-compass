#!/usr/bin/env python3
"""Gate B = 强模型解门(P1 第三类飞轮 keystone·2026-06-20)。

双门一鱼两吃:gate A(doubao 难倒·pass@k≤0.6)筛出 true_wall 候选 → 本模块用强模型
（qwen3.7-max/GLM5.2/deepseek4.0pro·百炼）逐个试解 → ≥1 解出 = 有干净 correct trace
可蒸馏 = bucket-A(蒸馏燃料 + 买方难倒题·一鱼两吃)· 全不解 = bucket-B(buyer_stump·
真前沿护城河·免费副产品)。p14 实证:强模型也可能全卡(那就是 bucket-B)。

纯编排:complete_fn(prompt, model)->code + eval_fn(code, task)->{passed:bool} 注入。
runner 侧用 fde_sdiagnose_run.bailian_complete + gpu_eval_candidate 接真模型/GPU。
出 strong_model_passed → 喂 fde_triage.classify_distillation_fuel 出最终桶。

设计见 docs/plans/2026-06-20-p1-third-class-flywheel-autonomy-plan.md(G1)。
"""
from __future__ import annotations


def run_strong_model_gate(true_wall_tasks: list, strong_models: list,
                          complete_fn, eval_fn, k: int = 1) -> list:
    """对每个 true_wall 题·遍历强模型试解。≥1 模型(best-of-k)解出 → strong_model_passed=True。

    短路:一旦某模型解出即停(省算力·"有干净 trace 可蒸"已成立)。
    🔴 三态(防 OOM/eval 崩误标 buyer_stump·6/20 实证 bug):
      True  = ≥1 模型真解出 → bucket-A 蒸馏燃料
      False = 真跑过 eval 且无人解出(genuine fail)→ buyer_stump 护城河
      None  = 一次 eval 都没真跑成(全 complete/eval 抛错 或 eval 返 ok=False 基础设施错·
              如 GPU OOM no_json)→ inconclusive·不臆造·→ true_wall_pending_strong_gate(hold)
    fail-soft:complete/eval 抛错 或 eval ok=False → 该次记未真评·不中断整环。
    回 [{task_uid, strong_model_passed(True/False/None), which_model, per_model:[{model,passed,error?}]}]。
    """
    out = []
    for task in true_wall_tasks:
        uid = task.get("task_uid")
        prompt = task.get("prompt", "")
        passed_any = False
        genuine_eval = False   # 至少一次 eval 真跑出结论(非 OOM/崩)
        which = None
        per_model = []
        for model in strong_models:
            m_passed = False
            m_err = None
            for _i in range(max(1, k)):
                try:
                    code = complete_fn(prompt, model)
                    res = eval_fn(code, task)
                except Exception as ex:  # noqa: BLE001 — 异常=未真评·不中断
                    m_err = str(ex)[:200]
                    continue
                if res and res.get("ok") is False:  # eval 基础设施错(OOM/no_json)=未真评
                    m_err = str(res.get("reason") or res.get("error") or "eval_error")[:200]
                    continue
                genuine_eval = True
                if res and res.get("passed"):
                    m_passed = True
                    break
            rec = {"model": model, "passed": m_passed}
            if m_err and not m_passed:
                rec["error"] = m_err
            per_model.append(rec)
            if m_passed:
                passed_any = True
                which = model
                break  # 短路:有一个解出就够(干净 trace 可蒸)
        if passed_any:
            spp = True
        elif genuine_eval:
            spp = False
        else:
            spp = None  # 一次都没真评出 → inconclusive(别当 buyer_stump)
        out.append({"task_uid": uid, "strong_model_passed": spp,
                    "which_model": which, "per_model": per_model})
    return out
