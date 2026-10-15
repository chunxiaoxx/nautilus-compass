#!/bin/bash
# compass LOOP 单轮执行器(schtasks 每 30 分钟触发)
cd "C:/Users/chunx/Projects/nautilus-compass" || exit 1
[ -f runtime/loop/STOP ] && exit 0
PROMPT=$(cat runtime/loop/round_prompt.md)
export COMPASS_EMBED_PROXY=http://127.0.0.1:19987
"C:/Users/chunx/Projects/nautilus-compass/.venv/Scripts/python.exe" - <<'PYEOF' >/dev/null 2>&1 || true
# 隧道保活:19987 无监听则重启 ssh -L 长连接
import socket, subprocess, sys
try:
    s=socket.create_connection(('127.0.0.1',19987), timeout=3); s.close()
except Exception:
    subprocess.Popen(['ssh','-f','-N','-o','ExitOnForwardFailure=yes','-o','ServerAliveInterval=20',
        '-o','StrictHostKeyChecking=no','-i','C:/Users/chunx/.ssh/id_ed25519',
        '-L','127.0.0.1:19987:127.0.0.1:8400','-p','23236','root@223.109.239.30'])
    time.sleep(5)
PYEOF
claude -p "$PROMPT" --model claude-sonnet-4-5 --output-format text >> runtime/loop/rounds.log 2>&1
echo "---- round end $(date '+%m-%d %H:%M') ----" >> runtime/loop/rounds.log
