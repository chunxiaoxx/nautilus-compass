"""齿轮⑤ 深 consolidation:36k cycle-auto 日记碎片 → 挑信号做胶囊 + 噪声归档(可逆)。

实测(2026-06-22):~/.claude/projects 下 36032 个 cycle-*-auto 目录(93%)·95% 单文件·
内容 = V5 daemon 每 cycle 的 think:/learn:/evolve: 独白·抽样 learn: 字段全空 = 噪声非教训。
把它们整体做成胶囊会淹没真信号(反精炼)→ 正解:挑 learn: 非空的少数蒸馏·其余归档。

设计 = 纯解析/分类(TDD)+ 注入 I/O(walk/write/archive)。归档 = mv 可逆·非删。
跑在 T4(碎片所在)。dry-run 先看信号/噪声比再动。
"""
from __future__ import annotations

import re
from typing import Callable, Iterable

# learn: 内容 >= 此长度才算捕获了真教训(空/极短 = 噪声决心书)。
MIN_LEARN_LEN = 15


def parse_cycle_md(text: str) -> dict:
    """解析 cycle ingest .md:frontmatter(tags/drift/agent_id)+ body(think/learn/evolve)。"""
    fm: dict = {}
    body = text
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.DOTALL)
    if m:
        fm_raw, body = m.group(1), m.group(2)
        for line in fm_raw.splitlines():
            if ":" in line:
                k, _, v = line.partition(":")
                fm[k.strip()] = v.strip()

    def _field(name: str) -> str:
        # body 里 "name: ...." 直到下一个 think/learn/evolve 或结尾。
        # 用 [ \t]*(不含换行)防空字段吞掉下一行内容(实测 bug:learn 空时误吃 evolve)。
        mm = re.search(rf"(?m)^{name}:[ \t]*(.*?)(?=\n(?:think|learn|evolve|<tool_call)|\Z)",
                       body, re.DOTALL)
        return mm.group(1).strip() if mm else ""

    return {
        "think": _field("think"),
        "learn": _field("learn"),
        "evolve": _field("evolve"),
        "tags": fm.get("tags", ""),
        "drift": fm.get("drift", ""),
        "agent_id": fm.get("agent_id", ""),
    }


def classify(parsed: dict) -> str:
    """valuable = learn: 非空且有实质内容;否则 noise(空决心书)。"""
    learn = (parsed.get("learn") or "").strip()
    if len(learn) >= MIN_LEARN_LEN:
        return "valuable"
    return "noise"


def lesson_to_capsule_body(parsed: dict, source: str) -> dict:
    """有价值的 learn: → capsule body(对齐 memory_bridge 的 ingest body 契约)。"""
    learn = parsed["learn"].strip()
    agent = parsed.get("agent_id") or "v5-daemon"
    return {
        "content": learn,
        "name": "capsule:cycle-lesson"[:80],
        "description": f"[cycle-distilled src={source} agent={agent}] {learn}"[:200],
        "project": "distilled-capsules",
        "tags": ["fleet-capsule", "cycle-distilled", f"source:{agent}"],
        "drift": "green",
    }


def consolidate_cycles(
    cycle_entries: Iterable[tuple],
    write_capsule_fn: Callable[[dict], object],
    archive_fn: Callable[[str], object],
    *,
    dry_run: bool = False,
) -> dict:
    """cycle_entries = [(dir_path, md_text), ...]。

    valuable → write_capsule_fn(body)·noise → archive_fn(dir_path)(dry_run 时都不调)。
    返回 {"valuable","noise","distilled","archived"}。
    """
    valuable = noise = distilled = archived = 0
    for dir_path, md_text in cycle_entries:
        parsed = parse_cycle_md(md_text or "")
        if classify(parsed) == "valuable":
            valuable += 1
            if not dry_run:
                write_capsule_fn(lesson_to_capsule_body(parsed, dir_path))
                distilled += 1
        else:
            noise += 1
            if not dry_run:
                archive_fn(dir_path)
                archived += 1
    return {"valuable": valuable, "noise": noise, "distilled": distilled, "archived": archived}
