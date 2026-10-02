#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A2-v4:锚点级果→因检索(判据档 docs/metering/A2V4_ANCHOR_RETRIEVAL_PREREG_20261002.md)。"""
import json
from pathlib import Path

import numpy as np

DIR = Path(__file__).resolve().parent.parent / "runtime" / "verdict_corpus"


def load():
    rows = [json.loads(l) for l in (DIR / "anchor_v0.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    eff = [a["effect"].get("reason_span") or a["anchor_id"] for a in rows]
    cau = [" ".join(filter(None, [
        " ".join(a["cause"]["criteria_refs"] or []),
        str(a["cause"].get("source_trace") or ""),
        str(a["cause"].get("artifact_ref") or "")])) for a in rows]
    ids = [a["anchor_id"] for a in rows]
    folds = [a["fold"] for a in rows]
    return rows, eff, cau, ids, folds


def encode(texts):
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-m3", device="cpu")
    return np.asarray(m.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False), dtype=np.float32)


def hit_at_k(Q, C, k=5):
    """Q[i] 的 top-k 检索是否命中 C 中同 i。"""
    sims = Q @ C.T
    hits = 0
    for i in range(len(Q)):
        sims[i, i] = -1e9
        top = np.argsort(-sims[i])[:k]
        hits += 1 if i in top else 0
    return hits / len(Q)


def main():
    rows, eff, cau, ids, folds = load()
    print(f"R1 编码两侧 {len(eff)}+{len(cau)} …", flush=True)
    E = encode(eff)
    C = encode(cau)
    assert E.shape[0] == C.shape[0] == 1454

    true_hit = hit_at_k(E, C, k=5)
    rng = np.random.default_rng(7)
    perm = rng.permutation(len(E))
    shuffled_hit = hit_at_k(E[perm], C, k=5)  # 他人 reason 查 → 语义桥地板
    random_hit = 5 / (len(E) - 1)              # 随机 top-5 期望

    gate = max(5 * random_hit, 3 * shuffled_hit)
    r2_pass = true_hit >= gate
    report = {
        "ts": "2026-10-02T18:0x+08:00",
        "R1_coverage": "2908/2908 编码零失败",
        "R2_causal_bridge": {
            "hit@5_true_query": round(float(true_hit), 4),
            "shuffled_query_floor": round(float(shuffled_hit), 4),
            "random_expectation": round(float(random_hit), 5),
            "gate": round(float(gate), 4),
            "pass": bool(r2_pass)},
        "verdict": "因果桥在 BGE 层存在→P1 可用轻量件" if r2_pass else "桥不在 BGE 层→P0-full(14B)升级依据坐实",
        "note": "R3 头增量副读数略(lite 头已证天花板,本次直连检索即为轻量件上限形态)",
    }
    (DIR / "a2v4_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
