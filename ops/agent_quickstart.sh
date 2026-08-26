#!/usr/bin/env bash
# nautilus-compass · agent quickstart · 30 秒把任意 CLI agent 接入云记忆
# 用法: bash ops/agent_quickstart.sh <agent_name>   (如 workbuddy, my-cli-agent)
# 前置: 本机能 ssh cloud(43.160.239.61)且有 python3
set -euo pipefail

AGENT="${1:?用法: agent_quickstart.sh <agent_name>}"
AGENT=$(echo "$AGENT" | tr -c 'a-zA-Z0-9_-' '_')
CLOUD_HOST="${CLOUD_HOST:-cloud}"
BRIDGE="$HOME/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py"
MCPJSON="${MCPJSON:-$PWD/.mcp.json}"

step(){ echo -e "\n[$1/5] $2"; }

step 1 "云端签发 token($AGENT)"
TOKEN="cmp_${AGENT}_$(openssl rand -hex 16 2>/dev/null || python3 -c 'import secrets;print(secrets.token_hex(16))')"
ssh "$CLOUD_HOST" "sudo python3 - <<EOF
import json
p='/etc/compass/tokens.json'
d=json.load(open(p))
d['$TOKEN']=['tools.read','tools.write']
json.dump(d,open(p,'w'),indent=1)
print('token registered')
EOF
sudo systemctl restart compass-mcp-tcp"
echo "token: ${TOKEN:0:20}..."

step 2 "确认 9877 隧道"
if ! (exec 3<>/dev/tcp/127.0.0.1/9877) 2>/dev/null; then
  echo "  无隧道,启动 ssh -N -L 9877:127.0.0.1:9877(后台)"
  nohup ssh -N -L 9877:127.0.0.1:9877 "$CLOUD_HOST" >/dev/null 2>&1 &
  sleep 3
fi
(exec 3<>/dev/tcp/127.0.0.1/9877) 2>/dev/null && echo "  9877 可达 ✓" || { echo "  ✗ 隧道起不来"; exit 1; }

step 3 "拉最新桥脚本(若无)"
if [ ! -f "$BRIDGE" ]; then
  mkdir -p "$(dirname "$BRIDGE")"
  curl -fsSL https://raw.githubusercontent.com/chunxiaoxx/nautilus-compass/main/ops/mcp_stdio_to_cloud.py -o "$BRIDGE" \
    || ssh "$CLOUD_HOST" "cat ~/nautilus-compass/ops/mcp_stdio_to_cloud.py" > "$BRIDGE"
fi

step 4 "写 $MCPJSON"
python3 - "$MCPJSON" "$TOKEN" "$BRIDGE" "$AGENT" <<'EOF'
import json, sys, os
path, token, bridge, agent = sys.argv[1:5]
cfg = json.load(open(path, encoding="utf-8")) if os.path.exists(path) else {"mcpServers": {}}
cfg.setdefault("mcpServers", {})["nautilus-compass-cloud"] = {
  "type": "stdio",
  "command": "python",
  "args": [bridge],
  "env": {
    "COMPASS_CLOUD_HOST": "127.0.0.1",
    "COMPASS_CLOUD_PORT": "9877",
    "COMPASS_CLOUD_TOKEN": token,
    "COMPASS_AGENT_TYPE": f"claude-code-{agent}",
    "PYTHONIOENCODING": "utf-8",
  },
}
json.dump(cfg, open(path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print(f"  {path} 已写入 nautilus-compass-cloud(agent_type=claude-code-{agent})")
EOF

step 5 "端到端自检(initialize → ingest → 云落盘)"
sleep 5
python3 - "$TOKEN" <<'EOF' && echo -e "\n✅ $AGENT 接入完成:重启 CLI 后 /mcp 即见 nautilus-compass-cloud" \
  || echo -e "\n❌ 自检失败——把上面输出发给 compass 框"
import sys, socket, json, time
tok = sys.argv[1]
def call(req, t=20):
    s = socket.create_connection(("127.0.0.1", 9877), timeout=t)
    s.sendall((json.dumps(req) + "\n").encode())
    b = b""
    while b"\n" not in b:
        c = s.recv(65536)
        if not c: break
        b += c
    return json.loads(b.split(b"\n")[0].decode())
init = call({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-11-25","authToken":tok}})
assert "result" in init, f"auth 失败: {init}"
tools = call({"jsonrpc":"2.0","id":2,"method":"tools/list"})
print(f"  initialize ✓ · tools={len(tools['result']['tools'])} ✓")
r = call({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"ingest_obs","arguments":{
    "project":"C--Users-chunx","text":"quickstart selftest ok","agent_type":"quickstart"}}})
assert "result" in r, f"ingest 失败: {r}"
print("  ingest_obs ✓ (云端 C--Users-chunx 落盘)")
EOF
