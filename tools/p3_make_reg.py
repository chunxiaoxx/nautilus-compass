#!/usr/bin/env python3
"""P3 S4 前置 · REG-100 回归集冻结件(一次性生成,生成后只读)。

设计档 §五:从冻结 split_test(149)分层抽样 100(pass/fail/insufficient_evidence
按 78/70/1 比例→52/47/1),种子 20261003,sha16 落档。
**永久冻结、永不入训、修改即事故**(设计档 §五原文)。
用法:python tools/p3_make_reg.py  (已存在则拒跑,防覆盖)
"""
from __future__ import annotations

import hashlib
import json
import random
import sys
from collections import defaultdict
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent
CORPUS = ROOT / "runtime" / "verdict_corpus"
OUT = CORPUS / "reg100.jsonl"
MANIFEST = CORPUS / "reg100_manifest.json"
SEED = 20261003
N_TARGET = 100
N_TOTAL = 149


def sha16(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def main() -> int:
    if OUT.exists() or MANIFEST.exists():
        print("[REFUSE] reg100 已存在——永久冻结件不许覆盖(修改即事故);"
              f"现件 sha16={sha16(OUT) if OUT.exists() else '?'}")
        return 1
    rows = [json.loads(l) for l in
            (CORPUS / "split_test.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    assert len(rows) == N_TOTAL, f"test 应 149 条,实 {len(rows)}——冻结基线漂移,停"
    by_label = defaultdict(list)
    for r in rows:
        by_label[r["truth_label"]].append(r)
    quota = {lab: round(N_TARGET * len(rs) / N_TOTAL) for lab, rs in by_label.items()}
    quota["pass"], quota["fail"] = 52, 47  # 52+47+1=100,消除整数凑整歧义,写死并落档
    rng = random.Random(SEED)
    picked = []
    for lab, k in quota.items():
        pool = sorted(by_label[lab], key=lambda r: r["content_hash"])
        picked.extend(rng.sample(pool, k))
    picked.sort(key=lambda r: r["content_hash"])
    OUT.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in picked) + "\n",
                   encoding="utf-8")
    manifest = {
        "frozen_at": "2026-10-03", "seed": SEED, "n": len(picked),
        "quota": quota, "source": "split_test.jsonl(149,sha16=" + sha16(CORPUS / "split_test.jsonl") + ")",
        "reg100_sha16": sha16(OUT),
        "frozen_terms": "永久冻结、永不入训、修改即事故(P3 设计档 §五;判据只许更严)",
        "usage": "G1 零退化门:挑战者与冠军在 REG-100 逐条对照,correct→incorrect 翻转必须=0",
    }
    MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(manifest, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
