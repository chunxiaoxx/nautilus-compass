"""本地 ClinVar SQLite 查询(替 Entrez 远程,<1ms)。build_local_clinvar.py 先建库。"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "_localdb" / "clinvar_grch38.sqlite"
_con = None


def _conn():
    global _con
    if _con is None:
        if not DB_PATH.exists():
            raise FileNotFoundError(f"本地 ClinVar 库不存在:{DB_PATH}(先跑 build_local_clinvar.py)")
        _con = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    return _con


def lookup(chrom: str, pos: int, ref: str | None = None, alt: str | None = None):
    """返回 (clnsig, gene, condition)。给 ref/alt 则精确匹配,否则取该坐标首条。查不到返回 (None,None,[])。"""
    cur = _conn().execute(
        "SELECT ref,alt,clnsig,gene,condition FROM clinvar WHERE chrom=? AND pos=?",
        (str(chrom), int(pos)))
    rows = cur.fetchall()
    if not rows:
        return None, None, []
    if ref is not None and alt is not None:
        for r, a, cls, g, cond in rows:
            if r == ref and a == alt:
                return cls, g, [c for c in cond.split("|") if c not in ("not specified", "not provided", "")]
    r, a, cls, g, cond = rows[0]
    return cls, g, [c for c in cond.split("|") if c not in ("not specified", "not provided", "")]
