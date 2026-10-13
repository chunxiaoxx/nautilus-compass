#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自举标签抽检抽样器(R532 · SELFLABEL_AUDIT_PREREG 步1): 分层 n=100,SEED 20261013。

总体=eightb_trigger 触发池的 self_labeled 子集(_src 记录于切分行)。
"""
import json
import random
from collections import Counter
from pathlib import Path

SEED = 20261013
N = 100
ROOT = Path("runtime/verdict_corpus/eightb_trigger")

rows = [json.loads(l) for l in (ROOT / "split_train.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
hold = [json.loads(l) for l in (ROOT / "split_dev.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
pool = rows + hold
self_lab = [r for r in pool if not r.get("_src", "").startswith(("split_", "delta:"))]
print(f"self_labeled 总体: {len(self_lab)}")

by_src = {}
for r in self_lab:
    by_src.setdefault(r["_src"], []).append(r)
quota = {s: max(1, round(N * len(v) / len(self_lab))) for s, v in by_src.items()}
# 修正配额至恰 100(最大余数法)
diff = N - sum(quota.values())
order = sorted(quota, key=lambda s: -(len(by_src[s]) * N / len(self_lab) % 1))
for s in order[:abs(diff)]:
    quota[s] += 1 if diff > 0 else -1

rng = random.Random(SEED)
sample = []
for s in sorted(by_src):
    k = min(quota[s], len(by_src[s]))
    sample.extend(rng.sample(by_src[s], k))
print(f"抽样 {len(sample)} 条 | 分层: {dict(Counter(r['_src'] for r in sample))}")

out = Path("runtime/org_fuel/selflabel_audit_sample.jsonl")
with open(out, "w", encoding="utf-8", newline="\n") as f:
    for r in sample:
        f.write(json.dumps({"id": r["id"], "_src": r["_src"],
                            "artifact": r.get("artifact") or {},
                            "judge_verdict": r.get("truth_label")}, ensure_ascii=False) + "\n")
print(f"[OK] {out}")
