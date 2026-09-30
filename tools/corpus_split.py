#!/usr/bin/env python3
"""corpus_split · P2 训练集防泄漏分层切分。

关键设计:
  · 按 qid 分组切分(同题不同 run——d12/d14 同 question_id——必须同折,
    否则 test 泄漏:模型在 train 见过同题不同配置的判定)
  · 分层因子:label(pass/fail/insufficient_evidence)× 源族(bc1/t3/f15/rejudge/lme)
  · seed=20260930 固定;比例 80/10/10
  · 产出 runtime/verdict_corpus/{split_train,split_dev,split_test}.jsonl + 统计
"""
from __future__ import annotations

import json
import random
import sys
from collections import Counter, defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "runtime" / "verdict_corpus" / "train_set_v0.jsonl"
OUT = ROOT / "runtime" / "verdict_corpus"
SEED = 20260930
RATIOS = (0.8, 0.1, 0.1)


def qid_of(sid: str) -> str:
    """样本 id → 泄漏防护键:同题不同 run 归并。

    rejudge-<qid> 与 lme-d12-...-<qid>/lme-d14-...-<qid> 同题 → 裸 qid;
    其余族样本 id 本身唯一。
    """
    if sid.startswith("rejudge-"):
        return sid[len("rejudge-"):]
    if sid.startswith("lme-"):
        return sid.rsplit("-", 1)[-1]
    return sid


def main():
    rows = [json.loads(l) for l in SRC.read_text(encoding="utf-8").splitlines() if l.strip()]
    groups = defaultdict(list)
    for r in rows:
        groups[qid_of(r["id"])].append(r)
    # 分层桶:key=(族, label) → 组列表;组内同折
    fam = lambda sid: sid.split("-", 1)[0]
    buckets = defaultdict(list)
    for qid, rs in groups.items():
        f = fam(rs[0]["id"])
        lab = rs[0]["truth_label"]
        buckets[(f, lab)].append(qid)
    rng = random.Random(SEED)
    splits = {"train": [], "dev": [], "test": []}
    for key in sorted(buckets):
        qids = sorted(buckets[key])
        rng.shuffle(qids)
        n = len(qids)
        n_tr = round(n * RATIOS[0])
        n_dev = round(n * RATIOS[1])
        for q in qids[:n_tr]:
            splits["train"] += groups[q]
        for q in qids[n_tr:n_tr + n_dev]:
            splits["dev"] += groups[q]
        for q in qids[n_tr + n_dev:]:
            splits["test"] += groups[q]
    for name, rows2 in splits.items():
        rng.shuffle(rows2)
        (OUT / f"split_{name}.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows2) + "\n",
            encoding="utf-8")
    stats = {name: {"n": len(rs),
                    "labels": dict(Counter(r["truth_label"] for r in rs)),
                    "fams": dict(Counter(fam(r["id"]) for r in rs))}
             for name, rs in splits.items()}
    (OUT / "split_stats.json").write_text(
        json.dumps({"seed": SEED, "ratios": RATIOS, "per_split": stats},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(stats, ensure_ascii=False, indent=1))
    # 泄漏自检:qid 跨折 = 必须为 0
    seen = {}
    leaks = 0
    for name, rs in splits.items():
        for r in rs:
            k = qid_of(r["id"])
            if k in seen and seen[k] != name:
                leaks += 1
            seen[k] = name
    print(f"[leak-check] 跨折 qid = {leaks} ({'PASS' if leaks == 0 else 'FAIL'})")


if __name__ == "__main__":
    main()
