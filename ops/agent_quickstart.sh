#!/usr/bin/env bash
# nautilus-compass · agent quickstart · 30 秒把任意 CLI agent 接入云记忆
# 用法: bash ops/agent_quickstart.sh <agent_name>   (如 workbuddy, my-cli-agent)
# 前置: 本机能 ssh cloud(43.160.239.61)且有 python3
set -euo pipefail

AGENT="${1:?用法: agent_quickstart.sh <agent_name>}"
# 2026-08-28 fix(workbuddy 实测): printf 去换行——echo 的 \n 会被 tr 吃成尾部 '_',产出孤儿 token(cmp_xxx__)
AGENT=$(printf '%s' "$AGENT" | tr -c 'a-zA-Z0-9_-' '_')
CLOUD_HOST="${CLOUD_HOST:-cloud}"
BRIDGE="$HOME/.claude/plugins/nautilus-compass/ops/mcp_stdio_to_cloud.py"
MCPJSON="${MCPJSON:-$PWD/.mcp.json}"
# 2026-08-28 fix(workbuddy 实测): Git-Bash 的 /c/... 路径喂给 Windows 原生 python 必炸
# (FileNotFoundError + .mcp.json 里 args 也带 /c/... 导致 Claude Code 桥接起不来)。
# cygpath 转原生路径;Linux 上 cygpath 不存在,原样透传。
if command -v cygpath >/dev/null 2>&1; then
  MCPJSON=$(cygpath -w "$MCPJSON")
  BRIDGE_NATIVE=$(cygpath -w "$BRIDGE")
else
  BRIDGE_NATIVE="$BRIDGE"
fi

step(){ echo -e "\n[$1/5] $2"; }

step 1 "云端签发 token($AGENT · 默认只读当前项目,写权限用 token_admin 手动加)"
# 2026-08-28 安全修复: 旧版这里自动签发全库读写 token(任何能 ssh cloud 的进程
# 都能自签全权=权限边界退化为 ssh 边界)。改为默认 read:<project> scoped 签发;
# 需要写权限/全域读时用 ops/compass_token_admin.py 显式加。
PROJECT_SLUG=$(basename "$(git rev-parse --show-toplevel 2>/dev/null || echo "$PWD")" | tr -c 'a-zA-Z0-9_-' '-' | sed 's/-$//')
TOKEN="cmp_${AGENT}__$(openssl rand -hex 16 2>/dev/null || python3 -c 'import secrets;print(secrets.token_hex(16))')"
ssh "$CLOUD_HOST" "sudo python3 - <<EOF
import json
p='/etc/compass/tokens.json'
d=json.load(open(p))
d['$TOKEN']={'scopes':['read:$PROJECT_SLUG'],'granted_at':'$(date -u +%Y-%m-%dT%H:%M:%SZ)'}
json.dump(d,open(p,'w'),indent=1)
print('token registered (read:$PROJECT_SLUG)')
EOF
sudo systemctl restart compass-mcp-http compass-mcp-tcp"
echo "token: ${TOKEN:0:20}... (scope=read:$PROJECT_SLUG · 全权请用 ops/compass_token_admin.py grant)"

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
# 2026-08-28 fix: bridge 路径用 BRIDGE_NATIVE(Git-Bash 下已是 Windows 原生路径)
python3 - "$MCPJSON" "$TOKEN" "$BRIDGE_NATIVE" "$AGENT" <<'EOF'
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
import sys, socket, json
tok = sys.argv[1]
# 2026-08-28 fix(workbuddy 实测): 云端 mcp_server 是 per-connection auth——
# 首条必须为带 authToken 的 initialize,且 auth 态绑定在连接上。每个请求新建
# socket 会让 tools/list 拿不到。改单连接复用,顺序发三条。
s = socket.create_connection(("127.0.0.1", 9877), timeout=20)
def call(req):
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
# 2026-08-28 fix(workbuddy 实测): v2.3.0 ingest_obs schema 必填 name(8-15 字),
# text 不是合法参数(旧脚本过期入参)。且 scoped token 默认只读——自检改走
# recall(read scope 内),写入路径由有 write scope 的 token 另测。
r = call({"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"recall","arguments":{
    "query":"project overview","project":"__selfcheck__","top_k":1}}})
assert "result" in r, f"recall 失败: {r}"
print("  recall ✓ (read scope 生效;写权限用 ops/compass_token_admin.py 加)")
s.close()
EOF

# ── 可选:--hud · 一键装融合 HUD(claude-hud 基座 + 实时 compass 段) ──
if [ "${2:-}" = "--hud" ]; then
  python3 - <<'PYH'
import json, os
p = os.path.join(os.getcwd(), ".claude", "settings.json")
os.makedirs(os.path.dirname(p), exist_ok=True)
d = json.load(open(p, encoding="utf-8")) if os.path.exists(p) else {}
wrapper = os.path.expanduser("~/.claude/plugins/nautilus-compass/compass_hud_wrapper.py").replace("\\", "/")
d["statusLine"] = {"type": "command", "command": f'python "{wrapper}"'}
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("HUD 已装:重启 CLI 后状态栏显示 📡compass 段(5min 流量/延迟/记忆数/drift)")
PYH
fi
