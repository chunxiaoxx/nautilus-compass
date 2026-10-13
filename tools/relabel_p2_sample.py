#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P2 验收抽样器(R534 步骤·P1 完成后运行): 分层抽 10% 生成盲评任务包。

用法: python tools/relabel_p2_sample.py
输入: runtime/org_fuel/strongmodel_relabel_r534.jsonl(P1 产物)
输出: runtime/org_fuel/relabel_p2_blindpack.jsonl(252 条,id/src/content/strongmodel_verdict 遮蔽)
"""
import json
import random
from collections import Counter
from pathlib import Path

SEED = 20261014
N = 252

rows = [json.loads(l) for l in open("runtime/org_fuel/strongmodel_relabel_r534.jsonl",
                                    encoding="utf-8") if l.strip()]
by_src = {}
for r in rows:
    by_src.setdefault(r.get("_src", "?"), []).append(r)
quota = {s: max(1, round(N * len(v) / len(rows))) for s, v in by_src.items()}
diff = N - sum(quota.values())
order = sorted(quota, key=lambda s: -(len(by_src[s]) * N / len(rows) % 1))
for s in order[:abs(diff)]:
    quota[s] += 1 if diff > 0 else -1
rng = random.Random(SEED)
sample = []
for s in sorted(by_src):
    sample.extend(rng.sample(by_src[s], min(quota[s], len(by_src[s]))))
out = Path("runtime/org_fuel/relabel_p2_blindpack.jsonl")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for r in sample:
        f.write(json.dumps({"id": r["id"], "_src": r.get("_src", "?"),
                            "content": r["content"],
                            "strongmodel_verdict": r["strongmodel_verdict"]},
                           ensure_ascii=False) + "\n")
print(f"[OK] P2 blindpack: {len(sample)} 条 | 分层 {dict(Counter(r['_src'] for r in sample))}")
print("待办: 非实现者盲评(只读 content,判三态)→对拍 strongmodel_verdict ≥90% →回池")
