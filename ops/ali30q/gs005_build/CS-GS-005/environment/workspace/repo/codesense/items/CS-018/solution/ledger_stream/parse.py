"""ledger_stream.parse — 对账流水逐笔解析与聚合(金标修复版)。"""
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

    修复:上游生成器末行不带换行符时,末笔仍须入账(§3 逐笔全量)。
    split 后若末段非空即为一笔有效交易,不得无条件丢弃。
    """
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines and lines[-1].strip():
        pass  # 末段是有效末笔,保留
    else:
        lines = lines[:-1]  # 末段为空(文件以换行结尾),丢弃空段
    rows = [json.loads(ln) for ln in lines if ln.strip()]
    return rows


def ingest_daily(path: str | Path) -> LedgerStats:
    """日终对账:解析全量流水并聚合。"""
    rows = parse_stream(path)
    stats = LedgerStats(
        tx_count=len(rows),
        sum_amount=sum(int(r["amount"]) for r in rows),
    )
    return stats
