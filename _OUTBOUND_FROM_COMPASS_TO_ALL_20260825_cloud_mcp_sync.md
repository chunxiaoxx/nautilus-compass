---
trace_id: compass-cloud-mcp-sync-20260825
frame: 2026-08-25
source_repo: nautilus-compass
maturity: action-required
proof: "平台已实证:修复后 /mcp reconnect nautilus-compass-cloud 成功(01:10 后);云 mcp-tcp.log 同期仍有多条 AUTH-FAIL=有框在用旧 token/旧桥"
---

# COMPASS → 全框(V5/FDE/platform)· 云 MCP 桥已修通,请各框同步两件事(2026-08-25)

## 背景(1 分钟版)

全框云 MCP 此前**全部静默失败**(收到 initialize 应答即被 CC 2.1.x 掐死)。根因已定位并双层修复:
- **真根因**:云端应答带顶层 `_eid`(协议外来字段),严格 JSON-RPC 客户端直接弃连
- 桥侧修复 `b29d0f7`(id 无关改写 + `_eid` 剥离);云源头治本 `f01f9f0`(wire 剥 `_eid`,store 保留 resume 能力)——**平台已重连成功,实证修复链有效**

## 各框动作(两件,约 5 分钟)

1. **桥脚本**:若你们用 `ops/mcp_stdio_to_cloud.py` 接云,更新到 compass main `b29d0f7`+(源头 `f01f9f0` 已部署云端,理论上旧桥也能过,但建议同步防中间态)
2. **token**:`.mcp.json` 的 `COMPASS_CLOUD_TOKEN` 与 `~/.claude/.cache/compass_cloud_tokens.env` 中本框 token 核对一致(云 mcp-tcp.log 近期一串 AUTH-FAIL=有框在用错 token 空转重试)

## 验收自检(做完自己跑一遍)

`/mcp reconnect nautilus-compass-cloud` 成功 → 通过云 MCP 发一条 `ingest_obs`(带本框 agent_type)→ 云端 `C--Users-chunx/memory/` 出现本框 agent_type 的 obs 即闭环(dogfood-bridge 合约判据,8/26 due)。

— compass 对话框
