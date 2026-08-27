#!/usr/bin/env python3
"""mem0 vs nautilus-compass head-to-head on LOCOMO-10 (retrieval layer).

Mirrors eval_locomo.py (compass side) and eval_mem0_headhead.py (mem0 side):
  - per conversation: reset mem0, add each session (2000-char cap, same as
    compass side session_text), search each qa question top-5
  - truth = qa.evidence "D<n>:<turn>" -> session_<n>
  - rank = first position of any truth session in top-5
  - metrics: P@1 / P@5 / MRR overall + per category
    (1 single-hop · 2 multi-hop · 3 temporal · 4 open-domain · 5 adversarial)

Fairness: mem0 infer=False (no LLM extraction, raw session text), vertexai
text-embedding-005 + qdrant local — identical embedder/store as the
LongMemEval-S head-to-head.

Run (cloud, from repo root):
  GOOGLE_APPLICATION_CREDENTIALS=~/secrets/gcp-vertex-sa.json \
  ZMM_LOCOMO_PATH=.cache/locomo10.json python3 tests/eval_mem0_locomo.py
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

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

LOCOMO_PATH = Path(os.environ.get("ZMM_LOCOMO_PATH", ".cache/locomo10.json"))
MAX_SESS_CHARS = 2000  # same cap as compass-side eval_locomo.session_text

CATEGORY = {"1": "single-hop", "2": "multi-hop", "3": "temporal",
            "4": "open-domain", "5": "adversarial"}


def session_text(turns, max_chars=MAX_SESS_CHARS):
    parts = [f"[{t.get('speaker', '?')}] {t.get('text', '')}" for t in turns]
    return "\n".join(parts)[:max_chars]


def evidence_sessions(qa):
    out = set()
    for e in qa.get("evidence", []):
        m = re.match(r"D(\d+):", e)
        if m:
            out.add(f"session_{int(m.group(1))}")
    return out


def main():
    GCP_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not GCP_JSON or not Path(GCP_JSON).exists():
        print("❌ Set GOOGLE_APPLICATION_CREDENTIALS", file=sys.stderr)
        sys.exit(1)
    os.environ.setdefault("OPENAI_API_KEY", "dummy-not-used-because-infer-False")
    from mem0 import Memory

    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": os.environ.get("ZMM_MEM0_QDRANT_PATH", "/tmp/mem0_qdrant_locomo"),
                "on_disk": True,
                "embedding_model_dims": 768,
            },
        },
        "llm": {"provider": "gemini", "config": {"model": "gemini-1.5-flash", "api_key": "dummy"}},
        "embedder": {
            "provider": "vertexai",
            "config": {
                "model": "text-embedding-005",
                "vertex_credentials_json": GCP_JSON,
                "embedding_dims": 768,
            },
        },
    }
    t0 = time.time()
    m = Memory.from_config(config)
    print(f"mem0 ready: {time.time()-t0:.1f}s")

    data = json.load(open(LOCOMO_PATH, encoding="utf-8"))
    print(f"LOCOMO-10: {len(data)} conversations")

    rows = []
    p1 = p5 = 0
    rrs = []
    t_start = time.time()
    for ci, conv in enumerate(data):
        try:
            m.reset()
        except Exception:
            pass
        c = conv["conversation"]
        sess_names = sorted([k for k in c if k.startswith("session_") and not k.endswith("date_time")],
                            key=lambda s: int(s.split("_")[1]))
        user_id = f"conv_{ci}"
        for name in sess_names:
            try:
                m.add(messages=session_text(c[name]), user_id=user_id,
                      metadata={"session_id": name}, infer=False)
            except Exception as e:
                print(f"  add fail: {e}", file=sys.stderr)

        for qi, qa in enumerate(conv["qa"]):
            try:
                results = m.search(query=qa["question"], filters={"user_id": user_id}, limit=5)
            except TypeError:
                results = m.search(query=qa["question"], user_id=user_id, limit=5)
            except Exception as e:
                print(f"  search fail: {e}", file=sys.stderr)
                results = []
            if isinstance(results, dict):
                results = results.get("results", [])
            truth = evidence_sessions(qa)
            rank = None
            top5 = []
            for r, hit in enumerate(results[:5], 1):
                sid = (hit.get("metadata") or {}).get("session_id")
                top5.append(sid)
                if sid in truth and rank is None:
                    rank = r
            rows.append({
                "conv": ci, "category": str(qa["category"]),
                "question": qa["question"][:120], "rank": rank,
                "top5": top5, "truth": sorted(truth),
            })
            if rank:
                rrs.append(1.0 / rank)
                if rank == 1: p1 += 1
                if rank <= 5: p5 += 1
            else:
                rrs.append(0.0)
        n_done = len(rows)
        elapsed = time.time() - t_start
        print(f"  conv {ci+1}/{len(data)} · {n_done} qs · {elapsed:.0f}s · MRR {statistics.mean(rrs):.3f}", flush=True)

    n = len(rows)
    print(f"\n=== mem0 LOCOMO-10 retrieval (n={n}) ===")
    print(f"  P@1={p1/n:.3f}  P@5={p5/n:.3f}  MRR={statistics.mean(rrs):.3f}")
    by = defaultdict(list)
    for r in rows:
        by[CATEGORY.get(r["category"], r["category"])].append(r)
    for cat in sorted(by):
        rs = by[cat]
        cp1 = sum(1 for r in rs if r["rank"] == 1) / len(rs)
        cp5 = sum(1 for r in rs if r["rank"] and r["rank"] <= 5) / len(rs)
        print(f"  {cat:14s} n={len(rs):4d}  P@1={cp1:.2f}  P@5={cp5:.2f}")

    out = Path.home() / ".claude/plugins/nautilus-compass/.cache/eval_mem0_locomo.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump({"n": n, "P@1": p1 / n, "P@5": p5 / n, "MRR": statistics.mean(rrs),
                   "by_category": {c: {"n": len(rs),
                                       "P@1": sum(1 for r in rs if r["rank"] == 1) / len(rs),
                                       "P@5": sum(1 for r in rs if r["rank"] and r["rank"] <= 5) / len(rs)}
                                   for c, rs in by.items()}}, f, ensure_ascii=False, indent=2)
    rows_path = out.with_name(out.stem + "_rows.jsonl")
    with open(rows_path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"\n  summary: {out} · rows: {rows_path}")


if __name__ == "__main__":
    main()
