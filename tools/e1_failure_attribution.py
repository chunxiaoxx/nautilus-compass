#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1 检索调优第一刀: A+ 查询失败样例归因(R436 · 工作集 A_plus_queries.json)。

口径与 eval.py 完全一致(bge-m3 CLS 池化+normalize+MAXLEN 512+parse_md 同款)。
输出: R@1/R@5/MRR 对齐预注册 + 逐条失败明细(gold rank/sim + top1 信息 + 查询特征)。
"""
import glob
import json
import re

import torch
from tokenizers import Tokenizer
from transformers import AutoModel

CORPUS_DIR = "/root/vdf/emb_bakeoff"
QUERIES = CORPUS_DIR + "/A_plus_queries.json"
OUT = CORPUS_DIR + "/e1_attribution.json"
BGE = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
DEV = "cuda"
MAXLEN = 512


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return path.rsplit("/", 1)[-1], t.strip()[:2000]


def load_corpus() -> list:
    out = []
    for p in sorted(glob.glob(CORPUS_DIR + "/*.md")):
        name, body = parse_md(p)
        if name.upper() in ("MEMORY.MD", "INDEX.MD") or len(body) < 50:
            continue
        out.append({"name": name, "body": body})
    return out


@torch.no_grad()
def embed(model, tok, texts: list) -> torch.Tensor:
    encs = [tok.encode(t).ids[:MAXLEN] for t in texts]
    pad_id = tok.token_to_id("<|endoftext|>") or tok.token_to_id("<pad>") or 0
    maxlen = max(len(e) for e in encs)
    input_ids = torch.full((len(encs), maxlen), pad_id, dtype=torch.long)
    attn = torch.zeros((len(encs), maxlen), dtype=torch.long)
    for i, e in enumerate(encs):
        input_ids[i, :len(e)] = torch.tensor(e)
        attn[i, :len(e)] = 1
    out = model(input_ids=input_ids.to(DEV), attention_mask=attn.to(DEV))
    vecs = out.last_hidden_state[:, 0]  # bge-m3 CLS 池化
    return torch.nn.functional.normalize(vecs, dim=-1)


def has_entity(q: str) -> bool:
    """查询是否保留英文实体锚(错误码/工具名/文件名片段)。"""
    return bool(re.search(r"[A-Za-z][A-Za-z0-9_.\-]{2,}", q))


def main():
    corpus = load_corpus()
    queries = json.load(open(QUERIES, encoding="utf-8"))
    tok = Tokenizer.from_file(BGE.rstrip("/") + "/tokenizer.json")
    model = AutoModel.from_pretrained(BGE, torch_dtype=torch.float16).to(DEV).eval()

    cvecs = embed(model, tok, [c["body"] for c in corpus])
    names = [c["name"] for c in corpus]
    idx = {n: i for i, n in enumerate(names)}

    rows, r1, r5, mrr = [], 0, 0, 0.0
    for q in queries:
        qv = embed(model, tok, [q["text"]])[0]
        sims = (cvecs @ qv).tolist()
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        rank = order.index(idx[q["gold"]]) + 1 if q["gold"] in idx else -1
        top1 = names[order[0]]
        hit1 = rank == 1
        r1 += hit1
        r5 += 1 <= rank <= 5
        mrr += 1.0 / rank if rank > 0 else 0.0
        rows.append({
            "query": q["text"], "gold": q["gold"], "top1": top1,
            "gold_rank": rank, "gold_sim": round(sims[idx[q["gold"]]], 4) if rank > 0 else None,
            "top1_sim": round(sims[order[0]], 4),
            "top5": [names[i] for i in order[:5]],
            "q_len": len(q["text"]), "q_has_entity": has_entity(q["text"]),
            "verdict": "HIT" if hit1 else ("NEAR_MISS" if 2 <= rank <= 5 else "FAR_MISS"),
        })

    n = len(rows)
    summary = {
        "n_queries": n, "n_corpus": len(corpus),
        "recall_at_1": round(r1 / n, 4), "recall_at_5": round(r5 / n, 4),
        "mrr": round(mrr / n, 4),
        "baseline_prereg_r1": 0.40,
        "hits": r1, "near_miss": sum(1 for r in rows if r["verdict"] == "NEAR_MISS"),
        "far_miss": sum(1 for r in rows if r["verdict"] == "FAR_MISS"),
        "miss_with_entity": sum(1 for r in rows if r["verdict"] != "HIT" and r["q_has_entity"]),
        "miss_without_entity": sum(1 for r in rows if r["verdict"] != "HIT" and not r["q_has_entity"]),
    }
    json.dump({"summary": summary, "rows": rows}, open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("SUMMARY", json.dumps(summary, ensure_ascii=False))
    print("\nFAIL DETAIL (top12):")
    for r in [x for x in rows if x["verdict"] != "HIT"][:12]:
        print(f"  [{r['verdict']} rank={r['gold_rank']}] {r['query'][:44]}"
              f" | gold={r['gold'][:26]} top1={r['top1'][:26]} entity={r['q_has_entity']}")


if __name__ == "__main__":
    main()
