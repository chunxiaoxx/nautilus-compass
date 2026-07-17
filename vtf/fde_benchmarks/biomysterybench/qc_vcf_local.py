#!/usr/bin/env python3
"""VCF 题的**本地** QC(供应商侧,批量用)· 纯 Windows 原生,零网络。

用本地 ClinVar SQLite(build_local_clinvar.py 建)对交付 zip 里每个变异查致病性+基因+病名,
坐实唯一性(恰好一个 Pathogenic),毫秒级。P4 批产 500 题的唯一性 QC 就靠它,
不再受 Entrez 限速(实测本地 vs 远程 ~13000× 提速,结果一致)。

远程 solve_problem.py 仍保留 = 模拟买方 bmb-infer 走公共工具证难度;本地 QC = 供应商快速验唯一。

用法: python qc_vcf_local.py _P1_out/data/bmb_vendor_000001.zip
"""
from __future__ import annotations

import argparse
import time
import zipfile
from pathlib import Path

import local_clinvar

PATHOGENIC = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", type=Path)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip_path) as z:
        txt = z.read("variants.vcf").decode()
    variants = [ln.split("\t") for ln in txt.splitlines() if ln and not ln.startswith("#")]

    t0 = time.time()
    hits = []
    for f in variants:
        chrom, pos, ref, alt = f[0], int(f[1]), f[3], f[4]
        cls, gene, cond = local_clinvar.lookup(chrom, pos, ref, alt)
        if cls in PATHOGENIC:
            hits.append((gene, cls, cond, f"chr{chrom}:{pos}"))
    dt = (time.time() - t0) * 1000

    print(f"{len(variants)} 变异 · 本地查 {dt:.1f}ms · 致病命中 {len(hits)} "
          f"(唯一=1:{'✅' if len(hits)==1 else '🔴'})")
    for g, cls, cond, loc in hits:
        print(f"  → {g} | {cls} | {cond} @ {loc}")
    if len(hits) == 1:
        g, _, cond, _ = hits[0]
        print(f"本地 QC 答案:{g}|{cond[0] if cond else '?'}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
