"""诊断 distilled 解内容(2026-06-23):over-fit distilled!=base 但 0 分·看学了什么。

over-fit(训练题=eval题)下 distilled 应复现 strong_solution。它 != base(adapter 生效)
但 ALE judge 0 分。此脚本 dump distilled 解全文对比 strong_solution,区分归因:
  ① distilled ≈ strong_solution 残缺/有 bug(语法接近·细节错)→ 1.5B 容量问题 → 上 7B
  ② distilled 乱码/跑题/截断(不像 strong)→ 训练管线问题(SFT 格式/seq 截断/学习率)

用法(GPU 盒·训练 venv):
  python distill_probe_solution.py <records.jsonl> <adapter_dir> [base_model] [tid1,tid2]
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _distill_runtime import load_models, generate_solution  # noqa: E402


def main() -> None:
    records_path = sys.argv[1]
    adapter = sys.argv[2]
    base_model = sys.argv[3] if len(sys.argv) > 3 else "Qwen/Qwen2.5-Coder-1.5B-Instruct"
    probe_ids = sys.argv[4].split(",") if len(sys.argv) > 4 else ["ahc015", "ahc008"]

    recs = {}
    for ln in open(records_path, encoding="utf-8"):
        ln = ln.strip()
        if ln:
            r = json.loads(ln)
            recs[r["task_id"]] = r

    model, tok = load_models(base_model, adapter)

    for tid in probe_ids:
        if tid not in recs:
            print(f"[probe] {tid} 不在 records·跳过")
            continue
        r = recs[tid]
        prob = r.get("problem_statement", "")
        strong = r.get("strong_solution", "")
        base_sol = generate_solution(model, tok, prob, use_adapter=False)
        dist_sol = generate_solution(model, tok, prob, use_adapter=True)
        print(f"\n{'=' * 72}\n=== {tid} ===")
        print(f"--- TARGET strong_solution ({len(strong)} chars·前700) ---")
        print(strong[:700])
        print(f"\n--- BASE 解 ({len(base_sol)} chars·前500) ---")
        print(base_sol[:500])
        print(f"\n--- DISTILLED 解 ({len(dist_sol)} chars·前900) ---")
        print(dist_sol[:900])
        print(f"{'=' * 72}")


if __name__ == "__main__":
    main()
