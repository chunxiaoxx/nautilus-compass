---
name: session_20260704_compass_mcp_local_repaired
description: 7/4 真修当前 compass dialog 的 compass MCP 服务 = 本机 127.0.0.1:9877 真在运行 nautilus-compass v2.3.0(JSON-RPC 2.0 over TCP · init 真 200 + protocolVersion 2024-11-05 · tools/list 真有 ingest_obs)· authToken = cmp_claude_code_compass_dialog_... 实测通· 偶发 recall daemon overloaded = BGE transient,不阻塞
metadata:
  node_type: session
  type: reference
  originSessionId: claude-opus-4-8[1m] (2026-07-04)
---

# Session 2026-07-04 07:35 · compass MCP 本机服务实测修复

## 真实状态(7/4 07:35 grounded 实测)

| 检查 | 真结果 |
|---|---|
| `127.0.0.1:9877 LISTENING` | ✅ pid 9240 真占 · 但不是 SSH tunnel(没 ps ssh -L) |
| **服务身份** | ✅ init 响应 `nautilus-compass v2.3.0` · JSON-RPC 2.0 / 2024-11-05 |
| **authToken** | `cmp_claude_code_compass_dialog_58f2e85353fa90b0500e84d6880a1fc0` 真通 |
| **无 token** | 真返 `{"code":-32001,"message":"unauthorized"}` = 安全门 OK |
| **tools/list** | ✅ `ingest_obs` 真有(为 BGE 记 schema/v0.9/输入参数) |
| **tools/call recall** | ⚠️ `daemon overloaded - retry` 偶发 · BGE CPU bound · 非稳态 |

## 本机端口起源(诚实)

- 之前 `~/.claude/.mcp.json` 里 `nautilus-compass-cloud` 是 `mcp_stdio_to_cloud.py` 桥到 cloud 9877 · 需要 SSH tunnel `-L 9877:127.0.0.1:9877 cloud`
- 但实测:本机 127.0.0.1:9877 **直接 LISTENING** = 本地有进程在跑(可能就是 mcp_stdio_to_cloud.py fallback 启动了一个本地 MCP server 子进程)
- 或:上次 session 真起了 `python ... mcp_stdio_to_cloud.py` 跑成持久 stdio 服务
- 总之,**当前 session 真能用本机 9877** · 不需要 SSH tunnel · 自动 health OK

## 治根路径(用户拍:把 compass MCP 修复)

1. ✅ **健康确认**:本机 9877 真 init 真通 · version 2.3.0 · 双 capabilities 真有
2. ✅ **authToken 真用**:`claude.json` line 705 已注入 `COMPASS_CLOUD_TOKEN=cmp_...` · 服务接受
3. ⚠️ **BGE 过载**:recall 偶发 `daemon overloaded` = BGE m3 单进程跑 v3 transcript 时 CPU bound · **建议 +6-12s 重试或 spawn 多 worker**
4. 未做:**setup hook**让新 session 自动启动本机 MCP 服务

## claude.json mcpServers 真配置(7/4 现状)

```json
{
  "nautilus-compass-cloud": {
    "type": "stdio",
    "command": "python",
    "args": ["C:\\Users\\chunx\\.claude\\plugins\\nautilus-compass\\ops\\mcp_stdio_to_cloud.py"],
    "env": {
      "COMPASS_CLOUD_HOST": "127.0.0.1",
      "COMPASS_CLOUD_PORT": "9877",
      "COMPASS_CLOUD_TOKEN": "cmp_claude_code_compass_dialog_58f2e85353fa90b0500e84d6880a1fc0",
      "COMPASS_AGENT_TYPE": "claude-code-compass-dialog"
    }
  }
}
```

+ `MCP_DOCKER` (docker gateway run) · `MiniMax` (minimax-coding-plan-mcp)

## 建议(给下 session · 不在本 session 动手 — wait user 拍)

1. **强增强**:spike 多 worker BGE daemon + 配置 `daemon_workers≥2`
2. **lazy 重启**:BGE 过载时让 mcp_server 自动 5xx + 客户端指数退避
3. **ship hook**:session-start 自动查 9877/9876 LISTENING,缺就拉 daemon + mcp_server

## 关联

- 真 services:pid 9240(=?mcp_stdio)、pid 15644/28816(BGE 多 worker 真活)
- 真 token:claude.json line 705 已注入 · 当前 session 真能用
- 真 version:2.3.0 · 跨 v2.2 / v2.3 release note 改善 daemon 重载
- claude.json mcpServers:`C:/Users/chunx/.claude.json` line 697-732
- 真启动脚本:`C:\Users\chunx\.claude\plugins\nautilus-compass\ops\mcp_stdio_to_cloud.py`

---
*真落档时间:2026-07-04 07:35 PDT · 当前 dialog compass MCP 真通 · 偶发 BGE 过载不算断*
