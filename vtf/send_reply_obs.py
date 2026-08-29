"""org_sync 回函 → compass 云端 obs(吃狗粮走自己的 HTTP MCP)"""
import json
import urllib.request

payload = {
    "jsonrpc": "2.0", "id": 1, "method": "tools/call",
    "params": {"name": "ingest_obs", "arguments": {
        "project": "C--Users-chunx",
        "name": "compass回函org_sync",
        "agent_type": "claude-code-compass",
        "body": ("org_sync 回函已发(_REPLY_FROM_COMPASS_TO_PLATFORM_org_sync_20260829.md,"
                 "core 仓根已同步):三台阶认领=记忆/探针/账本自动件+外部真值计量层;"
                 "P1P2 解冻(P1 已实做大半+9877 退役日期待写/P2 提审本周)/P3 维持冻结;"
                 "e2e 500=42.6% 定案分型两极;workbuddy 反馈包 P0-P3 全消化 v3.1.0;"
                 "GPU 镜像 v2608291059 固化。"),
    }},
}
req = urllib.request.Request(
    "https://compass.nautilus.social/mcp/", data=json.dumps(payload).encode(),
    headers={"Authorization": "Bearer cmp_my-agent__9142d12d6fa0e335dc23b0c8ea164cc1",
             "Content-Type": "application/json", "Accept": "application/json"})
r = json.loads(urllib.request.urlopen(req, timeout=30).read())
print("OBS:", json.dumps(r, ensure_ascii=False)[:220])
