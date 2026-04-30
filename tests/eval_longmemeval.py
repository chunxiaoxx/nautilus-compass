#!/usr/bin/env python3
"""LongMemEval-S retrieval eval · 给 nautilus-compass 跑公开 benchmark.

Dataset: xiaowu0162/longmemeval (HF) · 500 questions × 6 types
本脚本测 retrieval-only · question 当 query · session 当 memory entry · ground truth = answer_session_ids

子集 (subset=50) 覆盖 6 个 question_type · 每类 ~8 题
完整 (subset=500) 在 m3 上估 ~1.5 小时

Run:
  python tests/eval_longmemeval.py             # 50 题 subset
  python tests/eval_longmemeval.py --full      # 500 题
  python tests/eval_longmemeval.py --subset 100
"""
from __future__ import annotations

import argparse
import io
import json
import os
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "nautilus-compass"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

DATASET_PATH = Path(os.environ.get(
    "ZMM_LONGMEMEVAL_PATH",
    str(Path.home() / ".cache/huggingface/hub/datasets--xiaowu0162--longmemeval/snapshots/2ec2a557f339b6c0369619b1ed5793734cc87533/longmemeval_s"),
))


def session_to_text(session, max_chars=600):
    """600 chars 让 m3 在 Windows CPU 上每 session ~1.5s · 12 题 × 50 sess ≈ 15min."""
    parts = []
    for turn in session:
        role = turn.get("role", "?")
        content = turn.get("content", "")
        parts.append(f"[{role}] {content}")
    return "\n".join(parts)[:max_chars]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--subset", type=int, default=50)
    args = ap.parse_args()

    print(f"embedder = {zmd.EMBEDDER_MODEL}")
    if not DATASET_PATH.exists():
        print(f"❌ dataset not found at {DATASET_PATH}")
        print("   download: hf_hub_download(repo_id='xiaowu0162/longmemeval', filename='longmemeval_s', repo_type='dataset')")
        sys.exit(1)

    t0 = time.time()
    emb = zmd.get_embedder()
    print(f"embedder ready: {time.time()-t0:.1f}s")

    print(f"loading {DATASET_PATH.name} ...")
    data = json.load(open(DATASET_PATH, encoding="utf-8"))
    print(f"total questions: {len(data)}")

    # 按 type 均衡 subset
    if not args.full:
        per_type = max(1, args.subset // 6)
        by_type = defaultdict(list)
        for d in data:
            by_type[d["question_type"]].append(d)
        subset = []
        for t, items in sorted(by_type.items()):
            subset.extend(items[:per_type])
        data = subset
        print(f"subset ({per_type}/type · 6 types): {len(data)} questions")

    # 跑评估
    p1 = p3 = p5 = 0
    rrs = []
    type_metrics = defaultdict(lambda: {"n": 0, "p1": 0, "p3": 0, "p5": 0, "rrs": []})

    t0 = time.time()
    for i, q in enumerate(data):
        question = q["question"]
        truth_ids = set(q["answer_session_ids"])
        sess_ids = q["haystack_session_ids"]
        sessions = q["haystack_sessions"]
        if len(sess_ids) != len(sessions):
            continue

        # Embed query + all sessions
        q_emb = emb.encode(question)
        sess_embs = [emb.encode(session_to_text(s)) for s in sessions]

        sims = [(sess_ids[j], zmd.cosine(q_emb, sess_embs[j])) for j in range(len(sess_ids))]
        sims.sort(key=lambda x: -x[1])

        # 找最高排名的 truth session
        best_rank = None
        for rank, (sid, _) in enumerate(sims, 1):
            if sid in truth_ids:
                best_rank = rank
                break

        qt = q["question_type"]
        type_metrics[qt]["n"] += 1
        if best_rank:
            rrs.append(1.0 / best_rank)
            type_metrics[qt]["rrs"].append(1.0 / best_rank)
            if best_rank <= 1:
                p1 += 1; type_metrics[qt]["p1"] += 1
            if best_rank <= 3:
                p3 += 1; type_metrics[qt]["p3"] += 1
            if best_rank <= 5:
                p5 += 1; type_metrics[qt]["p5"] += 1
        else:
            rrs.append(0.0)

        elapsed = time.time() - t0
        eta = elapsed / (i + 1) * (len(data) - i - 1)
        print(f"  [{i+1}/{len(data)}] {qt:30s} rank={best_rank or 'N/A':>4}  ({len(sessions)} sess · {time.time()-t0:.0f}s · ETA {eta:.0f}s · MRR {statistics.mean(rrs):.3f})", flush=True)

    n = len(data)
    print(f"\n=== LongMemEval-S retrieval (n={n} · embedder={zmd.EMBEDDER_MODEL}) ===")
    print(f"  P@1  = {p1}/{n} = {p1/n:.3f}")
    print(f"  P@3  = {p3}/{n} = {p3/n:.3f}")
    print(f"  P@5  = {p5}/{n} = {p5/n:.3f}")
    print(f"  MRR  = {statistics.mean(rrs):.3f}")
    print(f"\n=== by question_type ===")
    for qt in sorted(type_metrics):
        m = type_metrics[qt]
        if m["n"] == 0: continue
        mrr = statistics.mean(m["rrs"]) if m["rrs"] else 0
        print(f"  {qt:30s} n={m['n']:3d}  P@1={m['p1']/m['n']:.2f}  P@5={m['p5']/m['n']:.2f}  MRR={mrr:.3f}")

    out = zmd.CACHE_DIR / f"longmemeval_results_{int(time.time())}.json"
    summary = {
        "dataset": "longmemeval_s",
        "n": n,
        "embedder": zmd.EMBEDDER_MODEL,
        "P@1": p1 / n, "P@3": p3 / n, "P@5": p5 / n,
        "MRR": statistics.mean(rrs),
        "by_type": {qt: {"n": m["n"], "P@1": m["p1"]/max(1,m["n"]), "P@5": m["p5"]/max(1,m["n"]), "MRR": statistics.mean(m["rrs"]) if m["rrs"] else 0} for qt, m in type_metrics.items()},
    }
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  详细结果: {out}")


if __name__ == "__main__":
    main()
