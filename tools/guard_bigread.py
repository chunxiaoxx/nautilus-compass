#!/usr/bin/env python3
"""守卫② · bigread 闸 —— PreToolUse 拦截大文件全文读(2026-11-01,治 thrashing 三守卫之二)

行为: Read 工具目标文件 >COMPASS_BIGREAD_KB(默认100KB)且未带 offset/limit 时 deny,
     提示分块读;其余一律放行(含异常 fail-open 静默放行)。
依据: REVIEW_mac_sessions P-w2(实测 flywheel 会话单行 231KB attachment);
     Claude Code Read 默认 2000 行对单行超长文件不设防。
输出: PreToolUse permissionDecision=deny JSON(仅 deny 时输出)。
"""
import json
import os
import sys


def main() -> int:
    raw = sys.stdin.read() or "{}"
    d = json.loads(raw)
    if d.get("tool_name") != "Read":
        return 0
    ti = d.get("tool_input") or {}
    fp = ti.get("file_path")
    if not fp or ti.get("offset") is not None or ti.get("limit") is not None:
        return 0
    lim = int(os.environ.get("COMPASS_BIGREAD_KB", "100")) * 1024
    try:
        size = os.path.getsize(fp)
    except OSError:
        return 0
    if size <= lim:
        return 0
    kb = size // 1024
    reason = (
        f"[bigread 闸] {fp} = {kb}KB > 100KB,整读会打进上下文(thrashing 病灶)。"
        f"改用: Read 带 offset/limit 分块(如 limit 400),或 Bash head -c / sed -n 取段;按需多轮读。"
    )
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception:
        sys.exit(0)
