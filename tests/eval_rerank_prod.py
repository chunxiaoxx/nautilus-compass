#!/usr/bin/env python3
"""Task 1.4 · validate the PRODUCTION recall reranker path on LongMemEval.

Unlike tests/eval_rerank.py (which loads its own inline CrossEncoder), this
routes candidates through the ACTUAL production functions
`daemon._rerank_top()` + `daemon._get_reranker()` used by handle_request recall,
proving the wired-in production code delivers the benchmark lift — not a
parallel benchmark implementation.

Pipeline per question:
  1. bi-encoder (bge-m3) retrieve → dense-ordered `top` = [(score, entry), ...]
     entry = {"path": session_id, "embed_text": session_text}  (same shape recall builds)
  2. COMPASS_PROD_RERANK=1 → daemon._rerank_top(question, top, top_k) reorders.
  3. compare P@1/P@5/MRR: dense baseline vs production-reranked.

Run:
  ZMM_DEVICE=cuda python tests/eval_rerank_prod.py                 # subset12 default
  python tests/eval_rerank_prod.py --dataset C:/tmp/longmemeval_subset12.json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")
# turn the production flag ON for this eval (must be set before daemon import so
# the module-level _PROD_RERANK_USE picks it up)
os.environ["COMPASS_PROD_RERANK"] = "1"

PLUGIN = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

# candidate width fed to the cross-encoder (matches production _RERANK_CANDIDATES)
TOP_K_FINAL = 5


def session_to_text(session, max_chars=600):
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return "\n".join(parts)[:max_chars]


def _first_truth_rank(ranked_entries, truth_ids):
    for r, e in enumerate(ranked_entries, 1):
        if e["path"] in truth_ids:
            return r
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", default="C:/tmp/longmemeval_subset12.json")
    ap.add_argument("--top-k", type=int, default=TOP_K_FINAL)
    args = ap.parse_args()

    assert zmd._PROD_RERANK_USE, "COMPASS_PROD_RERANK must be on for prod-path eval"
    print(f"prod flag: COMPASS_PROD_RERANK={zmd._PROD_RERANK_USE} · "
          f"candidates={zmd._RERANK_CANDIDATES} · reranker={zmd._RERANKER_MODEL}")

    emb = zmd.get_embedder()
    print("bi-encoder ready · warming production reranker singleton ...")
    t0 = time.time()
    zmd._get_reranker()  # production lazy singleton
    print(f"reranker ready: {time.time()-t0:.1f}s")

    data = json.load(open(args.dataset, encoding="utf-8"))
    print(f"questions: {len(data)} · dataset: {args.dataset}")

    p1_b = p5_b = 0
    p1_r = p5_r = 0
    rrs_b, rrs_r = [], []
    by_type = defaultdict(lambda: {"n": 0, "p5_b": 0, "p5_r": 0,
                                    "rrs_b": [], "rrs_r": []})

    t_start = time.time()
    for i, q in enumerate(data):
        question = q["question"]
        truth_ids = set(q["answer_session_ids"])
        sess_ids = q["haystack_session_ids"]
        sessions = q["haystack_sessions"]
        sess_texts = [session_to_text(s) for s in sessions]

        # Step 1: bi-encoder retrieve → dense-ordered `top` (production entry shape)
        q_emb = emb.encode(question)
        scored = []
        for sid, text in zip(sess_ids, sess_texts):
            s = zmd.cosine(q_emb, emb.encode(text))
            scored.append((s, {"path": sid, "embed_text": text}))
        scored.sort(key=lambda x: -x[0])

        # dense baseline order (truncated to candidate width, like production
        # would retrieve when reranking)
        dense_entries = [e for _s, e in scored]

        # Step 2: PRODUCTION rerank function over a widened candidate set
        cand = scored[:max(args.top_k, zmd._RERANK_CANDIDATES)]
        reranked = zmd._rerank_top(question, cand, args.top_k)
        reranked_entries = [e for _s, e in reranked]

        rank_b = _first_truth_rank(dense_entries, truth_ids)
        rank_r = _first_truth_rank(reranked_entries, truth_ids)

        qt = q["question_type"]
        by_type[qt]["n"] += 1
        if rank_b:
            rrs_b.append(1.0 / rank_b)
            by_type[qt]["rrs_b"].append(1.0 / rank_b)
            if rank_b <= 1: p1_b += 1
            if rank_b <= 5: p5_b += 1; by_type[qt]["p5_b"] += 1
        else:
            rrs_b.append(0.0)
        if rank_r:
            rrs_r.append(1.0 / rank_r)
            by_type[qt]["rrs_r"].append(1.0 / rank_r)
            if rank_r <= 1: p1_r += 1
            if rank_r <= 5: p5_r += 1; by_type[qt]["p5_r"] += 1
        else:
            rrs_r.append(0.0)

        elapsed = time.time() - t_start
        print(f"  [{i+1}/{len(data)}] {qt:28s} dense={rank_b or 'N/A':>4} "
              f"prod_rerank={rank_r or 'N/A':>4}  ({elapsed:.0f}s)", flush=True)

    n = len(data)
    print(f"\n=== Dense baseline (bge-m3) ===")
    print(f"  P@1={p1_b/n:.3f} · P@5={p5_b/n:.3f} · MRR={statistics.mean(rrs_b):.3f}")
    print(f"=== PRODUCTION path (_rerank_top · bge-reranker-v2-m3) ===")
    print(f"  P@1={p1_r/n:.3f} · P@5={p5_r/n:.3f} · MRR={statistics.mean(rrs_r):.3f}")
    print(f"=== Lift ===")
    print(f"  ΔP@1={p1_r/n-p1_b/n:+.3f}  ΔP@5={p5_r/n-p5_b/n:+.3f}  "
          f"ΔMRR={statistics.mean(rrs_r)-statistics.mean(rrs_b):+.3f}")
    print(f"\n=== by question_type ===")
    for qt in sorted(by_type):
        m = by_type[qt]
        mrr_b = statistics.mean(m["rrs_b"]) if m["rrs_b"] else 0
        mrr_r = statistics.mean(m["rrs_r"]) if m["rrs_r"] else 0
        print(f"  {qt:28s} n={m['n']:2d}  dense P@5={m['p5_b']/m['n']:.2f} "
              f"MRR={mrr_b:.3f}  →  prod P@5={m['p5_r']/m['n']:.2f} MRR={mrr_r:.3f}")


if __name__ == "__main__":
    main()
