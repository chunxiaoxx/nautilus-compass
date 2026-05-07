#!/usr/bin/env python3
"""Baselines for drift detection (provide non-self comparison points).

Runs 3 baselines + nautilus-compass v0.7.1 on the SAME 100-prompt test set:
  1. Random           — sanity floor
  2. Keyword match    — explicit deviation keyword list (rm -rf, hardcode, etc.)
  3. Zero-shot SBERT  — generic embedding cosine to keyword list
                        (no anchor curation, no top-k tuning)
  4. nautilus-compass v0.7.1 (full)

Goal: show our +X AUC over generic baselines is real,
      not just an artifact of using BGE.
"""
from __future__ import annotations

import json
import os
import random
import sys
from pathlib import Path

os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

PLUGIN = Path.home() / ".claude" / "plugins" / "nautilus-compass"
sys.path.insert(0, str(PLUGIN))
import daemon as zmd  # noqa: E402

sys.path.insert(0, str(PLUGIN / "tests"))
from eval_drift import ALIGNED, DEVIATION  # noqa


# Generic deviation keywords (no curation; just lexical patterns)
DEVIATION_KEYWORDS = [
    "rm -rf", "kill -9", "force push", "git push --force",
    "skip", "ignore", "硬编码", "hardcode",
    "不验证", "不测试", "不查",
    "假装", "我猜", "应该是", "反正",
    "drop table", "truncate", "delete from",
    "taskkill", "kill all", "全杀掉",
    "v1 不行", "重写", "rewrite",
    "宝贝", "你都对",
]


def auc_score(pos_scores: list[float], neg_scores: list[float]) -> float:
    """Mann-Whitney U statistic / (n1*n2)."""
    wins = ties = 0
    for p in pos_scores:
        for n in neg_scores:
            if p > n: wins += 1
            elif p == n: ties += 1
    return (wins + 0.5 * ties) / max(1, len(pos_scores) * len(neg_scores))


# Baseline 1: random
def baseline_random():
    random.seed(42)
    pos = [random.random() for _ in ALIGNED]
    neg = [random.random() for _ in DEVIATION]
    return auc_score(pos, neg)


# Baseline 2: keyword match
# Score = -count(deviation_keywords in prompt). Higher = more aligned.
def baseline_keyword():
    def score(p):
        return -sum(1 for kw in DEVIATION_KEYWORDS if kw.lower() in p.lower())
    pos = [score(p) for p in ALIGNED]
    neg = [score(p) for p in DEVIATION]
    return auc_score(pos, neg)


# Baseline 3: zero-shot SBERT against keyword list (no anchor curation)
def baseline_zeroshot():
    emb = zmd.get_embedder()
    kw_emb = [emb.encode(kw) for kw in DEVIATION_KEYWORDS]
    def score(p):
        e = emb.encode(p)
        # higher = more similar to deviation keyword list (so we negate for "aligned" sense)
        sims = [zmd.cosine(e, k) for k in kw_emb]
        return -max(sims)   # if very similar to a deviation keyword, score very negative
    pos = [score(p) for p in ALIGNED]
    neg = [score(p) for p in DEVIATION]
    return auc_score(pos, neg)


# Baseline 4: nautilus-compass v0.7.1 full (pos + neg anchors, top-3 mean)
def system_full():
    emb = zmd.get_embedder()
    anchors = json.loads(zmd.ANCHORS_PATH.read_text(encoding="utf-8"))
    def _txt(x): return x if isinstance(x, str) else x.get("text", "")
    pos_emb = [emb.encode(_txt(a)) for a in anchors["positive_anchors"]]
    neg_emb = [emb.encode(_txt(a)) for a in anchors["negative_anchors"]]
    K = 3
    def score(p):
        e = emb.encode(p)
        ps = sorted((zmd.cosine(e, pe) for pe in pos_emb), reverse=True)[:K]
        ns = sorted((zmd.cosine(e, ne) for ne in neg_emb), reverse=True)[:K]
        return sum(ps)/K - sum(ns)/K
    pos = [score(p) for p in ALIGNED]
    neg = [score(p) for p in DEVIATION]
    return auc_score(pos, neg)


def main():
    print(f"=== Drift detection baselines (n=100: {len(ALIGNED)} aligned + {len(DEVIATION)} deviation) ===")
    print(f"embedder: {zmd.EMBEDDER_MODEL}")
    print()

    print("Running 4 systems...")
    results = {}
    print("  1. random ...")
    results["random"] = baseline_random()
    print("  2. keyword match ...")
    results["keyword"] = baseline_keyword()
    print("  3. zero-shot SBERT (deviation keywords as anchors, no curation) ...")
    results["zeroshot"] = baseline_zeroshot()
    print("  4. nautilus-compass v0.7.1 (curated 25+35 anchors, top-3 mean) ...")
    results["full"] = system_full()

    print(f"\n=== Baselines comparison (Table 1 candidate) ===")
    print(f"  System                                ROC AUC      Δ from random")
    print(f"  ----------------------------------    -------    ----------------")
    base = results["random"]
    for name, label in [("random",   "random (floor)               "),
                        ("keyword",  "keyword match (no embedder)  "),
                        ("zeroshot", "zero-shot SBERT to keywords  "),
                        ("full",     "nautilus-compass v0.7.1 (full)    ")]:
        a = results[name]
        d = a - base
        print(f"  {label}        {a:.4f}     {d:+.4f}")
    print()
    print(f"Headline: nautilus-compass AUC {results['full']:.4f} vs zero-shot SBERT {results['zeroshot']:.4f}")
    print(f"           uplift over zero-shot: {results['full'] - results['zeroshot']:+.4f}")
    print(f"           (this is the value of curated anchors, controlling for embedder)")


if __name__ == "__main__":
    main()
