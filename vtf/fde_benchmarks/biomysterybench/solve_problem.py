#!/usr/bin/env python3
"""BioMysteryBench 盲解验证器(VCF→变异临床意义模板)· P1 雏形。

模拟买方 bmb-infer:**只读交付的 data/<ID>.zip**(绝不读 answer_key/manifest),
用允许域名的真实工具链独立把题解出来,并坐实:
  · 答案能从匿名 VCF 推出(VEP 注释 + ClinVar 查库)
  · 唯一(恰好一个 Pathogenic/Likely pathogenic 变异)
  · 记录工具调用次数(买方要 ≥10)

这也是建题管线的 QC 环节:每道产出题交付前跑一遍,确认唯一 + 难度 + 无泄露。

用法:
  python solve_problem.py _P1_out/data/bmb_vendor_000001.zip
"""
from __future__ import annotations

import argparse
import io
import json
import time
import urllib.request
import zipfile
from pathlib import Path

from Bio import Entrez

Entrez.email = "fde-compass@nautilus.social"

PATHOGENIC = {"Pathogenic", "Likely pathogenic", "Pathogenic/Likely pathogenic"}

_CALLS = {"vep": 0, "clinvar": 0}


def parse_vcf(text: str):
    variants, build = [], None
    for line in text.splitlines():
        if line.startswith("##reference"):
            build = line.split("=", 1)[1].strip()
        if line.startswith("#") or not line.strip():
            continue
        f = line.split("\t")
        variants.append({"chrom": f[0], "pos": int(f[1]), "ref": f[3], "alt": f[4]})
    return variants, build


def vep_annotate(chrom, pos, alt, sleep=0.2):
    """Ensembl VEP REST:坐标 → 基因 + 最重后果。"""
    _CALLS["vep"] += 1
    url = (f"https://rest.ensembl.org/vep/human/region/"
           f"{chrom}:{pos}-{pos}:1/{alt}?content-type=application/json")
    req = urllib.request.Request(url, headers={"User-Agent": "compass-bmb-solver"})
    v = json.load(urllib.request.urlopen(req, timeout=30))[0]
    time.sleep(sleep)
    genes = sorted({t.get("gene_symbol") for t in v.get("transcript_consequences", [])
                    if t.get("gene_symbol")})
    return genes, v.get("most_severe_consequence")


def clinvar_lookup(chrom, pos, sleep=0.4):
    """NCBI ClinVar:GRCh38 坐标 → 临床分类 + 疾病。"""
    _CALLS["clinvar"] += 1
    h = Entrez.esearch(db="clinvar", term=f"{chrom}[chr] AND {pos}[chrpos38]")
    ids = Entrez.read(h)["IdList"]
    time.sleep(sleep)
    if not ids:
        return None, []
    h = Entrez.esummary(db="clinvar", id=ids[0], retmode="json")
    res = json.load(h)["result"][ids[0]]
    time.sleep(sleep)
    gc = res.get("germline_classification", {})
    conds = [t.get("trait_name") for t in gc.get("trait_set", [])
             if t.get("trait_name") not in (None, "not specified", "not provided")]
    return gc.get("description"), conds


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", type=Path)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip_path) as z:
        vcf_text = z.read("variants.vcf").decode()

    variants, build = parse_vcf(vcf_text)
    print(f"读到 {len(variants)} 个变异 · 参考基因组 = {build}\n")
    assert build == "GRCh38", "solver 需先从头确定 build"

    t0 = time.time()
    hits = []
    for i, v in enumerate(variants, 1):
        genes, cons = vep_annotate(v["chrom"], v["pos"], v["alt"])
        cls, conds = clinvar_lookup(v["chrom"], v["pos"])
        flag = "  <-- PATHOGENIC" if cls in PATHOGENIC else ""
        print(f"[{i:2}/{len(variants)}] chr{v['chrom']}:{v['pos']} {v['ref']}>{v['alt']} "
              f"| {','.join(genes) or '?':10} | {cons or '?':22} | ClinVar={cls or '-':22}{flag}")
        if cls in PATHOGENIC:
            hits.append({"gene": ",".join(genes), "consequence": cons,
                         "cls": cls, "conditions": conds,
                         "locus": f"chr{v['chrom']}:{v['pos']}"})

    elapsed = time.time() - t0
    total_calls = _CALLS["vep"] + _CALLS["clinvar"]
    print(f"\n=== 盲解结果 ===")
    print(f"工具调用:VEP {_CALLS['vep']} + ClinVar {_CALLS['clinvar']} = {total_calls} 次"
          f"(买方门 ≥10:{'✅' if total_calls >= 10 else '🔴'})")
    print(f"墙钟(供应商已知解法,非模型摸索时间):{elapsed:.0f}s")
    print(f"致病变异命中数:{len(hits)}(唯一性要求 =1:{'✅' if len(hits) == 1 else '🔴'})")
    for h in hits:
        print(f"  → {h['gene']} | {h['consequence']} | {h['cls']} | {h['conditions']} @ {h['locus']}")

    if len(hits) == 1:
        g = hits[0]["gene"]
        cond = hits[0]["conditions"][0] if hits[0]["conditions"] else "?"
        print(f"\n盲解答案:{g}|{cond}")
        return 0
    print("\n🔴 答案不唯一或无解,题不合格")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
