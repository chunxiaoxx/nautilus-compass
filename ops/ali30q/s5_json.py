#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5 result.json 加载器 · F-011

v5 items/_s5 有一批未解的 git 冲突标记(实测 50 份)。json.loads 整份失败后
discrimination_jaccard / collect_for_quickscreen 当「无读数」跳过 → 甲方三门
缺腿(UNVERIFIED)或快筛 c2 假阴。

判分层只读、不改 v5 题面(turf: codesense-a-fix 禁写)。冲突时取 HEAD 侧
(当前工作区意图),再 json.loads;仍失败则返回 None。
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, TypeVar


def strip_conflict_markers(text: str, prefer: str = "head") -> str:
    """prefer='head' 保留 <<<<<<< 与 ======= 之间; 'theirs' 保留后半。"""
    if "<<<<<<<" not in text:
        return text
    keep_head = prefer != "theirs"
    out: list[str] = []
    mode = "keep"  # keep | head | theirs
    for line in text.splitlines(True):
        if line.startswith("<<<<<<<"):
            mode = "head"
            continue
        if line.startswith("======="):
            mode = "theirs"
            continue
        if line.startswith(">>>>>>>"):
            mode = "keep"
            continue
        if mode == "keep" or (mode == "head" and keep_head) or (mode == "theirs" and not keep_head):
            out.append(line)
    return "".join(out)


T = TypeVar("T")
BATCH_GAP_S = 3600.0


def latest_batch(
    items: list[tuple[float, T]], gap: float = BATCH_GAP_S
) -> list[tuple[float, T]]:
    """mtime 聚簇:间隔 >gap 开新批,只返回最新批(F-009 / F-012)。

    空输入原样返回。跨目录应先合并再调用一次,勿按目录各取最新再拼接
    (否则两 scratch 会把两批拼成假「最新」)。
    """
    if not items:
        return items
    files = sorted(items, key=lambda x: x[0])
    batches: list[list[tuple[float, T]]] = []
    cur: list[tuple[float, T]] = [files[0]]
    for prev, nxt in zip(files, files[1:]):
        if nxt[0] - prev[0] > gap:
            batches.append(cur)
            cur = []
        cur.append(nxt)
    batches.append(cur)
    return batches[-1]


def load_s5_json(path: Path) -> dict[str, Any] | None:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass
    if "<<<<<<<" not in text:
        return None
    for prefer in ("head", "theirs"):
        try:
            data = json.loads(strip_conflict_markers(text, prefer=prefer))
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict):
            return data
    return None
