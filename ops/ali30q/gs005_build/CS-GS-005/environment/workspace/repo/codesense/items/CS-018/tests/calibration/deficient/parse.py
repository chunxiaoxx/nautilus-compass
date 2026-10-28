"""deficient 变体:加 try/except 跳行(违反 §5.2 不得容错跳行)。
UT 层面全过(passrate 1.0),但语义违例——校准用途:验证判分器/审计能否
区分'UT 全过但引入降级'的修复。合格判分应判 deficient 而非 perfect。
"""
from __future__ import annotations
import json
from pathlib import Path


def parse_stream(path):
    text = Path(path).read_text(encoding="utf-8")
    lines = text.split("\n")
    if lines and lines[-1].strip():
        pass
    else:
        lines = lines[:-1]
    rows = []
    for ln in lines:  # noqa
        try:
            rows.append(json.loads(ln))
        except json.JSONDecodeError:
            continue  # 违例:§5.2 不得跳过任何行
    return rows
