#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P0-full 评估:hit@5 + 二项检验(判据档 v2:F2/F3)。

输入:p0_full_extract.py 产出的 {effect,cause}_{tag}.npy(双主干各一组)。
随机期望=5/(n-1);p 值=单侧二项检验(正态近似,n=1454 下与精确二项一致到 1e-4)。
用法:python3 p0_full_eval.py --dir p0_full_out --tags q14 turbo
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

K = 5


def hit_at_k(Q: np.ndarray, C: np.ndarray, k: int = K) -> tuple[int, int]:
    sims = Q @ C.T
    np.fill_diagonal(sims, -1e9)  # 排除自身位置(池=全量含自己,检索对象是其余 1453)
    top = np.argsort(-sims, axis=1)[:, :k]
    hits = int((top == np.arange(len(Q))[:, None]).any(axis=1).sum())
    return hits, len(Q)


def binom_p(k: int, n: int, p0: float) -> float:
    """单侧 P(X≥k),正态近似(带连续校正)。"""
    if k / n <= p0:
        return 1.0
    z = ((k - 0.5) / n - p0) / math.sqrt(p0 * (1 - p0) / n)
    return 0.5 * (1 - math.erf(z / math.sqrt(2)))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="p0_full_out")
    ap.add_argument("--tags", nargs="+", default=["q14", "turbo"])
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    d = Path(a.dir)
    random_exp = K / (1454 - 1)
    report = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "random_expectation":
              round(random_exp, 5), "gate_F2": 0.05, "backbones": {}}
    any_pass = False
    for tag in a.tags:
        try:
            E = np.load(d / f"effect_{tag}.npy")
            C = np.load(d / f"cause_{tag}.npy")
        except FileNotFoundError:
            print(f"[skip] {tag} 工件缺(未提取?)")
            continue
        En = E / np.linalg.norm(E, axis=1, keepdims=True)
        Cn = C / np.linalg.norm(C, axis=1, keepdims=True)
        hits, n = hit_at_k(En, Cn)
        p = binom_p(hits, n, random_exp)
        passed = hits / n >= 0.05 and p < 0.01
        any_pass = any_pass or passed
        report["backbones"][tag] = {
            "hit@5": round(hits / n, 4), "hits": hits, "n": n,
            "binom_p": f"{p:.2e}", "F2_pass": passed}
        print(f"[{tag}] hit@5={hits}/{n}={hits/n:.4f} p={p:.2e} "
              f"{'PASS' if passed else 'RED'}")
    report["F2_any_pass"] = any_pass
    report["verdict"] = (
        "F2 过→P0 检索头路线成立,进 P1(锚点+逆跳步)" if any_pass else
        "F2 双双红→语义桥需监督训练(P2 C/V 闭环 LoRA 建桥);根因排查=先文本质量后模型")
    (d / "p0_full_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"[save] {d / 'p0_full_report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
