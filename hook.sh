#!/bin/bash
# V5 Memory Plugin · UserPromptSubmit hook entry
# 跑 recall.py 注入 memory 时间戳分组到 system prompt
# 失败静默 · 不阻塞用户
#
# R444 bash 层节流前置(2026-10-09): 实测 recall.py 进程链 3.8-4.8s/条消息。
# 🔴修正案(第二版): 第一版 fast path 用 grep/sed/tr/cut 工具链,MSYS 每外部进程
# 被 Defender 扫描 ~1.5s,8 进程=12s——比 python 还慢。本版窗内路径**零外部进程**
# (纯 bash 内建+EPOCHSECONDS),窗外才落 ts 起 python。

PLUGIN_DIR="$(dirname "$(readlink -f "$0")")"

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

# ---- T5 bash fast path v2(零外部进程版) ----
THROTTLE_MIN="${COMPASS_THROTTLE_MIN:-10}"
INPUT="$(cat 2>/dev/null)"
SKIP_PYTHON=0

if [ "$THROTTLE_MIN" != "0" ] && [ "$THROTTLE_MIN" -gt 0 ] 2>/dev/null; then
    # session_id 提取: 纯参数扩展(免 grep/sed 进程)
    SID="${INPUT#*\"session_id\"}"
    SID="${SID#*:}"
    SID="${SID#*\"}"
    SID="${SID%%\"*}"
    if [ -n "$SID" ]; then
        # sanitize: bash 4+ 替换 + 截断(免 tr/cut)
        SAFE="${SID//[^a-zA-Z0-9_-]/_}"
        SAFE="${SAFE:0:80}"
        [ -z "$SAFE" ] && SAFE="anon"
        STATE="$HOME/.cache/compass_hook_throttle/${SAFE}.json"
        NOW="${EPOCHSECONDS:-$(date +%s)}"   # bash 5 内建优先,免 date 进程
        LAST=""
        if [ -f "$STATE" ]; then
            IFS= read -r LINE < "$STATE" 2>/dev/null
            LAST="${LINE#*\"ts\"}"
            LAST="${LAST#*:}"
            LAST="${LAST%%,*}"
            LAST="${LAST//[^0-9.]/}"
        fi
        if [ -n "$LAST" ]; then
            AGE=$((NOW - ${LAST%.*}))
            REMAIN=$((THROTTLE_MIN * 60 - AGE))
            if [ "$REMAIN" -gt 0 ] 2>/dev/null; then
                echo "[nautilus-compass-recall 节流 · window ${THROTTLE_MIN}min · ${REMAIN}s remain · bash fast path]"
                exit 0   # 零 python · 零外部进程
            fi
        fi
        SKIP_PYTHON=0   # 窗外: 交 python 全量(python 侧 throttle_check 落 ts,同格式)
    fi
fi

# 跑 recall.py · stdout → Claude Code 注入 system prompt
if [ "$SKIP_PYTHON" = "0" ]; then
    if [ -n "$INPUT" ]; then
        printf '%s' "$INPUT" | "$PYTHON" "$PLUGIN_DIR/recall.py" 2>/dev/null
    else
        "$PYTHON" "$PLUGIN_DIR/recall.py" 2>/dev/null
    fi
fi

exit 0
