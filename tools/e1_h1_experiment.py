#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""E1-TUNE H1 单独归因实验(R438): 库侧去重/合并 → 复跑同口径检索。

设计: 复制语料快照 → 合并 8 对同主题双文档(被并者内容 append 进保留者,防丢内容)
→ gold 重映射 → 与 R437 归因完全同口径(bge-m3 CLS/normalize/512)复跑 → 对比。
H1/H2 分开归因: 本脚本只动库结构,不动 embedder/rerank。
"""
import glob
import json
import os
import re
import shutil

import torch
from tokenizers import Tokenizer
from transformers import AutoModel

SRC = "/root/vdf/emb_bakeoff"
DST = "/root/vdf/emb_bakeoff_h1"
OUT = SRC + "/e1_h1_result.json"
BGE = "/root/vdd4/modelscope/models/models/BAAI--bge-m3/snapshots/master"
DEV = "cuda"
MAXLEN = 512

# (保留者, 被并者) — 扫描判据: 文件名 token Jaccard>=0.5 + 人工确认同主题
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
GONE = {b for _, b in MERGE_PAIRS}
REMAP = {b: a for a, b in MERGE_PAIRS}


def prepare_corpus() -> list:
    if os.path.exists(DST):
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST)
    for f in ("A_plus_queries.json", "e1_attribution.json", "e1_attr.log", "eval.py",
              "eval_4b.py", "gen_a_plus.py", "gen_smoke.py", "e1_failure_attribution.py",
              "e1_h1_result.json"):
        p = os.path.join(DST, f)
        if os.path.exists(p):
            os.remove(p)
    merged = []
    for keeper, gone in MERGE_PAIRS:
        kp, gp = os.path.join(DST, keeper), os.path.join(DST, gone)
        if os.path.exists(kp) and os.path.exists(gp):
            body = open(gp, encoding="utf-8", errors="replace").read()
            with open(kp, "a", encoding="utf-8") as f:
                f.write("\n\n<!-- merged from " + gone + " -->\n\n" + body)
            os.remove(gp)
            merged.append(gone)
    return merged


def parse_md(path: str) -> tuple:
    t = open(path, encoding="utf-8", errors="replace").read()
    if t.startswith("---"):
        m = re.match(r"---\n.*?\n---\n?", t, re.S)
        if m:
            t = t[m.end():]
    return path.rsplit("/", 1)[-1], t.strip()[:2000]


def load_corpus() -> list:
    out = []
    for p in sorted(glob.glob(DST + "/*.md")):
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
    vecs = out.last_hidden_state[:, 0]
    return torch.nn.functional.normalize(vecs, dim=-1)


def main():
    merged = prepare_corpus()
    corpus = load_corpus()
    queries = json.load(open(SRC + "/A_plus_queries.json", encoding="utf-8"))
    tok = Tokenizer.from_file(BGE.rstrip("/") + "/tokenizer.json")
    model = AutoModel.from_pretrained(BGE, torch_dtype=torch.float16).to(DEV).eval()

    cvecs = embed(model, tok, [c["body"] for c in corpus])
    names = [c["name"] for c in corpus]
    idx = {n: i for i, n in enumerate(names)}

    r1 = r5 = mrr = 0
    per = []
    for q in queries:
        gold = REMAP.get(q["gold"], q["gold"])
        qv = embed(model, tok, [q["text"]])[0]
        sims = (cvecs @ qv).tolist()
        order = sorted(range(len(sims)), key=lambda i: -sims[i])
        rank = order.index(idx[gold]) + 1 if gold in idx else -1
        top1 = names[order[0]]
        hit = rank == 1
        r1 += hit
        r5 += 1 <= rank <= 5
        mrr += 1.0 / rank if rank > 0 else 0.0
        per.append({"query": q["text"][:40], "gold": gold, "rank": rank, "top1": top1,
                    "verdict": "HIT" if hit else "MISS"})
    n = len(per)
    result = {
        "n_queries": n, "n_corpus_after_merge": len(corpus),
        "merged_away": merged,
        "recall_at_1": round(r1 / n, 4), "recall_at_5": round(r5 / n, 4),
        "mrr": round(mrr / n, 4),
        "baseline": {"recall_at_1": 0.4, "recall_at_5": 0.6667, "mrr": 0.4994},
        "delta_r1": round(r1 / n - 0.4, 4),
        "per_query": per,
    }
    json.dump(result, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("H1 SUMMARY", json.dumps({k: result[k] for k in
          ("recall_at_1", "recall_at_5", "mrr", "delta_r1", "n_corpus_after_merge")}, ensure_ascii=False))
    print("merged away:", len(merged), "corpus:", len(corpus))
    for p in per:
        if p["verdict"] == "MISS":
            print(f"  MISS rank={p['rank']} {p['query']} | top1={p['top1'][:30]}")


if __name__ == "__main__":
    main()
