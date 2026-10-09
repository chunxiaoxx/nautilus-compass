#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1-TUNE 终局评测(R442): v2 干净工作集 × 三配置正式定谳读数。

格1 基线:  原始语料 + bge-m3 alone
格2 H2:    原始语料 + bge-m3 + rerank
格3 组合:  合并语料(150) + bge-m3 + rerank
gold 含被并文件时 REMAP 到保留者(R438 同表)。输出 e1_final_verdict.json。
"""
import glob
import json
import re

import torch
from tokenizers import Tokenizer
from transformers import AutoModel, AutoModelForSequenceClassification, AutoTokenizer

SRC = "/root/vdf/emb_bakeoff"
H1 = "/root/vdf/emb_bakeoff_h1"
BGE = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
RERANK = "/root/vdf/models/bge-reranker-v2-m3"
OUT = SRC + "/e1_final_verdict.json"
DEV = "cuda"
MAXLEN = 512

REMAP = {
    "memgate-m5-deploy-lessons-20261008.md": "m5-memgate-deploy-lessons-20261009.md",
    "session_20260722-1251_client-auto-reconnect-shipped.md": "session_20260722-1257_client-auto-reconnect-shipped.md",
    "session_20260722-1251_MCP-TCP-auth-landed.md": "session_20260722-1257_MCP-TCP-auth-landed.md",
    "session_20260722-1251_server-status-endpoint-added.md": "session_20260722-1257_server-status-endpoint-added.md",
    "session_20260722-1251_TLS-demo-observation-one.md": "session_20260722-1257_TLS-demo-observation-one.md",
    "session_20260722-1251_TLS-demo-observation-two.md": "session_20260722-1257_TLS-demo-observation-two.md",
    "session_20260823-0912_goalmode-heartbeat-alert.md": "session_20260823-0935_goalmode-heartbeat-alert.md",
    "convergence-state-snapshot-20260809.md": "convergence-state-snapshot-20260821.md",
}


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return path.rsplit("/", 1)[-1], t.strip()[:2000]


def load_corpus(d: str) -> list:
    out = []
    for p in sorted(glob.glob(d + "/*.md")):
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


@torch.no_grad()
def rerank_scores(rr, rtok, q: str, cands: list, bodies: dict) -> list:
    inp = rtok([[q, bodies[n][:1200]] for n in cands], padding=True,
               truncation=True, max_length=512, return_tensors="pt").to(DEV)
    s = rr(**inp).logits.view(-1).float().tolist()
    return [n for _, n in sorted(zip(s, cands), reverse=True)]


def eval_cfg(bge, btok, rr, rtok, corpus, queries, use_rr: bool, label: str) -> dict:
    cvecs = embed_bge(bge, btok, [c["body"] for c in corpus])
    names = [c["name"] for c in corpus]
    bodies = {c["name"]: c["body"] for c in corpus}
    idx = {n: i for i, n in enumerate(names)}
    r1 = r5 = mrr = 0
    for q in queries:
        gold = REMAP.get(q["gold"], q["gold"])
        if gold not in idx:
            continue
        qv = embed_bge(bge, btok, [q["text"]])[0]
        sims = (cvecs @ qv).tolist()
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        top5 = [names[i] for i in order[:5]]
        final = rerank_scores(rr, rtok, q["text"], top5, bodies) if use_rr else top5
        rank = final.index(gold) + 1 if gold in final else order.index(idx[gold]) + 1
        r1 += rank == 1
        r5 += 1 <= rank <= 5
        mrr += 1.0 / rank
    n = len(queries)
    res = {"cfg": label, "n": n, "r1": round(r1 / n, 4), "r5": round(r5 / n, 4),
           "mrr": round(mrr / n, 4)}
    print("CFG", json.dumps(res, ensure_ascii=False), flush=True)
    return res


def main():
    queries = json.load(open(SRC + "/A_plus_queries_v2.json", encoding="utf-8"))
    btok = Tokenizer.from_file(BGE.rstrip("/") + "/tokenizer.json")
    bge = AutoModel.from_pretrained(BGE, torch_dtype=torch.float16).to(DEV).eval()
    rtok = AutoTokenizer.from_pretrained(RERANK)
    rr = AutoModelForSequenceClassification.from_pretrained(
        RERANK, torch_dtype=torch.float16).to(DEV).eval()

    src_corpus = load_corpus(SRC)
    h1_corpus = load_corpus(H1)
    results = {
        "workset": "A_plus_queries_v2.json (generator v2, 30 clean queries)",
        "cells": [
            eval_cfg(bge, btok, rr, rtok, src_corpus, queries, False, "baseline: src corpus, bge alone"),
            eval_cfg(bge, btok, rr, rtok, src_corpus, queries, True, "h2: src corpus + rerank"),
            eval_cfg(bge, btok, rr, rtok, h1_corpus, queries, True, "combined: merged corpus + rerank"),
        ],
        "criteria_v1": {"r1_min": 0.60, "r5_min": 0.80, "bge_frozen": True},
        "note": "正式定谳口径: 判据正本=v2 重生成工作集(本评测);H1+H2 组合格为建议部署管线",
    }
    json.dump(results, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("DONE ->", OUT)


if __name__ == "__main__":
    main()
