# -*- coding: utf-8 -*-
"""
core PostToolUse hook - 验越界 + 防冒充

从 compass/ops/compass_post_tool.py 复制 + 改 ALLOWED_ROOT
"""
import json
import re
import sys
from pathlib import Path

ALLOWED_ROOT = Path(r"C:\Users\chunx\Projects\nautilus-core")

# 禁止其他 dialog 写 OUTBOUND(只允许本 dialog)
FORBIDDEN = re.compile(r"_OUTBOUND_FROM_(?!CORE_)", re.IGNORECASE)

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        return 0
    tool = data.get("tool_name", "")
    if tool not in ("Write", "Edit", "MultiEdit"):
        return 0
    tool_input = data.get("tool_input", {}) or {}
    file_path = tool_input.get("file_path", "")
    if not file_path:
        return 0
    p = Path(file_path).resolve()
    if not str(p).startswith(str(ALLOWED_ROOT)):
        sys.stderr.write("[core-post] FAIL: 越界写 " + file_path + chr(92) + "n")
        return 1
    name = Path(file_path).name
    if FORBIDDEN.search(name):
        sys.stderr.write("[core-post] FAIL: 禁止冒充 pattern=" + FORBIDDEN.pattern + chr(92) + "n")
        return 1
    return 0

if __name__ == "__main__":
    sys.exit(main())
