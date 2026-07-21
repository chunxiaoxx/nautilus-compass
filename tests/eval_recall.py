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

Run:
  python tests/eval_recall.py --mode flat
  python tests/eval_recall.py --mode all     # run every mode, print delta table
  python tests/eval_recall.py --out .cache/eval_recall.json
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import shlex
import statistics
import sys
import time
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
OUT_VERSION = "1.0"
MAX_FAILED_TO_KEEP = 20
MRR_DELTA_MIN = 0.005
MRR_NEGATIVE_DELTA_MIN = -0.0005


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

    Faithful to production:
    - poi uses apply_poi_boost_value (same value-path boost snapshot uses)
    - tier uses apply_tier_weight (lifecycle additive bonus)
    - gemini only affects upstream query, so its rerank == tier
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
    n = len(mems)
    if n == 0:
        return {
            "mode": mode,
            "n": 0,
            "P@1": 0.0,
            "P@3": 0.0,
            "P@5": 0.0,
            "MRR": 0.0,
            "failed": [],
        }

    p1 = p3 = p5 = 0
    rrs = []
    failed = []

    for i in range(n):
        q = query_emb[i]
        # all candidates as (cosine, entry) carrying impact/tier + idx
        entries = [
            (cosine(q, body_emb[j]), {"idx": j, "impact": mems[j]["impact"], "tier": mems[j]["tier"]})
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
        "mode": mode,
        "n": n,
        "P@1": p1 / n,
        "P@3": p3 / n,
        "P@5": p5 / n,
        "MRR": statistics.mean(rrs),
        "failed": failed,
    }


def build_recommendations(mode_results, n_memories: int, n_impact: int, n_nonworking: int):
    """Turn eval outputs into next-step suggestions for the next tuning loop."""
    recs = []

    if n_memories == 0:
        recs.append({
            "priority": "critical",
            "action": "seed_memory_corpus",
            "reason": "No memories loaded from project memory dir.",
            "next_step": "Add session memories and rerun recall evaluation.",
            "evidence": {"n_memories": n_memories},
        })
        return recs

    if n_impact == 0:
        recs.append({
            "priority": "high",
            "action": "bootstrap_poi_signals",
            "reason": "No memory has cumulative_impact != 0; PoI boost is mathematically inactive.",
            "next_step": (
                "Run PoI outcome ingestion/reconciliation to mint cumulative_impact "
                "before claiming lifecycle value."
            ),
            "evidence": {"cumulative_impact_nonzero": n_impact, "total_memories": n_memories},
        })

    if n_nonworking == 0:
        recs.append({
            "priority": "medium",
            "action": "bootstrap_tier_signals",
            "reason": "All memories are working tier; tier bonus cannot re-rank on tier gaps.",
            "next_step": (
                "Review tier promotion cadence and gate conditions (promote_after / reinforce path), "
                "then rerun this benchmark."
            ),
            "evidence": {"tier_nonworking": n_nonworking, "total_memories": n_memories},
        })

    flat = next((r for r in mode_results if r["mode"] == "flat"), None)
    d1 = next((r for r in mode_results if r["mode"] == "poi"), None)
    d2 = next((r for r in mode_results if r["mode"] == "tier"), None)
    d3 = next((r for r in mode_results if r["mode"] == "gemini"), None)

    d1_delta = d1.get("delta_vs_flat", {}).get("MRR", 0.0) if d1 and flat else None
    d2_delta = d2.get("delta_vs_flat", {}).get("MRR", 0.0) if d2 and flat else None

    if d1_delta is not None and d1_delta < MRR_NEGATIVE_DELTA_MIN:
        recs.append({
            "priority": "medium",
            "action": "retune_lifecycle_weight",
            "reason": "D1(MRR delta) is negative after signal injection; PoI weight may be over-applied or too sparse.",
            "next_step": "Run paired ablation and reduce/gate PoI boost until positive on held-out smoke corpus.",
            "evidence": {"d1_delta_mrr": d1_delta},
        })
    elif d1_delta is not None and d1_delta < MRR_DELTA_MIN:
        recs.append({
            "priority": "low",
            "action": "freeze_or_rewrite",
            "reason": "D1(MRR delta) < +0.005; PoI change is not measurable on this corpus.",
            "next_step": "Prefer external signal experiments for D1 before changing default deployment flags.",
            "evidence": {"d1_delta_mrr": d1_delta},
        })

    if d2_delta is not None and d2_delta < MRR_NEGATIVE_DELTA_MIN:
        recs.append({
            "priority": "medium",
            "action": "retune_lifecycle_weight",
            "reason": "D2(MRR delta) is negative after tier signal injection; tier bonus may be too blunt for sparse signals.",
            "next_step": "Gate tier weighting behind minimum support or reduce additive bonus before default use.",
            "evidence": {"d2_delta_mrr": d2_delta},
        })
    elif d2_delta is not None and d2_delta < MRR_DELTA_MIN:
        recs.append({
            "priority": "low",
            "action": "freeze_or_rewrite",
            "reason": "D2(MRR delta) < +0.005; tier gain is not measurable on this corpus.",
            "next_step": "Keep tier weighting behind explicit flag until tier signal is sufficiently populated.",
            "evidence": {"d2_delta_mrr": d2_delta},
        })

    if d3 and d3.get("delta_vs_flat", {}).get("MRR", 0.0) < MRR_DELTA_MIN:
        recs.append({
            "priority": "medium",
            "action": "reassess_gemini_rewrite",
            "reason": "D3(MRR delta) < +0.005; Gemini rewrite not producing measurable uplift here.",
            "next_step": "Keep Gemini off by default or gate it with tighter token budget control.",
            "evidence": {"d3_delta_mrr": d3["delta_vs_flat"]["MRR"]},
        })

    if not recs:
        recs.append({
            "priority": "low",
            "action": "continue",
            "reason": "No blocking signal; keep collecting 2–3 runs before architecture change.",
            "next_step": "Re-run with the same plan and compare trend stability.",
            "evidence": {"modes": [r["mode"] for r in mode_results]},
        })

    return recs


def _normalize_failed(failed):
    return [
        {"name": name, "rank": rank, "query": query}
        for name, rank, query in failed[:MAX_FAILED_TO_KEEP]
    ]


def add_delta_vs_flat(results):
    """Attach delta_vs_flat to each mode result."""
    mode_index = {r["mode"]: i for i, r in enumerate(results)}
    base = results[mode_index["flat"]] if "flat" in mode_index and results[mode_index["flat"]]["n"] else None

    for r in results:
        if base and r["n"]:
            r["delta_vs_flat"] = {
                "P@1": r["P@1"] - base["P@1"],
                "P@3": r["P@3"] - base["P@3"],
                "P@5": r["P@5"] - base["P@5"],
                "MRR": r["MRR"] - base["MRR"],
            }
        else:
            r["delta_vs_flat"] = None
    return results


def build_recall_payload(args, mems, results, n_impact, n_nonworking, out_path, embedder=None, command=None):
    """Build JSON payload for downstream tuning scripts."""
    mode_order = [r["mode"] for r in results]
    return {
        "version": OUT_VERSION,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "meta": {
            "payload_version": OUT_VERSION,
            "mode": args.mode,
            "modes": mode_order,
            "n_memories": len(mems),
            "n_impact": n_impact,
            "n_tier_nonworking": n_nonworking,
            "embedder": embedder,
            "command": command,
            "out_file": str(out_path) if out_path else None,
            "has_embeddings": bool(mems),
        },
        "results": [
            {**r, "failed": _normalize_failed(r["failed"])}
            for r in results
        ],
        "result_summary": {
            r["mode"]: {
                "p1": r["P@1"],
                "p3": r["P@3"],
                "p5": r["P@5"],
                "mrr": r["MRR"],
                "delta_mrr_vs_flat": r["delta_vs_flat"]["MRR"] if r.get("delta_vs_flat") else None,
            }
            for r in results
        },
        "recommendations": build_recommendations(results, len(mems), n_impact, n_nonworking),
    }


def _print_table(results):
    print("\n=== retrieval quality (leave-one-out) ===")
    print(f"{'mode':<8} {'P@1':>7} {'P@3':>7} {'P@5':>7} {'MRR':>7}")
    base = results[0]
    for r in results:
        d = f"  (Δ MRR {r['MRR']-base['MRR']:+.3f})" if r is not base else ""
        print(f"{r['mode']:<8} {r['P@1']:>7.3f} {r['P@3']:>7.3f} "
              f"{r['P@5']:>7.3f} {r['MRR']:>7.3f}{d}")


def _print_failures(res):
    if len(res) == 1 and res[0]["failed"]:
        f = res[0]["failed"]
        print(f"\n=== {len(f)} memories not in top-5 (mode={res[0]['mode']}) ===")
        for name, rank, query in f[:10]:
            print(f"  rank={rank:3d}  {name}")
            print(f"           query: {query}")


def _write_artifact(payload, args_out, cache_dir):
    if args_out:
        out_path = Path(args_out)
    else:
        out_path = cache_dir / f"eval_recall_{int(time.time())}.json"

    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload["meta"]["out_file"] = str(out_path)
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)
        print(f"\n=== artifact ===\n  {out_path}")
        return out_path
    except Exception:
        print("\n=== artifact ===")
        print("  skipped (failed to write JSON artifact)")
        payload["meta"]["out_file"] = None
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--mode",
        default="flat",
        choices=list(MODES) + ["all"],
        help="recall mode (flat/poi/tier/gemini) or 'all' for delta table",
    )
    ap.add_argument("--out", help="optional JSON artifact path (default .cache/eval_recall_<timestamp>.json)")
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
                  f"({time.time()-t0:.1f}s)" + ("" if n_changed else " → Gemini off · D3 == D2"))
        else:
            qe = query_emb_flat
        results.append(evaluate(mems, body_emb, qe, mode, zmd.cosine))

    add_delta_vs_flat(results)

    _print_table(results)
    _print_failures(results)

    payload = build_recall_payload(
        args=args,
        mems=mems,
        results=results,
        n_impact=n_impact,
        n_nonworking=n_nonworking,
        out_path=None,
        embedder=zmd.EMBEDDER_MODEL,
        command=f"{shlex.quote(sys.executable)} {shlex.join(sys.argv)}",
    )

    out_path = _write_artifact(payload, args.out, zmd.CACHE_DIR)
    payload["meta"]["out_file"] = str(out_path) if out_path else None


if __name__ == "__main__":
    main()
