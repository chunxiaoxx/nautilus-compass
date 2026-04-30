#!/usr/bin/env python3
"""mem0 vs nautilus-compass head-to-head on LongMemEval-S subset 12.

For fair retrieval-only comparison:
  - Add each haystack session as a separate mem0 memory
  - Query mem0.search(question, top_k=5)
  - Check if any returned memory's metadata.session_id matches truth

OpenAI key 通过 OPENAI_API_KEY env var · 不写文件不写 hist
Run: OPENAI_API_KEY=$(cat /c/tmp/.openai_key) python tests/eval_mem0_headhead.py
"""
from __future__ import annotations

import json
import os
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

DATASET_PATH = Path(os.environ.get(
    "ZMM_LONGMEMEVAL_PATH", "C:/tmp/longmemeval_subset12.json",
))


def session_to_text(session, max_chars=600):
    parts = [f"[{t.get('role', '?')}] {t.get('content', '')}" for t in session]
    return "\n".join(parts)[:max_chars]


def main():
    # Vertex AI 走 service account JSON · OpenAI key 不需要 (mem0 v2 LLM 字段需 dummy 占位)
    os.environ.setdefault("OPENAI_API_KEY", "dummy-not-used-because-infer-False")
    from mem0 import Memory

    # 用 Vertex AI embedder · service account JSON · 无 OpenAI 依赖
    # infer=False 跳过 LLM extraction · 直接存原文 · 公平比 retrieval
    # 读 GOOGLE_APPLICATION_CREDENTIALS env var (Google SDK 标准) · 用户自己 export
    GCP_JSON = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    if not GCP_JSON or not Path(GCP_JSON).exists():
        print("❌ Set GOOGLE_APPLICATION_CREDENTIALS=/path/to/your-gcp-sa.json", file=sys.stderr)
        print("   See: https://cloud.google.com/docs/authentication/application-default-credentials", file=sys.stderr)
        sys.exit(1)
    config = {
        "vector_store": {
            "provider": "qdrant",
            "config": {
                "path": "C:/tmp/mem0_qdrant_eval",
                "on_disk": True,
                "embedding_model_dims": 768,   # 必填 · 跟 Vertex text-embedding-005 同
            },
        },
        # 不配 LLM · 因为 infer=False 不调 LLM · mem0 v2 仍可能要求 llm 字段 · 给个 dummy
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

    print(f"loading mem0 ...")
    t0 = time.time()
    m = Memory.from_config(config)
    print(f"mem0 ready: {time.time()-t0:.1f}s")

    data = json.load(open(DATASET_PATH, encoding="utf-8"))
    print(f"questions: {len(data)}")

    p1 = p3 = p5 = 0
    rrs = []
    type_metrics = defaultdict(lambda: {"n": 0, "p1": 0, "p5": 0, "rrs": []})

    t_start = time.time()
    for i, q in enumerate(data):
        question = q["question"]
        truth_ids = set(q["answer_session_ids"])
        sess_ids = q["haystack_session_ids"]
        sessions = q["haystack_sessions"]

        # Reset mem0 for each question (else mem0 mixes haystacks)
        try:
            m.reset()
        except Exception:
            pass

        # Add each session as separate mem0 memory · use raw text · skip extraction
        # mem0 1.x API: m.add(messages, user_id, metadata)
        user_id = f"q_{q['question_id']}"
        for sid, sess in zip(sess_ids, sessions):
            try:
                m.add(
                    messages=session_to_text(sess, max_chars=600),
                    user_id=user_id,
                    metadata={"session_id": sid},
                    infer=False,   # skip LLM extraction · 直接存原文 · 公平比 retrieval
                )
            except Exception as e:
                print(f"  add fail (skipping): {e}", file=sys.stderr)

        # Search top-5 (mem0 v2 API: filters={'user_id': ...})
        try:
            results = m.search(query=question, filters={"user_id": user_id}, limit=5)
        except TypeError:
            # fallback: 老 API
            try:
                results = m.search(query=question, user_id=user_id, limit=5)
            except Exception as e:
                print(f"  search fail: {e}", file=sys.stderr)
                results = []
        except Exception as e:
            print(f"  search fail: {e}", file=sys.stderr)
            results = []

        # Find rank of truth
        rank = None
        if isinstance(results, dict):
            results = results.get("results", [])
        for r, hit in enumerate(results, 1):
            sid = (hit.get("metadata") or {}).get("session_id")
            if sid in truth_ids:
                rank = r
                break

        qt = q["question_type"]
        type_metrics[qt]["n"] += 1
        if rank:
            rrs.append(1.0 / rank)
            type_metrics[qt]["rrs"].append(1.0 / rank)
            if rank <= 1: p1 += 1; type_metrics[qt]["p1"] += 1
            if rank <= 3: p3 += 1
            if rank <= 5: p5 += 1; type_metrics[qt]["p5"] += 1
        else:
            rrs.append(0.0)

        elapsed = time.time() - t_start
        eta = elapsed / (i + 1) * (len(data) - i - 1)
        print(f"  [{i+1}/{len(data)}] {qt:30s} rank={rank or 'N/A':>4}  "
              f"({len(sessions)} sess · {elapsed:.0f}s · ETA {eta:.0f}s · MRR {statistics.mean(rrs):.3f})", flush=True)

    n = len(data)
    print(f"\n=== mem0 (text-embedding-3-small · raw session add · n={n}) ===")
    print(f"  P@1={p1}/{n}={p1/n:.3f}  P@5={p5}/{n}={p5/n:.3f}  MRR={statistics.mean(rrs):.3f}")
    print(f"\n=== by question_type ===")
    for qt in sorted(type_metrics):
        m_ = type_metrics[qt]
        if m_["n"] == 0: continue
        print(f"  {qt:30s} n={m_['n']:2d}  P@1={m_['p1']/m_['n']:.2f}  P@5={m_['p5']/m_['n']:.2f}  "
              f"MRR={statistics.mean(m_['rrs']) if m_['rrs'] else 0:.3f}")

    summary = {
        "system": "mem0 (text-embedding-3-small)",
        "n": n, "P@1": p1/n, "P@5": p5/n, "MRR": statistics.mean(rrs),
        "by_type": {qt: {"P@5": m_["p5"]/m_["n"], "MRR": statistics.mean(m_["rrs"]) if m_["rrs"] else 0, "n": m_["n"]}
                    for qt, m_ in type_metrics.items()},
    }
    out = Path.home() / ".claude/plugins/nautilus-compass/.cache/eval_mem0_headhead.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    print(f"\n  详细: {out}")


if __name__ == "__main__":
    main()
