#!/usr/bin/env python3
"""Drift detection w/ CrossEncoder · 跟 bi-encoder cosine top-3 mean 对比.

Hypothesis: CrossEncoder(prompt, anchor) 比 cosine(emb(prompt), emb(anchor))
更精确, 因为 cross-encoder 看 token interaction 不只 vector cosine.

Pipeline:
  1. 用同一个 100 prompt set (50 aligned + 50 deviation, 来自 eval_drift.py)
  2. baseline: bi-encoder top-3 mean alignment - top-3 mean deviation
  3. with-rerank: CrossEncoder 给每 (prompt, anchor) 对打分 → top-3 mean
  4. 比 ROC AUC

预期: AUC 0.92 → 0.94+. 如果只 +0.01 就不值得加 hook (latency cost ≥ +0.5s).
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "nautilus-compass"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

# Import 测试集 from eval_drift.py
sys.path.insert(0, str(PLUGIN / "tests"))
from eval_drift import ALIGNED, DEVIATION  # noqa: E402

RERANKER_PATH = os.environ.get(
    "ZMM_RERANKER_MODEL",
    str(Path.home() / ".cache/modelscope/hub/models/BAAI/bge-reranker-v2-m3"),
)
TOP_K = 3


def main():
    print(f"bi-encoder: {zmd.EMBEDDER_MODEL}")
    print(f"reranker:   {RERANKER_PATH}")

    # Load both models
    from sentence_transformers import CrossEncoder
    t0 = time.time()
    print("loading CrossEncoder ...")
    reranker = CrossEncoder(RERANKER_PATH, device="cpu")
    print(f"reranker ready: {time.time()-t0:.1f}s")
    emb = zmd.get_embedder()
    print(f"bi-encoder ready")

    # Load anchors
    anchors = json.loads((zmd.ANCHORS_PATH).read_text(encoding="utf-8"))
    pos_anchors = anchors["positive_anchors"]
    neg_anchors = anchors["negative_anchors"]
    pos_emb = [emb.encode(p) for p in pos_anchors]
    neg_emb = [emb.encode(n) for n in neg_anchors]

    def score_bi(prompt):
        """Baseline: bi-encoder top-3 mean."""
        e = emb.encode(prompt)
        pos_sims = sorted((zmd.cosine(e, pe) for pe in pos_emb), reverse=True)[:TOP_K]
        neg_sims = sorted((zmd.cosine(e, ne) for ne in neg_emb), reverse=True)[:TOP_K]
        return sum(pos_sims)/TOP_K - sum(neg_sims)/TOP_K

    def score_cross(prompt):
        """CrossEncoder top-3 mean."""
        pos_pairs = [(prompt, p) for p in pos_anchors]
        neg_pairs = [(prompt, n) for n in neg_anchors]
        pos_scores = sorted(reranker.predict(pos_pairs).tolist(), reverse=True)[:TOP_K]
        neg_scores = sorted(reranker.predict(neg_pairs).tolist(), reverse=True)[:TOP_K]
        return sum(pos_scores)/TOP_K - sum(neg_scores)/TOP_K

    print(f"\nscoring 100 prompts (bi vs cross) ...")
    t0 = time.time()
    bi_aligned = [score_bi(p) for p in ALIGNED]
    bi_deviation = [score_bi(p) for p in DEVIATION]
    print(f"  bi done · {time.time()-t0:.1f}s")
    t0 = time.time()
    cross_aligned = [score_cross(p) for p in ALIGNED]
    cross_deviation = [score_cross(p) for p in DEVIATION]
    print(f"  cross done · {time.time()-t0:.1f}s")

    def auc(pos, neg):
        n1, n2 = len(pos), len(neg)
        wins = ties = 0
        for ps in pos:
            for ns in neg:
                if ps > ns: wins += 1
                elif ps == ns: ties += 1
        return (wins + 0.5 * ties) / (n1 * n2)

    bi_auc = auc(bi_aligned, bi_deviation)
    cross_auc = auc(cross_aligned, cross_deviation)

    print(f"\n=== AUC comparison ===")
    print(f"  bi-encoder (cosine top-3 mean):     ROC AUC = {bi_auc:.4f}")
    print(f"  CrossEncoder (rerank score top-3):  ROC AUC = {cross_auc:.4f}")
    print(f"  Δ AUC = {cross_auc - bi_auc:+.4f}")

    # Latency check
    print(f"\n=== Latency per scoring (median over 5) ===")
    import time as _t
    samples = []
    for p in ALIGNED[:5]:
        s = _t.time(); score_bi(p); samples.append(_t.time() - s)
    print(f"  bi-encoder:    {statistics.median(samples)*1000:.0f}ms")
    samples = []
    for p in ALIGNED[:5]:
        s = _t.time(); score_cross(p); samples.append(_t.time() - s)
    print(f"  CrossEncoder:  {statistics.median(samples)*1000:.0f}ms")

    print(f"\n=== 决策建议 ===")
    if cross_auc - bi_auc < 0.01:
        print(f"  Δ AUC < 0.01 · CrossEncoder 提升不显著 · 不值得加 hook latency cost")
    elif cross_auc - bi_auc < 0.03:
        print(f"  Δ AUC 0.01-0.03 · 边际提升 · 可作为 opt-in CLI mode (--strict)")
    else:
        print(f"  Δ AUC ≥ 0.03 · 显著提升 · 值得加 hook (但 latency 看用户接受度)")


if __name__ == "__main__":
    main()
