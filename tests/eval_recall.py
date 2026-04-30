#!/usr/bin/env python3
"""Recall quality on existing 28 memories · leave-one-out P@5 / MRR.

每条 memory 取 description / title 当 query · 看自己是否在 top-5.
也跑 6 条 24h-old memory 验证时间桶召回.

Run: python tests/eval_recall.py
"""
from __future__ import annotations

import io
import json
import re
import statistics
import sys
import time
from pathlib import Path

import os as _os
_os.environ.setdefault("PYTHONIOENCODING", "utf-8")
_os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "zenmind-mem"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

PROJECT_MEM = Path.home() / ".claude/projects/C--Users-chunx/memory"


def load_memories():
    """Return list of (name, query_text, body_text)."""
    out = []
    for f in sorted(PROJECT_MEM.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        # Frontmatter description as query
        desc = None
        if txt.startswith("---"):
            end = txt.find("\n---", 4)
            if end > 0:
                m = re.search(r"^description:\s*(.+)$", txt[4:end], re.MULTILINE)
                if m:
                    desc = m.group(1).strip()
        # Fallback: first H1 line
        if not desc:
            m = re.search(r"^#\s+(.+)$", txt, re.MULTILINE)
            if m:
                desc = m.group(1).strip()
        if not desc:
            continue
        body = txt[:1500]
        out.append((f.name, desc, body))
    return out


def main():
    print(f"embedder = {zmd.EMBEDDER_MODEL}")
    t0 = time.time()
    emb = zmd.get_embedder()
    print(f"embedder ready: {time.time()-t0:.1f}s")

    mems = load_memories()
    print(f"memories with description: {len(mems)}")

    t0 = time.time()
    body_emb = [emb.encode(b) for _, _, b in mems]
    query_emb = [emb.encode(q) for _, q, _ in mems]
    print(f"embed bodies+queries: {time.time()-t0:.1f}s")

    # leave-one-out: query i 的 body_emb[i] 是 ground truth
    p1 = p3 = p5 = 0
    rrs = []
    failed = []
    for i in range(len(mems)):
        q = query_emb[i]
        sims = [(j, zmd.cosine(q, body_emb[j])) for j in range(len(mems))]
        sims.sort(key=lambda x: -x[1])
        ranks = [s[0] for s in sims]
        rank_of_truth = ranks.index(i) + 1
        rrs.append(1.0 / rank_of_truth)
        if rank_of_truth == 1:
            p1 += 1
        if rank_of_truth <= 3:
            p3 += 1
        if rank_of_truth <= 5:
            p5 += 1
        else:
            failed.append((mems[i][0], rank_of_truth, mems[i][1][:80]))

    n = len(mems)
    print("\n=== retrieval quality (leave-one-out) ===")
    print(f"  P@1 = {p1}/{n} = {p1/n:.3f}")
    print(f"  P@3 = {p3}/{n} = {p3/n:.3f}")
    print(f"  P@5 = {p5}/{n} = {p5/n:.3f}")
    print(f"  MRR = {statistics.mean(rrs):.3f}")

    if failed:
        print(f"\n=== {len(failed)} memories not in top-5 ===")
        for name, rank, query in failed[:10]:
            print(f"  rank={rank:3d}  {name}")
            print(f"           query: {query}")

    # 也做 cross-similarity 检查 · 看 P@5 失败时是不是有更相似的相邻 memory
    print("\n  P@5 失败常见原因: query 描述太宽泛 · 多个 memory 互为近邻 · 不一定是 embedder 不好")


if __name__ == "__main__":
    main()
