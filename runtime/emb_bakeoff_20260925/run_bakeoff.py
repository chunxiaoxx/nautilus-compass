# -*- coding: utf-8 -*-
"""向量对拍执行:bge-m3 vs Qwen3-Embedding-0.6B,自家记忆语料召回。
判据见 PREREGISTER.md(预注册,只许更严)。dense-only cosine。
用法:python run_bakeoff.py"""
import json
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer

MEMDIR = (Path.home() / ".claude/projects"
          / "C--Users-chunx-Projects-nautilus-compass/memory")
HERE = Path(__file__).parent
MODELS = {"bge-m3": "BAAI/bge-m3", "qwen3-0.6b": "Qwen/Qwen3-Embedding-0.6B"}
KS = (1, 5, 10)


def load_corpus():
    docs = {}
    for f in sorted(MEMDIR.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        docs[f.name] = f.read_text(encoding="utf-8")[:4000]
    return docs


def embed(model, texts, is_query, use_query_prompt=False):
    kw = {"normalize_embeddings": True, "batch_size": 32,
          "show_progress_bar": False}
    if is_query and use_query_prompt:
        # Qwen3-Embedding 官方推荐检索指令前缀(ST 自动带 prompt_name)
        try:
            return model.encode(texts, prompt_name="query", **kw)
        except Exception:
            pass
    return model.encode(texts, **kw)


def metrics(ranks):
    """ranks=各查询 gold 的排名(1-based,未命中=inf)。"""
    n = len(ranks)
    rec = {k: sum(1 for r in ranks if r <= k) / n for k in KS}
    mrr = sum(1.0 / r for r in ranks if np.isfinite(r)) / n
    return {**{f"recall@{k}": round(rec[k], 4) for k in KS},
            "mrr@10": round(mrr, 4)}


def run():
    docs = load_corpus()
    qf = json.loads((HERE / "queries.json").read_text(encoding="utf-8"))
    names = list(docs)
    texts = [docs[n] for n in names]
    idx = {n: i for i, n in enumerate(names)}
    queries = [(q["doc"], "cn", q["q_cn"]) for q in qf["queries"]]
    queries += [(q["doc"], "en", q["q_en"]) for q in qf["queries"]]
    print(f"corpus {len(names)} docs · queries {len(queries)}")

    out = {}
    for label, mid in MODELS.items():
        m = SentenceTransformer(mid)
        qprompt = "qwen" in mid.lower()
        D = embed(m, texts, False)
        Q = embed(m, [q for _, _, q in queries], True,
                  use_query_prompt=qprompt)
        S = Q @ D.T  # (n_queries, n_docs),已归一化=cosine
        ranks_all, ranks_cn, ranks_en = [], [], []
        for i, (gold, lang, _) in enumerate(queries):
            rank = int((S[i] > S[i][idx[gold]]).sum()) + 1
            ranks_all.append(rank)
            (ranks_cn if lang == "cn" else ranks_en).append(rank)
        out[label] = {"all": metrics(ranks_all),
                      "cn": metrics(ranks_cn), "en": metrics(ranks_en)}
        print(label, json.dumps(out[label]), flush=True)
        del m
    (HERE / "bakeoff_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8",
        newline="\n")
    return out


if __name__ == "__main__":
    run()
