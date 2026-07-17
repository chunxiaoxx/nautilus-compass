#!/usr/bin/env python3
"""BioMysteryBench 盲解验证器(蛋白序列→基因/疾病模板)· BLAST 工具链。

模拟买方 bmb-infer:**只读交付的 data/<ID>.zip**,对每条序列跑 blastp(vs SwissProt)
识别蛋白身份,找出唯一的溶酶体酶 → 基因 + 疾病。坐实:可解 + 唯一 + ≥10 工具。

用法: python solve_seq_problem.py _SEQ_out/data/bmb_vendor_000003.zip
"""
from __future__ import annotations

import argparse
import time
import zipfile
from pathlib import Path

from Bio import SeqIO
from Bio.Blast import NCBIWWW, NCBIXML

# 溶酶体(贮积病)酶的判别关键词 vs 胞质管家蛋白
LYSO_KW = ("hexosaminidase", "lysosom", "cerebrosidase", "iduronidase", "sulfatase",
           "alpha-glucosidase", "acid alpha", "galactosidase", "arylsulfatase", "sphingomyelin")
# 已知蛋白名 → (基因, 疾病)· 供盲解输出
LYSO_MAP = {"hexosaminidase": ("HEXA", "Tay-Sachs disease")}

_CALLS = {"blast": 0}


def blastp_top(seq, sleep=1.0, retries=3):
    """blastp vs SwissProt,对瞬时网络/SSL 抖动重试(远程 BLAST 常见)。"""
    _CALLS["blast"] += 1
    last = None
    for attempt in range(retries):
        try:
            r = NCBIWWW.qblast("blastp", "swissprot", seq, hitlist_size=1, expect=1e-10)
            rec = NCBIXML.read(r)
            time.sleep(sleep)
            if not rec.alignments:
                return None, None
            al = rec.alignments[0]
            ident = al.hsps[0].identities / al.hsps[0].align_length if al.hsps else 0
            return al.hit_def, ident
        except Exception as e:  # noqa: BLE001 — 瞬时 SSL/网络抖动,退避重试
            last = e
            print(f"    (重试 {attempt+1}/{retries}: {type(e).__name__})")
            time.sleep(5 * (attempt + 1))
    raise last


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("zip_path", type=Path)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip_path) as z:
        fasta = z.read("sequences.fasta").decode()
    recs = list(SeqIO.parse(io_str(fasta), "fasta"))
    print(f"读到 {len(recs)} 条序列,逐条 blastp(vs SwissProt)...\n")

    t0 = time.time()
    lyso_hits = []
    for i, rec in enumerate(recs, 1):
        defn, ident = blastp_top(str(rec.seq))
        is_lyso = defn and any(k in defn.lower() for k in LYSO_KW)
        flag = "  <-- 溶酶体酶" if is_lyso else ""
        print(f"[{i:2}/{len(recs)}] {rec.id} | id≈{ident:.0%} | {(defn or '?')[:70]}{flag}")
        if is_lyso:
            lyso_hits.append({"label": rec.id, "defline": defn})

    elapsed = time.time() - t0
    print(f"\n=== 盲解结果 ===")
    print(f"工具调用:blastp {_CALLS['blast']} 次(买方门 ≥10:{'✅' if _CALLS['blast'] >= 10 else '🔴'})")
    print(f"墙钟(供应商已知解法):{elapsed:.0f}s")
    print(f"溶酶体酶命中数:{len(lyso_hits)}(唯一性要求 =1:{'✅' if len(lyso_hits) == 1 else '🔴'})")

    if len(lyso_hits) == 1:
        defn = lyso_hits[0]["defline"].lower()
        gene, disease = next(((g, d) for k, (g, d) in LYSO_MAP.items() if k in defn), ("?", "?"))
        print(f"  → {lyso_hits[0]['label']}: {lyso_hits[0]['defline'][:70]}")
        print(f"\n盲解答案:{gene}|{disease}")
        return 0
    print("\n🔴 溶酶体酶不唯一或未识别,题不合格")
    return 1


def io_str(s):
    import io
    return io.StringIO(s)


if __name__ == "__main__":
    raise SystemExit(main())
