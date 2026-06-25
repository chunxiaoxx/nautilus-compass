#!/usr/bin/env python3
"""Recall quality benchmark · leave-one-out P@1/3/5 + MRR, with A/B mode switch.

Each memory's description/title is the query; its body is the ground-truth hit.
Modes layer the production recall enhancements so we can read off each delta:

  D0 flat   · pure bge-m3 cosine                      (baseline floor)
  D1 poi    · + cumulative_impact boost               (apply_poi_boost_value)
  D2 tier   · + lifecycle tier additive rank bonus    (apply_tier_weight)
  D3 gemini · + Gemini query rewrite before retrieval (query_rewrite.rewrite_query)

Honest-measurement note: D1/D2 can only move ranking when the corpus actually
carries cumulative_impact / non-`working` tier frontmatter. On a corpus without
that metadata, D1≈D2≈D0 — report that as "metadata absent", never as proof the
lifecycle is useless.

Run: python tests/eval_recall.py --mode flat
     python tests/eval_recall.py --mode all   # run every mode, print delta table
"""
from __future__ import annotations

import argparse
import re
import statistics
import sys
import time
import pathlib
from pathlib import Path

import os as _os
_os.environ.setdefault("PYTHONIOENCODING", "utf-8")
_os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN_USER = Path.home() / ".claude" / "plugins" / "nautilus-compass"
# CI fallback · use repo root when user-level plugin not installed
PLUGIN = PLUGIN_USER if PLUGIN_USER.exists() else pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PLUGIN))
# repo root also on path (for recall_pkg / recall / query_rewrite imports)
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

PROJECT_MEM = Path.home() / ".claude/projects/C--Users-chunx/memory"

MODES = ("flat", "poi", "tier", "gemini")


# ---------------------------------------------------------------------------
# Pure re-rank (testable without embedder / disk)
# ---------------------------------------------------------------------------
def rerank(mode: str, entries: list) -> list:
    """Re-rank candidate list per benchmark mode.

    Args:
        mode: one of flat / poi / tier / gemini.
        entries: list of (cosine_score, entry_dict) · entry_dict carries
                 "impact" (float cumulative_impact) and "tier" (str).
    Returns:
        re-sorted list of (score, entry_dict) descending.

    Faithful to production: poi uses apply_poi_boost_value (the snapshot-hit
    value path), tier uses apply_tier_weight (the lifecycle additive bonus).
    gemini only affects the upstream query, so its rerank == tier.
    """
    if mode not in MODES:
        raise ValueError(f"unknown mode: {mode}")
    if mode == "flat":
        return sorted(entries, key=lambda x: -x[0])

    from recall_pkg.poi_weighting import apply_poi_boost_value
    boosted = []
    for score, entry in entries:
        impact = entry.get("impact", 0.0) if isinstance(entry, dict) else 0.0
        boosted.append((apply_poi_boost_value(score, impact), entry))
    boosted.sort(key=lambda x: -x[0])

    if mode in ("tier", "gemini"):
        from recall import apply_tier_weight
        boosted = apply_tier_weight(boosted)
    return boosted


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------
def _parse_front(txt: str):
    """Return (description, cumulative_impact float, tier str) from frontmatter."""
    desc = None
    impact = 0.0
    tier = "working"
    if txt.startswith("---"):
        end = txt.find("\n---", 4)
        if end > 0:
            front = txt[4:end]
            m = re.search(r"^description:\s*(.+)$", front, re.MULTILINE)
            if m:
                desc = m.group(1).strip()
            m = re.search(r"^\s*cumulative_impact:\s*(-?\d+(?:\.\d+)?)", front, re.MULTILINE)
            if m:
                try:
                    impact = float(m.group(1))
                except ValueError:
                    impact = 0.0
            m = re.search(r"^\s*tier:\s*(\w+)", front, re.MULTILINE)
            if m:
                tier = m.group(1).strip()
    if not desc:
        m = re.search(r"^#\s+(.+)$", txt, re.MULTILINE)
        if m:
            desc = m.group(1).strip()
    return desc, impact, tier


def load_memories():
    """Return list of dicts: name, query, body, impact, tier."""
    out = []
    for f in sorted(PROJECT_MEM.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        try:
            txt = f.read_text(encoding="utf-8")
        except Exception:
            continue
        desc, impact, tier = _parse_front(txt)
        if not desc:
            continue
        out.append({
            "name": f.name,
            "query": desc,
            "body": txt[:1500],
            "impact": impact,
            "tier": tier,
        })
    return out


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate(mems, body_emb, query_emb, mode, cosine):
    """Leave-one-out retrieval metrics for one mode. Returns dict."""
    p1 = p3 = p5 = 0
    rrs = []
    failed = []
    n = len(mems)
    for i in range(n):
        q = query_emb[i]
        # all candidates as (cosine, entry) carrying impact/tier + idx
        entries = [
            (cosine(q, body_emb[j]),
             {"idx": j, "impact": mems[j]["impact"], "tier": mems[j]["tier"]})
            for j in range(n)
        ]
        ranked = rerank(mode, entries)
        ranks = [e["idx"] for _, e in ranked]
        rank_of_truth = ranks.index(i) + 1
        rrs.append(1.0 / rank_of_truth)
        if rank_of_truth == 1:
            p1 += 1
        if rank_of_truth <= 3:
            p3 += 1
        if rank_of_truth <= 5:
            p5 += 1
        else:
            failed.append((mems[i]["name"], rank_of_truth, mems[i]["query"][:80]))
    return {
        "mode": mode, "n": n,
        "P@1": p1 / n, "P@3": p3 / n, "P@5": p5 / n,
        "MRR": statistics.mean(rrs),
        "failed": failed,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", default="flat",
                    choices=list(MODES) + ["all"],
                    help="recall mode (flat/poi/tier/gemini) or 'all' for delta table")
    args = ap.parse_args()

    import daemon as zmd  # local import · heavy embedder lib
    print(f"embedder = {zmd.EMBEDDER_MODEL}")
    t0 = time.time()
    emb = zmd.get_embedder()
    print(f"embedder ready: {time.time()-t0:.1f}s")

    mems = load_memories()
    n_impact = sum(1 for m in mems if m["impact"] != 0.0)
    n_nonworking = sum(1 for m in mems if m["tier"] != "working")
    print(f"memories with description: {len(mems)}")
    print(f"  carrying cumulative_impact != 0 : {n_impact}")
    print(f"  carrying tier != working        : {n_nonworking}")
    if n_impact == 0:
        print("  ⚠️  no cumulative_impact in corpus → D1(poi) WILL equal D0(flat)")
    if n_nonworking == 0:
        print("  ⚠️  all tiers == working → D2(tier) WILL equal D1(poi)")

    t0 = time.time()
    body_emb = [emb.encode(m["body"]) for m in mems]
    query_emb_flat = [emb.encode(m["query"]) for m in mems]
    print(f"embed bodies+queries: {time.time()-t0:.1f}s")

    modes = list(MODES) if args.mode == "all" else [args.mode]
    results = []
    for mode in modes:
        if mode == "gemini":
            # rewrite queries upstream (no-op + original query when not opted in)
            from query_rewrite import rewrite_query
            t0 = time.time()
            q_texts = [rewrite_query(m["query"]) for m in mems]
            n_changed = sum(1 for a, b in zip(q_texts, (m["query"] for m in mems)) if a != b)
            qe = [emb.encode(t) for t in q_texts] if n_changed else query_emb_flat
            print(f"gemini rewrite: {n_changed}/{len(mems)} queries changed "
                  f"({time.time()-t0:.1f}s)"
                  + ("" if n_changed else " → Gemini off · D3 == D2"))
        else:
            qe = query_emb_flat
        res = evaluate(mems, body_emb, qe, mode, zmd.cosine)
        results.append(res)

    print("\n=== retrieval quality (leave-one-out) ===")
    print(f"{'mode':<8} {'P@1':>7} {'P@3':>7} {'P@5':>7} {'MRR':>7}")
    base = results[0]
    for r in results:
        d = f"  (Δ MRR {r['MRR']-base['MRR']:+.3f})" if r is not base else ""
        print(f"{r['mode']:<8} {r['P@1']:>7.3f} {r['P@3']:>7.3f} "
              f"{r['P@5']:>7.3f} {r['MRR']:>7.3f}{d}")

    if len(results) == 1 and results[0]["failed"]:
        f = results[0]["failed"]
        print(f"\n=== {len(f)} memories not in top-5 (mode={results[0]['mode']}) ===")
        for name, rank, query in f[:10]:
            print(f"  rank={rank:3d}  {name}")
            print(f"           query: {query}")


if __name__ == "__main__":
    main()
