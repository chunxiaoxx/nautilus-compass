#!/usr/bin/env python3
"""nautilus-compass v2.5.1 · PostToolUse hook · J1 fact_status 写入门补丁。

问题: fact_status 门只装在 daemon 读出+session_writer,而 9/9 后实际新记忆
      大多由会话 agent 直接 Write 进 ~/.claude/projects/<proj>/memory/——
      该路径无人检查,9/9-9/14 三项目 30 次写入零覆盖(RSI 环 #1 复算
      J1 FAIL 实证:hooks/scripts 对 fact_status 零落点)。
解法: Write/Edit 落盘后立刻补验:目标是 memory/*.md 且 frontmatter 缺
      fact_status → 注入 `fact_status: inferred`(保守默认;写者知道得更准
      时应显式写 measured/heard,后续可改)。
边界(fail-open 契约):
  · 任何异常静默退出,绝不挡写、绝不破坏文件、退出码恒 0
  · MEMORY.md 索引、无 frontmatter 的文件、非 memory 目录一律不动
  · 只在缺字段时追加一行,不改既有内容(注入逻辑与
    session_writer._inject_frontmatter_field 同构,但保行尾字节保真)
接线: ~/.claude/settings.json · PostToolUse · matcher "Write|Edit"
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

MEM_ROOT = Path.home() / ".claude" / "projects"


def _has_fact_status(fm_text: str) -> bool:
    """frontmatter 文本里是否已有 fact_status 字段(不论值是否合法——已有就不动,
    值的修正归写者,本 hook 不猜值不覆盖)。"""
    return any(line.strip().startswith("fact_status:")
               for line in fm_text.split("\n"))


def stamp(path_str: str, mem_root: Path = MEM_ROOT) -> bool:
    """对刚写入的 memory 文件补 fact_status。返回是否发生了修改。"""
    try:
        p = Path(path_str)
        if p.suffix != ".md" or p.name == "MEMORY.md":
            return False
        if p.parent.name != "memory" or mem_root not in p.parents:
            return False
        with open(p, "r", encoding="utf-8", newline="") as f:
            text = f.read()
    except Exception:
        return False
    if not text.startswith("---"):
        return False
    end = text.find("\n---", 3)
    if end <= 0:
        return False
    if _has_fact_status(text[:end]):
        return False
    # 注入必须保持原行尾(newline="" 读写保真;注入行跟随文件既有行尾风格)
    nl = "\r\n" if "\r\n" in text[: end] else "\n"
    if nl == "\n":
        new_text = text[:end] + f"\nfact_status: inferred" + text[end:]
    else:
        # _inject_frontmatter_field 只产 \n;CRLF 文件手工插入,保持字节保真
        new_text = text[:end] + "\r\nfact_status: inferred" + text[end:]
    try:
        with open(p, "w", encoding="utf-8", newline="") as f:
            f.write(new_text)
        return True
    except Exception:
        return False


def main() -> int:
    try:
        payload = json.loads(sys.stdin.read() or "{}")
    except Exception:
        return 0
    if payload.get("tool_name") not in ("Write", "Edit"):
        return 0
    fp = (payload.get("tool_input") or {}).get("file_path") or ""
    if fp:
        stamp(fp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
