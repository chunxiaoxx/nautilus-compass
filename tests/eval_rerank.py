#!/usr/bin/env python3
"""LongMemEval-S retrieval + BGE CrossEncoder rerank · 测 reranker 提升量.

Pipeline:
  1. bi-encoder (default m3) retrieve top-K candidates  (K=20)
  2. cross-encoder (BAAI/bge-reranker-v2-m3) rerank → top-5
  3. 跟无 rerank baseline 对比

Run:
  python tests/eval_rerank.py              # subset 4 默认
  python tests/eval_rerank.py --full       # full subset
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

PLUGIN = Path.home() / ".claude" / "plugins" / "zenmind-mem"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

DATASET_PATH = Path(os.environ.get(
    "ZMM_LONGMEMEVAL_PATH",
    "C:/tmp/longmemeval_subset12.json",
))
RERANKER_PATH = os.environ.get(
    "ZMM_RERANKER_MODEL",
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"),
)
# TOP_K_RETRIEVE = N: bi-encoder 拿 top-N 给 reranker
# 用 full haystack (50) 让 reranker 看全部候选 · production 选 30-50 看 latency vs quality
TOP_K_RETRIEVE = 50
TOP_K_RERANK = 5


def session_to_text(session, max_chars=600):
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return "\n".join(parts)[:max_chars]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--subset", type=int, default=4)
    args = ap.parse_args()

    print(f"bi-encoder: {zmd.EMBEDDER_MODEL}")
    print(f"reranker:   {RERANKER_PATH}")

    # Load reranker
    from sentence_transformers import CrossEncoder
    t0 = time.time()
    print("loading CrossEncoder ...")
    reranker = CrossEncoder(RERANKER_PATH, device="cpu")
    print(f"reranker ready: {time.time()-t0:.1f}s")

    emb = zmd.get_embedder()
    print(f"bi-encoder ready")

    data = json.load(open(DATASET_PATH, encoding="utf-8"))
    if not args.full:
        # subset 等量平衡 6 type
        per = max(1, args.subset // 6)
        by_type = defaultdict(list)
        for d in data:
            by_type[d["question_type"]].append(d)
        data = [x for t in sorted(by_type) for x in by_type[t][:per]]
    print(f"questions: {len(data)}")

    p1_b = p3_b = p5_b = 0   # baseline (bi-encoder only)
    p1_r = p3_r = p5_r = 0   # rerank
    rrs_b, rrs_r = [], []
    type_metrics = defaultdict(lambda: {"n": 0, "rrs_b": [], "rrs_r": [],
                                         "p5_b": 0, "p5_r": 0})

    t_start = time.time()
    for i, q in enumerate(data):
        question = q["question"]
        truth_ids = set(q["answer_session_ids"])
        sess_ids = q["haystack_session_ids"]
        sessions = q["haystack_sessions"]
        sess_texts = [session_to_text(s) for s in sessions]

        # Step 1: bi-encoder retrieve top-K
        q_emb = emb.encode(question)
        sess_embs = [emb.encode(t) for t in sess_texts]
        sims = [(sess_ids[j], zmd.cosine(q_emb, sess_embs[j]), j) for j in range(len(sess_ids))]
        sims.sort(key=lambda x: -x[1])

        # Baseline rank (no rerank)
        baseline_rank = None
        for r, (sid, _, _) in enumerate(sims, 1):
            if sid in truth_ids:
                baseline_rank = r
                break

        # Step 2: cross-encoder rerank top-K
        topk = sims[:TOP_K_RETRIEVE]
        pairs = [(question, sess_texts[idx]) for _, _, idx in topk]
        rerank_scores = reranker.predict(pairs)
        reranked = sorted(zip(topk, rerank_scores), key=lambda x: -x[1])

        rerank_rank = None
        for r, ((sid, _, _), _) in enumerate(reranked, 1):
            if sid in truth_ids:
                rerank_rank = r
                break

        qt = q["question_type"]
        type_metrics[qt]["n"] += 1
        if baseline_rank:
            rrs_b.append(1.0 / baseline_rank)
            type_metrics[qt]["rrs_b"].append(1.0 / baseline_rank)
            if baseline_rank <= 1: p1_b += 1
            if baseline_rank <= 3: p3_b += 1
            if baseline_rank <= 5: p5_b += 1; type_metrics[qt]["p5_b"] += 1
        else:
            rrs_b.append(0.0)
        if rerank_rank:
            rrs_r.append(1.0 / rerank_rank)
            type_metrics[qt]["rrs_r"].append(1.0 / rerank_rank)
            if rerank_rank <= 1: p1_r += 1
            if rerank_rank <= 3: p3_r += 1
            if rerank_rank <= 5: p5_r += 1; type_metrics[qt]["p5_r"] += 1
        else:
            rrs_r.append(0.0)

        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (len(data) - i - 1)
        print(f"  [{i+1}/{len(data)}] {qt:30s} base={baseline_rank or 'N/A':>4} rr={rerank_rank or 'N/A':>4}  "
              f"({len(sessions)} sess · {elapsed:.0f}s · ETA {eta:.0f}s)", flush=True)

    n = len(data)
    print(f"\n=== Baseline (bi-encoder only · {zmd.EMBEDDER_MODEL}) ===")
    print(f"  P@1={p1_b}/{n}={p1_b/n:.3f} · P@5={p5_b}/{n}={p5_b/n:.3f} · MRR={statistics.mean(rrs_b):.3f}")
    print(f"\n=== With Reranker (top-{TOP_K_RETRIEVE} → CrossEncoder bge-reranker-v2-m3) ===")
    print(f"  P@1={p1_r}/{n}={p1_r/n:.3f} · P@5={p5_r}/{n}={p5_r/n:.3f} · MRR={statistics.mean(rrs_r):.3f}")
    print(f"\n=== Lift ===")
    print(f"  ΔP@1={p1_r/n - p1_b/n:+.3f}  ΔP@5={p5_r/n - p5_b/n:+.3f}  ΔMRR={statistics.mean(rrs_r)-statistics.mean(rrs_b):+.3f}")

    print(f"\n=== by question_type ===")
    for qt in sorted(type_metrics):
        m = type_metrics[qt]
        if m["n"] == 0: continue
        mrr_b = statistics.mean(m["rrs_b"]) if m["rrs_b"] else 0
        mrr_r = statistics.mean(m["rrs_r"]) if m["rrs_r"] else 0
        print(f"  {qt:30s} n={m['n']:2d}  base P@5={m['p5_b']/m['n']:.2f} MRR={mrr_b:.3f}  →  rerank P@5={m['p5_r']/m['n']:.2f} MRR={mrr_r:.3f}")

    out = zmd.CACHE_DIR / f"eval_rerank_{int(time.time())}.json"
    summary = {
        "embedder": zmd.EMBEDDER_MODEL, "reranker": RERANKER_PATH,
        "n": n,
        "baseline": {"P@1": p1_b/n, "P@5": p5_b/n, "MRR": statistics.mean(rrs_b)},
        "rerank":   {"P@1": p1_r/n, "P@5": p5_r/n, "MRR": statistics.mean(rrs_r)},
        "by_type": {qt: {"baseline_MRR": statistics.mean(m["rrs_b"]) if m["rrs_b"] else 0,
                          "rerank_MRR": statistics.mean(m["rrs_r"]) if m["rrs_r"] else 0,
                          "baseline_P@5": m["p5_b"]/m["n"], "rerank_P@5": m["p5_r"]/m["n"],
                          "n": m["n"]} for qt, m in type_metrics.items()},
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  详细结果: {out}")


if __name__ == "__main__":
    main()
