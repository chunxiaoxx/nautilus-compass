#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1-TUNE H1×H2 叠加实验(R440): 库侧合并(8对) + cross-encoder rerank 组合读数。

语料=emb_bakeoff_h1(R438 合并后 150 文档);检索=bge-m3 同口径;重排=同 H2 reranker。
与 R437/438/439 同工作集同判据,完成 2×2 归因矩阵的最后一格。
"""
import glob
import json
import re

import torch
from tokenizers import Tokenizer
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

H1 = "/root/vdf/emb_bakeoff_h1"
OUT = H1 + "/e1_combined_result.json"
BGE = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
RERANK = "/root/vdf/models/bge-reranker-v2-m3"
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
    for p in sorted(glob.glob(H1 + "/*.md")):
        name, body = parse_md(p)
        if name.upper() in ("MEMORY.MD", "INDEX.MD") or len(body) < 50:
            continue
        out.append({"name": name, "body": body})
    return out


@torch.no_grad()
def embed_bge(model, tok, texts: list) -> torch.Tensor:
    encs = [tok.encode(t).ids[:MAXLEN] for t in texts]
    pad_id = tok.token_to_id("<|endoftext|>") or tok.token_to_id("<pad>") or 0
    maxlen = max(len(e) for e in encs)
    input_ids = torch.full((len(encs), maxlen), pad_id, dtype=torch.long)
    attn = torch.zeros((len(encs), maxlen), dtype=torch.long)
    for i, e in enumerate(encs):
        input_ids[i, :len(e)] = torch.tensor(e)
        attn[i, :len(e)] = 1
    out = model(input_ids=input_ids.to(DEV), attention_mask=attn.to(DEV))
    return torch.nn.functional.normalize(out.last_hidden_state[:, 0], dim=-1)


def main():
    corpus = load_corpus()
    queries = json.load(open(H1 + "/A_plus_queries.json", encoding="utf-8"))
    btok = Tokenizer.from_file(BGE.rstrip("/") + "/tokenizer.json")
    bge = AutoModel.from_pretrained(BGE, torch_dtype=torch.float16).to(DEV).eval()
    rtok = AutoTokenizer.from_pretrained(RERANK)
    rr = AutoModelForSequenceClassification.from_pretrained(
        RERANK, torch_dtype=torch.float16).to(DEV).eval()

    cvecs = embed_bge(bge, btok, [c["body"] for c in corpus])
    names = [c["name"] for c in corpus]
    bodies = {c["name"]: c["body"] for c in corpus}
    idx = {n: i for i, n in enumerate(names)}

    # gold 重映射(R438 同款: 被并文件→保留者)
    MERGE_PAIRS = [
        ("m5-memgate-deploy-lessons-20261009.md", "memgate-m5-deploy-lessons-20261008.md"),
        ("session_20260722-1257_client-auto-reconnect-shipped.md", "session_20260722-1251_client-auto-reconnect-shipped.md"),
        ("session_20260722-1257_MCP-TCP-auth-landed.md", "session_20260722-1251_MCP-TCP-auth-landed.md"),
        ("session_20260722-1257_server-status-endpoint-added.md", "session_20260722-1251_server-status-endpoint-added.md"),
        ("session_20260722-1257_TLS-demo-observation-one.md", "session_20260722-1251_TLS-demo-observation-one.md"),
        ("session_20260722-1257_TLS-demo-observation-two.md", "session_20260722-1251_TLS-demo-observation-two.md"),
        ("session_20260823-0935_goalmode-heartbeat-alert.md", "session_20260823-0912_goalmode-heartbeat-alert.md"),
        ("convergence-state-snapshot-20260821.md", "convergence-state-snapshot-20260809.md"),
    ]
    REMAP = {b: a for a, b in MERGE_PAIRS}

    r1 = r5 = mrr = 0
    per = []
    for q in queries:
        gold = REMAP.get(q["gold"], q["gold"])
        qv = embed_bge(bge, btok, [q["text"]])[0]
        sims = (cvecs @ qv).tolist()
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        top5 = [names[i] for i in order[:5]]
        with torch.no_grad():
            inp = rtok([[q["text"], bodies[n][:1200]] for n in top5], padding=True,
                       truncation=True, max_length=512, return_tensors="pt").to(DEV)
            s = rr(**inp).logits.view(-1).float().tolist()
        reranked = [n for _, n in sorted(zip(s, top5), reverse=True)]
        rank = reranked.index(gold) + 1 if gold in reranked else None
        if rank is None:
            gr = order.index(idx[gold]) + 1 if gold in idx else -1
            rank = gr
        hit = rank == 1
        r1 += hit
        r5 += 1 <= rank <= 5
        mrr += 1.0 / rank if rank > 0 else 0.0
        per.append({"q": q["text"][:36], "gold": gold[:32], "rank": rank,
                    "verdict": "HIT" if hit else "MISS", "polluted": q["text"].startswith(("如果", "查询:"))})
    n = len(per)
    clean = [p for p in per if not p["polluted"]]
    ch = sum(1 for p in clean if p["verdict"] == "HIT")
    cr5 = sum(1 for p in clean if p["rank"] <= 5)
    result = {
        "n_queries": n, "corpus": "emb_bakeoff_h1 (merged, 150 docs)",
        "pipeline": "bge-m3 retrieve -> bge-reranker-v2-m3 top5 rerank",
        "recall_at_1": round(r1 / n, 4), "recall_at_5": round(r5 / n, 4), "mrr": round(mrr / n, 4),
        "clean_r1": round(ch / len(clean), 4), "clean_r5": round(cr5 / len(clean), 4),
        "clean_hits": f"{ch}/{len(clean)}",
        "baseline": {"r1": 0.4, "r5": 0.6667, "mrr": 0.4994},
        "h1_only": {"r1": 0.4333}, "h2_only": {"r1": 0.5667, "clean_r1": 0.8},
        "per_query": per,
    }
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("COMBINED", json.dumps({k: result[k] for k in
          ("recall_at_1", "recall_at_5", "mrr", "clean_r1", "clean_r5", "clean_hits")}, ensure_ascii=False))
    for p in per:
        if p["verdict"] == "MISS":
            print(f"  MISS rank={p['rank']} poll={p['polluted']} {p['q']}")


if __name__ == "__main__":
    main()
