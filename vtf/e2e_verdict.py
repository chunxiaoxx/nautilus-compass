"""e2e 裁决:context 臂 vs doubao 基线臂,分型明细对比(join by qid)。

用法: python3 /tmp/e2e_verdict.py <baseline.jsonl> <ctx.jsonl>
"""
import json
import sys
from collections import defaultdict


def load(path):
    rows = {}
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        qid = d.get("qid") or d.get("question_id") or d.get("id")
        rows[qid] = d
    return rows


def acc_of(d):
    for k in ("judge_acc", "acc", "correct"):
        if k in d:
            v = d[k]
            return float(v) if not isinstance(v, bool) else (1.0 if v else 0.0)
    return None


base = load(sys.argv[1])
ctx = load(sys.argv[2])

by_type = defaultdict(lambda: {"b": [], "c": []})
for qid, d in ctx.items():
    qt = d.get("qtype") or d.get("question_type") or "?"
    a = acc_of(d)
    if a is None:
        continue
    by_type[qt]["c"].append(a)
    if qid in base:
        ab = acc_of(base[qid])
        if ab is not None:
            by_type[qt]["b"].append(ab)

print(f"{'qtype':38} {'base':>10} {'ctx':>10} {'Δ':>8}")
tb, tc, nb, nc = 0.0, 0.0, 0, 0
for qt in sorted(by_type):
    b = by_type[qt]["b"]
    c = by_type[qt]["c"]
    mb = sum(b) / len(b) if b else 0.0
    mc = sum(c) / len(c) if c else 0.0
    tb += sum(b)
    tc += sum(c)
    nb += len(b)
    nc += len(c)
    print(f"{qt:38} {mb:10.3f} {mc:10.3f} {mc-mb:+8.3f}   (n={len(c)})")
print("-" * 70)
print(f"{'TOTAL':38} {tb/max(nb,1):10.3f} {tc/max(nc,1):10.3f} {tc/max(nc,1)-tb/max(nb,1):+8.3f}   (n_base={nb}, n_ctx={nc})")
