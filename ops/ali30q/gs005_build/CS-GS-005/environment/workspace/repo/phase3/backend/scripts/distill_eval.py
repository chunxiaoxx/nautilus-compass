#!/usr/bin/env python3
"""齿轮⑦ held-out eval:蒸馏 7B vs base 7B vs doubao(2026-06-22)· 证/杀决策门。

中心环 forcing function 的测量端。held-out A 类题(训练未见)上三方打分 → 分数 delta →
PROVEN(破墙·放大)/ KILLED(诚实退回护城河)/ INCONCLUSIVE。

🔴 GPU/env-gated:模型推理(torch·base+adapter)+ 连续 scorer(ALE public_eval=compass env)。
纯逻辑(compute_score_delta / prove_or_kill_verdict)在 services.distill_train(已 TDD green)。

用法:
  python scripts/distill_eval.py --heldout /path/heldout.jsonl --adapter /path/adapter \
     --base-model Qwen/Qwen2.5-Coder-7B-Instruct --out /path/eval_result.json
"""
from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.distill_train import compute_score_delta, prove_or_kill_verdict  # noqa: E402
from services.confound_check import eval_confound_checks  # noqa: E402


def load_jsonl(path: str) -> list[dict]:
    rows = []
    with open(path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="蒸馏 held-out eval(分数 delta + 证/杀)")
    ap.add_argument("--heldout", required=True, help="held-out A 类题 jsonl(训练未见)")
    ap.add_argument("--adapter", required=True, help="蒸馏 adapter 目录")
    ap.add_argument("--base-model", default="Qwen/Qwen2.5-Coder-7B-Instruct")
    ap.add_argument("--out", default="eval_result.json")
    ap.add_argument("--min-n", type=int, default=20)
    a = ap.parse_args(argv)

    heldout = load_jsonl(a.heldout)
    print(f"[eval] held-out {len(heldout)} 题 · adapter={a.adapter}")

    # 🔴 GPU/env effect:对每题用 base / base+adapter / doubao 产解 → 连续 scorer 打分。
    #    scorer = ALE public_eval(compass env·6-key 契约)或 SWE harness(二元对照)。
    #    本骨架定义契约;真推理+打分接 compass scorer / V5 harness 的 eval_fn。
    from scripts._distill_runtime import (  # lazy·GPU 侧实现(env 就绪时建)
        load_models, generate_solution, score_solution, doubao_solution)

    model, tok = load_models(a.base_model, a.adapter)   # 单模型·adapter 切换(省显存·7B 必需)

    per_task = []
    for t in heldout:
        tid = t["task_id"]
        prob = t.get("problem_statement", "")
        kind = t.get("kind", "ale")   # SWE held-out → SWE instruction + docker scorer(score_solution 据 task.kind 分派)
        base_sol = generate_solution(model, tok, prob, kind=kind, use_adapter=False)   # 旁路 adapter=base
        dist_sol = generate_solution(model, tok, prob, kind=kind, use_adapter=True)    # adapter on=distilled
        row = {
            "task_id": tid,
            "base": score_solution(t, base_sol),
            "distilled": score_solution(t, dist_sol),
            "doubao": doubao_solution(t),   # 或读 t['doubao_score'] 若已算
            # 诊断:解长度区分 KILLED 归因——空解(题太难 artifact)vs 产解但分低(真没破墙)
            "base_len": len(base_sol.strip()),
            "distilled_len": len(dist_sol.strip()),
        }
        # confound 旁注:adapter 生效?解非空?(KILLED 信之前先排 confound·2026-06-23)
        row["confound_checks"] = eval_confound_checks(row)
        per_task.append(row)
        print(f"[eval] {tid}: base={row['base']}(len{row['base_len']}) "
              f"distilled={row['distilled']}(len{row['distilled_len']}) "
              f"doubao={row['doubao']}", flush=True)

    delta = compute_score_delta(per_task)
    verdict = prove_or_kill_verdict(delta, min_n=a.min_n)
    result = {"verdict": verdict, "delta": delta, "n": len(per_task)}
    with open(a.out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, ensure_ascii=False, indent=2)
    # per_task dump(LOO/CV driver 跨折聚合用·distill_loo.py 读 <out>.pertask.json)
    with open(a.out.replace(".json", ".pertask.json"), "w", encoding="utf-8") as fh:
        json.dump(per_task, fh, ensure_ascii=False, indent=2)
    print(f"[eval] 🎯 verdict={verdict} · win_rate_vs_base={delta['win_rate_vs_base']} "
          f"· uplift={delta['mean_rel_uplift_vs_base']} · n={delta['n']}")
    # graded 信号(6/23·早期/部分泛化探测·KILLED 时看 valid_rate 升没升判趋势)
    print(f"[eval] graded · distilled_valid_rate={delta.get('distilled_valid_rate')} "
          f"· near_base_rate={delta.get('near_base_rate')} "
          f"· base_valid_rate={delta.get('base_valid_rate')} "
          f"(valid_rate 升 = distilled 开始产有效解·即便 win<0.6 也是泛化迹象)")
    # confound 旁注 surface:KILLED 带未排除 confound = 不可信(先排 confound 再信)
    from services.confound_check import unresolved_confounds
    unresolved = unresolved_confounds({"per_task": per_task})
    if unresolved:
        print(f"[eval] ⚠️ 未排除 confound(verdict 不可全信·先排):{unresolved}")
    print(f"[eval] PROVEN=破墙放大 / KILLED=诚实退护城河 / INCONCLUSIVE=补燃料或样本")
    return 0


if __name__ == "__main__":
    sys.exit(main())
