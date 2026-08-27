#!/usr/bin/env python3
"""LOCOMO-10 retrieval evaluation · nautilus-compass vs (later) mem0.

Protocol (retrieval-only, aligned with our LongMemEval-S protocol):
  - unit  : one session (turns joined; LOCOMO has ~19 sessions/conv, ~9K tokens)
  - truth : qa.evidence "D<n>:<turn>" maps to session_<n>
  - metric: P@1 / P@5 / MRR overall + per category
    (1 single-hop · 2 multi-hop · 3 temporal · 4 open-domain · 5 adversarial)
  - pipeline: bge-m3 dense (m3-only) or + bge-reranker (m3-rerank)
    19 sessions/conv < K so candidate-pool truncation is a non-issue here.

mem0-paper e2e comparison (LLM-judge 0-5) is a separate later step; this file
locks the retrieval layer first.

Run (cloud, from repo root):
  ZMM_LONGMEMEVAL_PATH=.cache/locomo10.json python3 tests/eval_locomo.py
Env: ZMM_LOCOMO_PATH · ZMM_DEVICE · ZMM_RETRIEVAL_ONLY(=1 default here)
"""
from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import daemon as zmd  # noqa: E402  (embedder + cosine, same as LongMemEval eval)

LOCOMO_PATH = Path(os.environ.get("ZMM_LOCOMO_PATH", ".cache/locomo10.json"))
USE_RERANK = os.environ.get("ZMM_LOCOMO_RERANK", "0") == "1"
MAX_SESS_CHARS = 2000

CATEGORY = {"1": "single-hop", "2": "multi-hop", "3": "temporal",
            "4": "open-domain", "5": "adversarial"}


def session_text(turns, max_chars=MAX_SESS_CHARS):
    parts = [f"[{t.get('speaker', '?')}] {t.get('text', '')}" for t in turns]
    return "\n".join(parts)[:max_chars]


def evidence_sessions(qa):
    """['D1:3','D2:7'] -> {'session_1','session_2'}"""
    out = set()
    for e in qa.get("evidence", []):
        m = re.match(r"D(\d+):", e)
        if m:
            out.add(f"session_{int(m.group(1))}")
    return out


def main():
    data = json.load(open(LOCOMO_PATH, encoding="utf-8"))
    print(f"LOCOMO-10: {len(data)} conversations · {sum(len(c['qa']) for c in data)} questions")

    emb = zmd.get_embedder()
    reranker = None
    if USE_RERANK:
        from sentence_transformers import CrossEncoder
        try:
            import torch
            device = os.environ.get("ZMM_DEVICE", "cuda" if torch.cuda.is_available() else "cpu")
        except Exception:
            device = "cpu"
        reranker = CrossEncoder(
            os.environ.get("ZMM_RERANKER_MODEL", "BAAI/bge-reranker-v2-m3"), device=device)
        print(f"reranker on ({device})")

    # cross-question text-addressed cache (same trick as LongMemEval eval)
    cache: dict = {}
    def cached(text):
        key = hash(text)
        if key not in cache:
            cache[key] = emb.encode(text)
        return cache[key]

    rows = []
    t0 = time.time()
    for ci, conv in enumerate(data):
        c = conv["conversation"]
        sess_names = sorted([k for k in c if k.startswith("session_") and not k.endswith("date_time")],
                            key=lambda s: int(s.split("_")[1]))
        sess_texts = [session_text(c[n]) for n in sess_names]
        sess_embs = [cached(t) for t in sess_texts]
        for qa in conv["qa"]:
            q_emb = cached(qa["question"])
            sims = sorted(range(len(sess_names)), key=lambda j: -zmd.cosine(q_emb, sess_embs[j]))
            if reranker is not None:
                pairs = [(qa["question"], sess_texts[j]) for j in sims]
                scores = reranker.predict(pairs)
                sims = [j for j, _ in sorted(zip(sims, scores), key=lambda x: -x[1])]
            top5 = [sess_names[j] for j in sims[:5]]
            truth = evidence_sessions(qa)
            rank = next((i + 1 for i, s in enumerate(top5) if s in truth), None)
            rows.append({
                "conv": ci, "category": str(qa["category"]),
                "question": qa["question"][:120], "answer": qa.get("answer", ""),
                "top5": top5, "truth": sorted(truth), "rank": rank,
            })
        print(f"  conv {ci+1}/{len(data)} · {len(rows)} qs · {time.time()-t0:.0f}s", flush=True)

    n = len(rows)
    p1 = sum(1 for r in rows if r["rank"] == 1)
    p5 = sum(1 for r in rows if r["rank"] and r["rank"] <= 5)
    mrr = statistics.mean(1 / r["rank"] if r["rank"] else 0.0 for r in rows)
    print(f"\n=== LOCOMO-10 retrieval ({'m3-rerank' if USE_RERANK else 'm3-only'} · n={n}) ===")
    print(f"  P@1={p1/n:.3f}  P@5={p5/n:.3f}  MRR={mrr:.3f}")
    by = defaultdict(list)
    for r in rows:
        by[CATEGORY.get(r["category"], r["category"])].append(r)
    for cat in sorted(by):
        rs = by[cat]
        cp1 = sum(1 for r in rs if r["rank"] == 1) / len(rs)
        cp5 = sum(1 for r in rs if r["rank"] and r["rank"] <= 5) / len(rs)
        cmrr = statistics.mean(1 / r["rank"] if r["rank"] else 0.0 for r in rs)
        print(f"  {cat:14s} n={len(rs):4d}  P@1={cp1:.2f}  P@5={cp5:.2f}  MRR={cmrr:.2f}")

    out = Path.home() / ".claude/plugins/nautilus-compass/.cache/eval_locomo_retrieval.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"n": n, "P@1": p1 / n, "P@5": p5 / n, "MRR": mrr,
                   "rerank": USE_RERANK,
                   "by_category": {c: {"n": len(rs), "P@1": sum(1 for r in rs if r['rank'] == 1) / len(rs),
                                       "P@5": sum(1 for r in rs if r['rank'] and r['rank'] <= 5) / len(rs)}
                                   for c, rs in by.items()}}, f, ensure_ascii=False, indent=2)
    rows_path = out.with_name(out.stem + "_rows.jsonl")
    with open(rows_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n  summary: {out} · rows: {rows_path}")


if __name__ == "__main__":
    main()
