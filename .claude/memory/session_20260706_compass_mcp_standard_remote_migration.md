---
name: session_20260706_compass_mcp_standard_remote_migration
description: 7/6 · compass MCP 断线根因(cloud 过载:泄漏 sshd 20天92%CPU + V5 main_singleton 空转90%CPU 把 2 核拖到 load5 → SSH隧道握手>30s超时)已修(kill sshd,load5→2)。牵出架构真相:当前 compass MCP = stdio桥→SSH隧道→localhost:9877 raw-TCP(7/28 决策"不重造官方HTTP"复用token-TCP的产物)。用户拍板迁标准远程 MCP(公网HTTPS),照抄平台 HR agent 的 FastMCP+nginx+certbot 参考实现。方案 + Task0-3 已本地 grounded 验证。
metadata:
  node_type: session
  type: decision
  originSessionId: claude-opus-4-8[1m] (2026-07-06)
---

# Session 2026-07-06 · compass MCP 断线修复 + 迁标准远程 MCP(Task0-3 done)

## 1 · MCP 断线根因(grounded 实测 · 非 MCP 死)

`/mcp` 报 `nautilus-compass-cloud timed out 30000ms`。诊断链:
- 配置 = stdio bridge `ops/mcp_stdio_to_cloud.py` → `127.0.0.1:9877`(**SSH 隧道 PID 14744** `ssh -fN -L 9877:127.0.0.1:9877 cloud`)→ cloud `compass-mcp-tcp.service`(pid 2637249,`mcp_server.py --transport tcp --port 9877 --token-file /etc/compass/tokens.json`,v2.3.0)。三 systemd active,直连探针 <1s 得合法 init。**云服务活、隧道通** —— 不是 MCP 死。
- 真因 = cloud **2 核机 load 5.01**(250% 过载)→ SSH 隧道握手偶发 >30s → 破 MCP 客户端 30s 超时 → 本 session 整程掉线(recall 退回本地 BGE)。
- 两个失控进程:① **sshd PID 63067**(泄漏会话·1000+ socket fd·卡 20 天 91.8% CPU)= platform 死连接 → **已 kill(用户授权),load 5.01→2.01,握手实测 <0.4s×3 稳**。② **V5 `nautilus_v5.main_singleton` PID 884064**(6/30 起 90% CPU + 10.6% mem 空转)= V5 turf,**未杀,已 ingest_obs outbound 到 project=nautilus-v5**(thread `thread_compass_to_v5_singleton_spin_20260706`)交回 V5 框。
- 恢复本 session compass MCP:cloud 过载已清 → **重启 Claude Code** 即经现有桥重连。

## 2 · 架构真相:为什么走 SSH(不是补丁,是 7/28 决策)

- Claude Code 侧 = **标准 MCP stdio 传输**(完好);stdio "server" 是 `mcp_stdio_to_cloud.py` 桥(v1.8/v1.9:auto-reconnect + 在途持久化)。
- SSH 是垫在桥底下的传输:cloud MCP 服务只绑 `127.0.0.1:9877`(localhost-only,不公开)→ SSH `-L` 是够到它的办法。
- **7/28 决策(docs/plans/2026-06-06-compass-mcp-3agent-dogfood-design.md):「不重造官方 HTTP,复用 token-gated TCP」** → 主动选了 raw-TCP,公网 HTTP 网关(k8s gateway.yaml/ingress.yaml)PARKED on 平台签 G-token。

## 3 · 标准远程 MCP 早已实现(用户提醒·grounded 证实)

平台已有公网 HTTPS MCP,**HR agent 那套是金标准可照抄**:
- `hr-mcp-server/server.py` = **官方 `from mcp.server.fastmcp import FastMCP`** · `mcp.run(transport="streamable-http")` on 8090 · nginx `hr-agent.conf`: `hr.nautilus.social` `location = /mcp → 127.0.0.1:8090` + certbot TLS。**Claude Code `type:http` 原生连**。
- 平台 MCP `nautilus-engine/mcp_server.py`(8096,手搓 http.server,`POST /mcp`=200)= 自定义,不照抄。
- compass 自己的 `compass_http.py` `/mcp/*` 是 REST 三路由(无 JSON-RPC 信封/无 SSE)→ **Claude Code 连不上**,故须建规范 Streamable-HTTP 面。

## 4 · 决策 + 进度(用户拍:B=迁标准远程 · 选项3=公网HTTPS)

方案 = `plugin repo docs/plans/2026-07-06-compass-mcp-standard-remote-fastmcp.md`(8 任务 TDD)。核心:新增 `mcp_http_server.py` 用低阶 `mcp.server.lowlevel.Server` + `StreamableHTTPSessionManager` 复用 `mcp_server.TOOLS`(17 工具·`{fn,schema}`),bearer auth 复用 `/etc/compass/tokens.json`,照抄 HR nginx+certbot。

**turf**:compass 写 wrapper/测/本地验(Task0-5);**nginx 子域/DNS/cert/共享VM 部署 = platform turf**(Task6 做成 handoff,不擅自 apply)。

**已完成 Task 0-3(branch `feat/mcp-standard-remote-http` @ plugin repo · 2 commit 34334c1/367e1d6)**:
- `mcp_http_server.py` + `tests/test_mcp_http_server.py`(5/5 green)+ `scripts/smoke_http_mcp.py`。
- 本地真 socket 验证:init(serverInfo=nautilus-compass 2.3.0)+ tools/list=17 + **tools/call recall 真 daemon(9876)往返 isError=False** + auth 无token→401/有token→放行。
- 端点 canonical = `/mcp/`(Mount);SDK=mcp 1.16.0;工具 fn 同步→`anyio.to_thread.run_sync` 包(不堵事件循环)。

**待办**:Task4(systemd unit draft)· Task5(nginx+Claude Code config sample)· Task6(**平台 handoff:DNS compass.nautilus.social + certbot + 部署 8097**)· Task7(切 `type:http` + 退役桥/隧道)· Task8(PR/记录)。Task2 Step3(Claude Code 原生连 verify)留到 cloud 部署后做。

## 关联
[[session_20260706_compass_ssot_drift_qixuw_cstart_orphan_mcp_restore]] · [[session_20260704_compass_mcp_local_repaired]]
