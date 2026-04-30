#!/usr/bin/env python3
"""Calibrate cosine thresholds for the active embedder.

切 embedder 后第一个要跑的脚本。读 28 条 memory + 50 anchors
跑两两 cosine · 出分位数 · 推荐 COSINE_MIN / NEG_ANCHOR_HIT_THRESHOLD。

Run: python tests/eval_calibrate.py
"""
from __future__ import annotations

import io
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

PROJECT_MEM = Path.home() / ".claude/projects/C--Users-chunx/memory"


def main():
    t0 = time.time()
    print(f"embedder = {zmd.EMBEDDER_MODEL}")
    emb = zmd.get_embedder()
    print(f"embedder load: {time.time()-t0:.1f}s")

    # Anchors
    anchors = json.loads((PLUGIN / "anchors.json").read_text(encoding="utf-8"))
    pos = anchors["positive_anchors"]
    neg = anchors["negative_anchors"]

    # Memory bodies
    mems = []
    for f in sorted(PROJECT_MEM.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        try:
            txt = f.read_text(encoding="utf-8")[:1500]
            mems.append((f.name, txt))
        except Exception:
            continue
    print(f"memory entries: {len(mems)} · pos anchors: {len(pos)} · neg anchors: {len(neg)}")

    t0 = time.time()
    pos_emb = [emb.encode(p) for p in pos]
    neg_emb = [emb.encode(n) for n in neg]
    mem_emb = [(name, emb.encode(body)) for name, body in mems]
    print(f"embed all: {time.time()-t0:.1f}s")

    # Distribution 1: memory ↔ memory cosine (intra-corpus相似性 baseline)
    intra = []
    for i in range(len(mem_emb)):
        for j in range(i + 1, len(mem_emb)):
            intra.append(zmd.cosine(mem_emb[i][1], mem_emb[j][1]))

    # Distribution 2: anchor ↔ memory cosine
    pos_to_mem = []
    for pe in pos_emb:
        for _, me in mem_emb:
            pos_to_mem.append(zmd.cosine(pe, me))
    neg_to_mem = []
    for ne in neg_emb:
        for _, me in mem_emb:
            neg_to_mem.append(zmd.cosine(ne, me))

    def quant(xs, qs=(0.05, 0.25, 0.5, 0.75, 0.95)):
        if not xs:
            return {}
        s = sorted(xs)
        return {f"p{int(q*100)}": round(s[int(len(s) * q)], 4) for q in qs}

    def fmt(label, xs):
        q = quant(xs)
        print(
            f"  {label:24s} n={len(xs):5d}  "
            f"min={min(xs):+.3f} p5={q['p5']:+.3f} p25={q['p25']:+.3f} "
            f"p50={q['p50']:+.3f} p75={q['p75']:+.3f} p95={q['p95']:+.3f} max={max(xs):+.3f} "
            f"mean={statistics.mean(xs):+.3f}"
        )

    print("\n=== cosine 分布 ===")
    fmt("memory ↔ memory (intra)", intra)
    fmt("pos anchors ↔ memory", pos_to_mem)
    fmt("neg anchors ↔ memory", neg_to_mem)

    # 校准建议
    print("\n=== 推荐 threshold ===")
    print(f"  COSINE_MIN              = {quant(intra)['p25']:.3f}  (memory intra p25 · 召回最低门槛)")
    print(f"  NEG_ANCHOR_HIT_THRESHOLD = {quant(neg_to_mem)['p95']:.3f}  (neg ↔ mem p95 · top 5% 才算命中负锚)")
    pos_p50 = quant(pos_to_mem)["p50"]
    neg_p50 = quant(neg_to_mem)["p50"]
    print(f"  drift baseline alignment-deviation: pos_p50={pos_p50:+.3f}  neg_p50={neg_p50:+.3f}  delta={pos_p50-neg_p50:+.3f}")
    print("  ⚠️ 把这些值更新到 daemon.py 或 ZMM_*  env vars")


if __name__ == "__main__":
    main()
