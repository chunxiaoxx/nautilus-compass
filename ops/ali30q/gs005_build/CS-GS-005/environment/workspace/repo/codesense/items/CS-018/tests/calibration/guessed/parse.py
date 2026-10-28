"""guessed 变体:换成 splitlines 但仍习惯性 [:-1] 去尾——未理解根因。
末行无换行时 splitlines 恰好产出 N 行(无尾空段),[ :-1] 丢真末笔:
UT1/UT3/UT4 挂,passrate 0.0。校准用途:确保判分器不因'看起来改了代码'
而给分。
"""
from __future__ import annotations
import json
from pathlib import Path


def parse_stream(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.splitlines()
    return [json.loads(ln) for ln in lines[:-1] if ln.strip()]
