#!/usr/bin/env python
# PRECOR B/C 一致性回放 runner:8 配置 x 292 题 → 一致率矩阵 CSV
# 用法:python precor_replay.py --serve http://127.0.0.1:8300 --split test --out precor_matrix.csv
# 判据:docs/metering/PRECOR_JUDGE_ROBUST_20261006.md(合格线=对 bf16 一致率>=99%,预注册)
import argparse, csv, itertools, json, urllib.request

ap = argparse.ArgumentParser()
ap.add_argument("--serve", default="http://127.0.0.1:8300")
ap.add_argument("--corpus", required=True, help="split_test/dev 292 题 jsonl(qid,prompt)")
ap.add_argument("--configs", default="bf16,fp8,int8,awq,gptq,fp16-bf100, seed2, seed3")
ap.add_argument("--out", default="precor_matrix.csv")
a = ap.parse_args()
cfgs = [c.strip() for c in a.configs.split(",")]

def ask(prompt, cfg):
    body = json.dumps({"model": f"nacre-champion@{cfg}" if "@" in cfg else "nacre-champion",
                       "messages": [{"role": "user", "content": prompt}], "temperature": 0}).encode()
    req = urllib.request.Request(a.serve + "/v1/chat/completions", body,
                                 {"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(req, timeout=120))["choices"][0]["message"]["content"]

rows = [json.loads(l) for l in open(a.corpus, encoding="utf-8")]
base = {r["qid"]: ask(r["prompt"], cfgs[0]) for r in rows}
w = csv.writer(open(a.out, "w", newline=""))
w.writerow(["qid"] + cfgs[1:] + ["base_first30"])
match = {c: 0 for c in cfgs[1:]}
for r in rows:
    outs = [base[r["qid"]]] + [ask(r["prompt"], c) for c in cfgs[1:]]
    w.writerow([r["qid"]] + [1 if o == outs[0] else 0 for o in outs[1:]] + [outs[0][:30]])
    for i, c in enumerate(cfgs[1:]):
        match[c] += 1 if outs[i + 1] == outs[0] else 0
n = len(rows)
print(f"n={n}")
for c in cfgs[1:]:
    print(f"  {c}: 一致率 {match[c]/n:.4f}({'PASS' if match[c]/n >= 0.99 else 'FAIL'})")
