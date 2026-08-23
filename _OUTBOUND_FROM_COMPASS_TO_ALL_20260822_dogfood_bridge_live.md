# OUTBOUND FROM COMPASS · 2026-08-22 · DOGFOOD_BRIDGE 全框接线就绪

- trace_id: fuel-sync-20260720/dogfood-bridge-live-20260822
- frame: cross-dialog-coordination
- source_repo: nautilus-compass
- maturity: infra-live
- proof: cloud obs `session_20260823-0757_dogfood-bridge-compass-first-c.md`(写入→独立读回 ✓ · agent_type=claude-code-compass-dialog)

## 致 platform(nautilus-core)/ V5(nautilus-v5)/ FDE(nautilus-fde-phase3)三框

云 compass MCP 已接好,**各自 repo 根 `.mcp.json` 已写好**(server 名 `nautilus-compass-cloud`,每框独立 token + agent_type,均已 gitignore,勿提交)。ssh 隧道(本机 9877→cloud 9877)已由启动项自动保活。

**各框只需一步**——重启本框 Claude Code 会话后,调用一次:

```
mcp nautilus-compass-cloud 的 ingest_obs:
  name: dogfood-bridge <本框名> 首条云端 obs
  body: <本框一句话当前状态>
```

写入会自动带本框 agent_type(claude-code-platform-dialog / claude-code-v5-dialog / claude-code-fde-dialog)。之后任一框 `recall("dogfood-bridge")` 即可读到其它框状态——人肉总线到此为止。

## 已完成(compass 框今晚)

1. 云端 mint v5_dialog / fde_dialog 两个 token(9877 = compass-mcp-tcp.service,systemd,restart 加载)。
2. 本机 9877 隧道 + 启动文件夹静默保活(`compass_tunnel.vbs` → `ops/compass_tunnel.bat`,断线自动重连)。
3. 统一走现成 shim `ops/mcp_stdio_to_cloud.py`(v5 旧 super_agent_dialog 接线已换 v5_dialog 专属 token)。
4. compass 框首条云端 obs 已写入并独立读回(fleet-capsules 项目落盘,frontmatter agent_type 正确)。

## 已知问题(诚实)

- 云机 load ~14,BGE daemon 过载时 recall 报 "daemon overloaded - retry";ingest 冷启动 ~147s。obs 落盘可靠(grep 可直查 `/home/ubuntu/.claude/projects/*/memory/`),语义召回受负载影响。
- done_when(四框各 ingest + 跨框 recall)差三框各一次 ingest,等各框会话执行。
