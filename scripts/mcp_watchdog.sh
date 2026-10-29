#!/bin/bash
# compass MCP 端到端探活/自愈 watchdog(2026-10-27 质疑审查产物)
# 8097 本地 HTTP + 公网域名双探;daemon 死则拉起;留痕 /tmp/compass_watchdog.log
LOG=/tmp/compass_watchdog.log
TS=$(date "+%m-%d %H:%M:%S")
TOK=$(python3 -c "import json;print(list(json.load(open('$HOME/.claude/.cache/compass_mcp_tokens.json')).keys())[0])" 2>/dev/null)

# 1) 本地 8097
LC=$(curl -s --max-time 8 -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8097/mcp/ \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"watchdog","version":"1"}}}')
# 2) daemon 9876
DC=$(python3 -c "
import socket
s=socket.socket(); s.settimeout(5)
try: s.connect(('127.0.0.1',9876)); print('ok')
except Exception: print('dead')" 2>/dev/null)
# 3) 公网域名(经cloud nginx→Mac)
# 3) 公网域名(经cloud nginx→Mac)——10/29 R203定谳:服务端listen 8443 ssl无443(9/5"8443陷阱"复发),
#    且腾讯云安全组8443未放行(外部恒000,候用户控制台放行);链路本体=cloud本机127.0.0.1:8443=200[实测]。
#    业务零影响:主通道=本地stdio+Tailscale 100.84.23.45:8097双路。此探活在放行前恒000,仅作链路降级监控。
PC=$(curl -s --max-time 12 -o /dev/null -w "%{http_code}" -X POST https://compass.nautilus.social:8443/mcp/ \
  -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"watchdog","version":"1"}}}')

ACT=""
if [ "$DC" != "ok" ]; then
  launchctl kickstart -k gui/$(id -u)/com.nautilus.compass-daemon 2>/dev/null
  ACT="$ACT daemon_restarted"
fi
if [ "$LC" != "200" ] && [ "$DC" = "ok" ]; then
  launchctl kickstart -k gui/$(id -u)/com.nautilus.compass-mcp-http 2>/dev/null
  ACT="$ACT mcphttp_restarted"
fi
echo "[$TS] local=$LC daemon=$DC public=$PC$ACT" >> "$LOG"
# 只在异常时多留一行详情,正常轮一行即可(与值守轮 noop 静默纪律同构)
