#!/usr/bin/env python3
"""把 clinvar.vcf.gz 建成本地 SQLite 索引库(纯 Windows 原生,消 Entrez 限速/延迟)。

解析 ClinVar VCF 的 INFO(CLNSIG 致病性 / GENEINFO 基因 / CLNDN 疾病),
建 SQLite 表 + (chrom,pos) 索引 → 坐标查从远程 ~0.4s(限速 3-10/s)降到本地 <1ms。

用法:
  python build_local_clinvar.py _localdb/clinvar_grch38.vcf.gz   # 建库
  # 之后 local_clinvar.lookup(chrom,pos) 即时返回致病性+基因+病名
"""
from __future__ import annotations

import sqlite3
import sys
import time
from pathlib import Path

from Bio import bgzf

DB_PATH = Path(__file__).parent / "_localdb" / "clinvar_grch38.sqlite"


def parse_info(info: str) -> dict:
    d = {}
    for kv in info.split(";"):
        if "=" in kv:
            k, v = kv.split("=", 1)
            d[k] = v
    return d


def build(vcf_gz: Path, db_path: Path = DB_PATH) -> None:
    if db_path.exists():
        db_path.unlink()
    con = sqlite3.connect(db_path)
    con.execute("""CREATE TABLE clinvar(
        chrom TEXT, pos INTEGER, ref TEXT, alt TEXT,
        clnsig TEXT, gene TEXT, condition TEXT)""")
    t0 = time.time()
    batch, n, kept = [], 0, 0
    with bgzf.open(str(vcf_gz), "rt") as f:
        for line in f:
            if line.startswith("#"):
                continue
            n += 1
            c = line.rstrip("\n").split("\t")
            if len(c) < 8:
                continue
            chrom, pos, _id, ref, alt = c[0], c[1], c[2], c[3], c[4]
            info = parse_info(c[7])
            clnsig = info.get("CLNSIG", "").replace("_", " ")
            gene = info.get("GENEINFO", "").split(":")[0] if info.get("GENEINFO") else ""
            cond = info.get("CLNDN", "").replace("_", " ")
            if not clnsig:
                continue
            batch.append((chrom, int(pos) if pos.isdigit() else 0, ref, alt, clnsig, gene, cond))
            kept += 1
            if len(batch) >= 20000:
                con.executemany("INSERT INTO clinvar VALUES(?,?,?,?,?,?,?)", batch)
                batch.clear()
    if batch:
        con.executemany("INSERT INTO clinvar VALUES(?,?,?,?,?,?,?)", batch)
    con.execute("CREATE INDEX idx_pos ON clinvar(chrom, pos)")
    con.commit()
    con.close()
    print(f"✅ 建库完成:{kept} 条(总 {n})· {time.time()-t0:.0f}s · {db_path.name} "
          f"({db_path.stat().st_size/1e6:.0f}MB)")


if __name__ == "__main__":
    build(Path(sys.argv[1] if len(sys.argv) > 1 else DB_PATH.parent / "clinvar_grch38.vcf.gz"))
