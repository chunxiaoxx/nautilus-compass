#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1-TUNE H2 单独归因实验(R439): cross-encoder rerank(bge-reranker-v2-m3) top5 重排。

与 R437/R438 同工作集/同判据;检索侧复用归因 JSON 的 bge top5(检索口径不变,
只加重排层——H1/H2 分开归因纪律)。gold rank>5 的污染条 rerank 原理性无效,如实计入。
"""
import glob
import json
import re

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

SRC = "/root/vdf/emb_bakeoff"
RERANK = "/root/vdf/models/bge-reranker-v2-m3"
ATTR = SRC + "/e1_attribution.json"
OUT = SRC + "/e1_h2_result.json"
DEV = "cuda"


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return path.rsplit("/", 1)[-1], t.strip()[:2000]


def main():
    corpus = {}
    for p in sorted(glob.glob(SRC + "/*.md")):
        name, body = parse_md(p)
        if name.upper() in ("MEMORY.MD", "INDEX.MD") or len(body) < 50:
            continue
        corpus[name] = body
    attr = json.load(open(ATTR, encoding="utf-8"))

    tok = AutoTokenizer.from_pretrained(RERANK)
    model = AutoModelForSequenceClassification.from_pretrained(
        RERANK, torch_dtype=torch.float16).to(DEV).eval()

    r1 = r5 = mrr = 0
    per = []
    pairs_changed = 0
    for row in attr["rows"]:
        q = row["query"]
        cands = [n for n in row["top5"] if n in corpus]
        if not cands:
            continue
        scores = {}
        with torch.no_grad():
            for i in range(0, len(cands), 5):
                batch = cands[i:i + 5]
                inp = tok([[q, corpus[n][:1200]] for n in batch], padding=True,
                          truncation=True, max_length=512, return_tensors="pt").to(DEV)
                s = model(**inp).logits.view(-1).float().tolist()
                scores.update(dict(zip(batch, s)))
        order = sorted(cands, key=lambda n: -scores[n])
        gold = row["gold"]
        rank = order.index(gold) + 1 if gold in order else row["gold_rank"]
        if rank == 1:
            r1 += 1
        if 1 <= rank <= 5:
            r5 += 1
            mrr += 1.0 / rank
        if order[0] != row["top1"]:
            pairs_changed += 1
        per.append({"q": q[:36], "gold": gold[:32], "old_rank": row["gold_rank"],
                    "new_rank": rank, "new_top1": order[0][:32],
                    "gold_score": round(scores.get(gold, -99), 3),
                    "top1_old_score": round(scores.get(row["top1"], -99), 3)})
    n = len(per)
    result = {
        "n_queries": n, "reranker": "bge-reranker-v2-m3 fp16",
        "rerank_scope": "top5 only (bge retrieval unchanged)",
        "recall_at_1": round(r1 / n, 4), "recall_at_5": round(r5 / n, 4),
        "mrr": round(mrr / n, 4),
        "baseline_r1": 0.4, "baseline_r5": 0.6667, "baseline_mrr": 0.4994,
        "delta_r1": round(r1 / n - 0.4, 4),
        "top1_changed": pairs_changed,
        "per_query": per,
    }
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("H2 SUMMARY", json.dumps({k: result[k] for k in
          ("recall_at_1", "recall_at_5", "mrr", "delta_r1", "top1_changed")}, ensure_ascii=False))
    for p in per:
        mark = "  <-- upgraded" if p["new_rank"] < p["old_rank"] else ""
        print(f"  rank {p['old_rank']}->{p['new_rank']} | {p['q']} | new_top1={p['new_top1']}{mark}")


if __name__ == "__main__":
    main()
