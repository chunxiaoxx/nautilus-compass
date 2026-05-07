#!/bin/bash
# V5 Memory Plugin · UserPromptSubmit hook entry
# 跑 recall.py 注入 memory 时间戳分组到 system prompt
# 失败静默 · 不阻塞用户

PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"

# Python 优先级: 1) v5 venv (最佳 · 后续 v0.2 用 BGE) 2) 系统 python3
PYTHON=""
if [ -x "/c/Users/chunx/Projects/nautilus-v5/.venv/Scripts/python.exe" ]; then
    PYTHON="/c/Users/chunx/Projects/nautilus-v5/.venv/Scripts/python.exe"
elif command -v python3 &> /dev/null; then
    PYTHON="python3"
elif command -v python &> /dev/null; then
    PYTHON="python"
fi

if [ -z "$PYTHON" ]; then
    exit 0   # 没 python · 静默退出 · 不阻塞
fi

# 跑 recall.py · stdout → Claude Code 注入 system prompt
"$PYTHON" "$PLUGIN_DIR/recall.py" 2>/dev/null

exit 0
