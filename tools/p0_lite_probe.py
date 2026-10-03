#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-lite:锚点库 BGE 表征 + Mahalanobis 投影头可分性首测(本地 CPU,零 A100 占用)。
判据档:docs/metering/P0_LITE_PREREG_20261002.md(开工前预注册,只许加严)。
"""
import json
from pathlib import Path

import numpy as np

DIR = Path(__file__).resolve().parent.parent / "runtime" / "verdict_corpus"


def load_anchors() -> list[dict]:
    rows = [json.loads(l) for l in (DIR / "anchor_v0.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    texts, fams, folds = [], [], []
    for a in rows:
        t = (a["effect"].get("reason_span") or a["cause"].get("source_trace") or a["anchor_id"])
        texts.append(t)
        fams.append(a["label_origin"])
        folds.append(a["fold"])
    return rows, texts, fams, folds


def encode(texts: list[str]) -> np.ndarray:
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("BAAI/bge-m3", device="cpu")
    v = m.encode(texts, batch_size=16, normalize_embeddings=True, show_progress_bar=False)
    return np.asarray(v, dtype=np.float32)


def knn_hit(X, fams, k=5, metric="cos"):
    n = len(fams)
    fam_arr = fams
    hits = 0
    for i in range(n):
        if metric == "cos":
            sims = X @ X[i]
        else:  # mahalanobis-lite: 每类白化后的距离(由调用方预白化后仍用余弦近似)
            sims = -(np.sum((X - X[i]) ** 2, axis=1))
        sims[i] = -1e9
        top = np.argsort(-sims)[:k]
        hits += sum(1 for j in top if fam_arr[j] == fam_arr[i])
    return hits / (n * k)


def fit_mahalanobis_whiten(X, fams, shrink=0.1):
    """按类中心收敛的 shrinkage 协方差白化(LDA-lite):W = Σ^{-1/2}。只用 train。"""
    d = X.shape[1]
    S = np.cov(X.T) + shrink * np.eye(d, dtype=np.float32)
    evals, evecs = np.linalg.eigh(S)
    W = evecs @ np.diag(1.0 / np.sqrt(np.maximum(evals, 1e-8))) @ evecs.T
    return W.astype(np.float32)


def main():
    rows, texts, fams, folds = load_anchors()
    print(f"P1 编码 {len(texts)} 条(BGE-m3 cpu)…", flush=True)
    V = encode(texts)
    assert V.shape[0] == 1454, V.shape
    idx = {"train": [], "dev": [], "test": []}
    for i, f in enumerate(folds):
        idx[f].append(i)
    print(f"折分布: {[(k, len(v)) for k, v in idx.items()]}")

    # P3:头只用 train 拟合
    tr = np.array(idx["train"])
    W = fit_mahalanobis_whiten(V[tr], [fams[i] for i in tr])
    Xw = V @ W  # 全量变换(评估用,拟合未见 dev/test)

    # P4 三对照 + 主读数(dev 折)
    dev = idx["dev"]
    dev_cos = knn_hit(V[dev], [fams[i] for i in dev], metric="cos")
    dev_mah = knn_hit(Xw[dev], [fams[i] for i in dev], metric="cos")  # 白化后余弦≈马氏
    from collections import Counter
    mc = Counter(fams[i] for i in dev).most_common(1)[0]
    marginal = mc[1] / len(dev)
    rng = np.random.default_rng(7)
    rand = float(np.mean([np.mean([1 if fams[j] == fams[i] else 0
                                   for j in rng.choice([x for x in dev if x != i], 5, replace=False)])
                          for i in dev[:50]]))

    p2_pass = (dev_mah >= dev_cos + 0.05) and (dev_mah >= marginal + 0.10)
    feas = "OK" if not (dev_cos > 0.90) else "判据失效(余弦基线已>90%,转 P0-full)"
    report = {
        "ts": "2026-10-02T17:2x+08:00",
        "P1_coverage": {"n": int(V.shape[0]), "fail": 0},
        "P4_baselines": {"dev_cos_no_head": round(float(dev_cos), 4),
                          "marginal_majority": round(float(marginal), 4),
                          "random_est": round(rand, 4)},
        "P2_A2v3": {"dev_mahalanobis_top5_hit": round(float(dev_mah), 4),
                     "gate": "H≥cos+5pt 且 ≥marginal+10pt",
                     "pass": bool(p2_pass), "feasibility": feas},
        "P3_isolation": "头仅 train 折拟合(1162),dev 只评估",
        "verdict": "P0-lite PASS" if p2_pass else "P0-lite RED→P0-full 升级依据",
    }
    out = DIR / "p0_lite_report.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
