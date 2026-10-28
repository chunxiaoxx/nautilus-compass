# -*- coding: utf-8 -*-
"""
core SessionStart hook - 核 cwd + 3 档 alert

从 compass/ops/compass_session_start.py 复制 + 改 EXPECTED_CWD
EXPECTED_CWD = 'nautilus-core'
"""
import json
import os
import sys

EXPECTED_CWD = "nautilus-core"

ALERTS_RED = [
    "超红: 越界写非 core 项目文件",
    "超红: 不写 .claude/memory/session_*.md 就 Stop",
    "超红: drift score < -0.07(R1 立停)",
]
ALERTS_YELLOW = [
    "黄: 不读 auto_surface_hook / 不读 NEW_SESSION_START / 不核身份",
    "黄: 段落超 8 行 / '真'字 >= 3",
    "黄: 不写 session memory 落档",
]

def main():
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cwd = data.get("cwd", os.getcwd())
    if EXPECTED_CWD not in cwd:
        sys.stderr.write("[" + EXPECTED_CWD + "-hook] FAIL: cwd=" + cwd + " 不含 " + EXPECTED_CWD + chr(92) + "n")
        return 1
    for a in ALERTS_RED:
        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [超红] " + a + chr(92) + "n")
    for a in ALERTS_YELLOW:
        sys.stderr.write("[" + EXPECTED_CWD + "-alert] [黄] " + a + chr(92) + "n")
    # org/bootstrap 狗粮接入(§⓪-E 索引环):mailbox 未读+due 亮牌,fail-soft 3s
    try:
        import urllib.request
        with urllib.request.urlopen(
                "https://www.nautilus.social/api/platform/org/bootstrap?agent=platform",
                timeout=3) as resp:
            import json as _json
            d = _json.load(resp).get("data") or {}
        mb = d.get("mailbox") or {}
        unread, due = len(mb.get("unread") or []), mb.get("due_12h", 0)
        if unread:
            sys.stderr.write("[org] mailbox 未读 " + str(unread) + " 封(12h 内到期 " + str(due) + ")——先处理再开工" + chr(10))
    except Exception:
        pass  # 网络/服务不可用时静默,不阻塞开局
    return 0

if __name__ == "__main__":
    sys.exit(main())
