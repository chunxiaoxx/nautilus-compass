#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Embedder 对拍评测(bge-m3 锚 vs Qwen3-Emb 0.6B/4B)· 判据=EMB_BAKEOFF_PREREG_20261009.md。

Set A 全库自监督(30 查询 seed42)/Set B 中文切片/Set C 实弹三查询。
各模型用其官方用法:bge-m3=CLS 池化;Qwen3-Embedding=末 token 池化+查询指令前缀。
全部 fp16 cuda,归一化后余弦。输出 results.json。
"""
import glob
import json
import os
import random
import re
import time

import torch
from transformers import AutoModel, AutoTokenizer

os.environ.setdefault("MODELSCOPE_CACHE", "/root/vdd4/modelscope")
CORPUS_DIR = "/root/vdd4/emb_bakeoff"
BGE_PATH = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
QWEN032 = "Qwen/Qwen3-Embedding-0.6B"
QWEN4B = "Qwen/Qwen3-Embedding-4B"
QWEN_INSTR = "Given a memory retrieval query, retrieve the most relevant past session memory entry."
DEV = "cuda"
MAXLEN = 512
REL_SAMPLES = 30


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return os.path.basename(path), t.strip()[:2000]


def cjk_ratio(s: str) -> float:
    cjk = sum(1 for ch in s if "一" <= ch <= "鿿")
    return cjk / max(len(s), 1)


def load_corpus() -> list:
    out = []
    for p in sorted(glob.glob(CORPUS_DIR + "/*.md")):
        name, body = parse_md(p)
        if name.upper() in ("MEMORY.MD", "INDEX.MD") or len(body) < 50:
            continue
        out.append({"name": name, "body": body})
    return out


@torch.no_grad()
def embed(model, tok, texts: list, is_qwen: bool, is_query: bool) -> torch.Tensor:
    if is_qwen and is_query:
        texts = [f"Instruct: {QWEN_INSTR}\nQuery: {t}" for t in texts]
    enc = tok(texts, padding=True, truncation=True, max_length=MAXLEN,
              return_tensors="pt").to(DEV)
    out = model(**enc)
    if is_qwen:
        last = enc["attention_mask"].sum(dim=1) - 1
        vecs = out.last_hidden_state[torch.arange(len(texts)), last]
    else:
        vecs = out.last_hidden_state[:, 0]
    return torch.nn.functional.normalize(vecs, dim=-1)


@torch.no_grad()
def load_model(path_or_id: str, is_qwen: bool):
    kw = dict(torch_dtype=torch.float16, trust_remote_code=True) if is_qwen else \
         dict(torch_dtype=torch.float16)
    tok = AutoTokenizer.from_pretrained(path_or_id, trust_remote_code=True)
    model = AutoModel.from_pretrained(path_or_id, **kw).to(DEV).eval()
    return tok, model


def evaluate(tok, model, is_qwen: bool, corpus: list, sets: dict) -> dict:
    cvecs = embed(model, tok, [c["body"] for c in corpus], is_qwen, False)
    out = {}
    for set_name, spec in sets.items():
        r1 = r5 = mrr = 0.0
        for q in spec["queries"]:
            qv = embed(model, tok, [q["text"]], is_qwen, True)[0]
            sims = cvecs @ qv
            rank = int((sims >= sims.max()).nonzero()[0][0]) if False else None
            order = torch.argsort(sims, descending=True).tolist()
            ranked = [corpus[j]["name"] for j in order]
            pos = ranked.index(q["gold"]) + 1 if q["gold"] in ranked else 10**9
            r1 += 1.0 if pos == 1 else 0.0
            r5 += 1.0 if pos <= 5 else 0.0
            mrr += 1.0 / pos
        n = len(spec["queries"])
        out[set_name] = {"n": n, "recall@1": round(r1 / n, 4),
                         "recall@5": round(r5 / n, 4), "MRR": round(mrr / n, 4)}
    return out


def main():
    corpus = load_corpus()
    print("corpus:", len(corpus))
    random.seed(42)
    sample = random.sample(corpus, REL_SAMPLES)
    set_a = [{"text": c["body"][:200], "gold": c["name"]} for c in sample]
    set_b = [{"text": c["body"][:200], "gold": c["name"]}
             for c in sample if cjk_ratio(c["body"]) > 0.5]
    set_c = [
        {"text": "9876 daemon ping 协议要求", "gold": "daemon-9876-watchdog-rootcause-20260908.md"},
        {"text": "PyPI nautilus-compass 发布", "gold": "pypi-311-published-20260906.md"},
        {"text": "LME-V2 451 题基准归属", "gold": "lmev2-upstream-attribution-20260902.md"},
    ]
    sets = {"A_all": {"queries": set_a}, "B_cjk": {"queries": set_b}, "C_live": {"queries": set_c}}
    print({k: len(v["queries"]) for k, v in sets.items()})

    results = {}
    for label, path, is_qwen in [
        ("bge-m3", BGE_PATH, False),
        ("qwen3-emb-0.6B", QWEN032, True),
        ("qwen3-emb-4B", QWEN4B, True),
    ]:
        try:
            t0 = time.time()
            tok, model = load_model(path, is_qwen)
            results[label] = evaluate(tok, model, is_qwen, corpus, sets)
            results[label]["load_embed_secs"] = round(time.time() - t0, 1)
            print(label, json.dumps(results[label], ensure_ascii=False))
            del tok, model
            torch.cuda.empty_cache()
        except Exception as e:
            results[label] = {"error": str(e)[:300]}
            print(label, "ERROR", str(e)[:200])
    out = "/root/vdd4/emb_bakeoff/results.json"
    json.dump(results, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("WROTE", out)


if __name__ == "__main__":
    main()
