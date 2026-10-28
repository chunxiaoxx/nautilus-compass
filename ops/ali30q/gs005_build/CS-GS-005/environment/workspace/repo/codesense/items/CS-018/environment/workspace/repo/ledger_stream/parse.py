"""ledger_stream.parse — 对账流水逐笔解析与聚合(坑版:末笔丢失待修)。"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass
class LedgerStats:
    tx_count: int = 0
    sum_amount: int = 0  # 单位:分


def parse_stream(path: str | Path) -> list[dict]:
    """逐笔解析 jsonl 流水文件,返回全量交易列表。

    业务规则 §3:逐笔全量入账,末笔与首笔同等义务。
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    rows = [json.loads(ln) for ln in lines[:-1] if ln.strip()]
    return rows


def ingest_daily(path: str | Path) -> LedgerStats:
    """日终对账:解析全量流水并聚合。"""
    rows = parse_stream(path)
    stats = LedgerStats(
        tx_count=len(rows),
        sum_amount=sum(int(r["amount"]) for r in rows),
    )
    return stats
