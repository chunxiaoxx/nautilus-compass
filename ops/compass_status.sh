#!/usr/bin/env bash
# nautilus-compass · compass status · 一屏看清记忆层健康状况(用户可感知面板雏形)
# 用法: bash ops/compass_status.sh
set -uo pipefail
CLOUD_HOST="${CLOUD_HOST:-cloud}"

line(){ printf '%-22s %s\n' "$1" "$2"; }

echo "═══ nautilus-compass status ═══"

# 1. 本地 daemon
L=$(python3 - <<'EOF' 2>/dev/null || echo '{"ok":false}'
import socket, json
s=socket.create_connection(("127.0.0.1",9876),timeout=3)
s.sendall(b'{"action":"status"}\n')
print(s.recv(65536).decode())
EOF
)
python3 - "$L" <<'EOF'
import json,sys
try: d=json.loads(sys.argv[1])
except Exception: d={}
if d.get("ok"):
    r=d["recall"]["sliding_5min"]
    print(f"local daemon      ✓ 5min:{r['count_5min']} 次 · p95 {r['p95_ms']}ms · overload {r['overload_5min']}")
    print(f"                   内存 {d['rss_mb']}MB · CPU {d['cpu_pct']}% · pkl {d['memory']['pkl_count']} 个/{d['memory']['pkl_total_mb']}MB")
else:
    if d: print("local daemon      ~ 旧版运行中(无 /status)·重启后升级: powershell ~/.claude/plugins/nautilus-compass/daemon_start.ps1")
    else: print("local daemon      ✗ DOWN")
EOF

# 2. 云端 MCP
if (exec 3<>/dev/tcp/127.0.0.1/9877) 2>/dev/null; then
  echo "cloud mcp (9877)   ✓ 隧道可达"
else
  echo "cloud mcp (9877)   ✗ 隧道断(ssh -N -L 9877:127.0.0.1:9877 $CLOUD_HOST)"
fi

# 3. 云端记忆池 + 本 agent 近况
ssh -o ConnectTimeout=8 "$CLOUD_HOST" 'bash -s' <<'EOF' 2>/dev/null || echo "remote stats       (ssh 不可达)"
N=$(ls ~/.claude/projects/C--Users-chunx/memory/ 2>/dev/null | wc -l)
R=$(ls -t ~/.claude/projects/C--Users-chunx/memory/ 2>/dev/null | head -1)
D=$(systemctl is-active compass-bge-daemon 2>/dev/null)
M=$(systemctl is-active compass-mcp-tcp 2>/dev/null)
echo "云记忆池            $N 条 · daemon:$D · mcp:$M"
echo "最新 obs            $R"
EOF
