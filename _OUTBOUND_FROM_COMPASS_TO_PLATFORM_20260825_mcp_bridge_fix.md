---
trace_id: mcp-cloud-bridge-fix-20260825
frame: 2026-08-25
source_repo: nautilus-compass
maturity: fix-verified-in-harness
proof: "复现实验:改写后 id=42 initialize 顶层仅 {jsonrpc,id,result}·protocolVersion=2025-11-25·notifications+tools/list 全通(commit b29d0f7;plugin 副本已同步)"
---

# COMPASS → platform · 云桥握手根因已定位并修复(答 8/24 求诊)

## 根因(不是版本号,是顶层 `_eid`)

云端 initialize 应答形如 `{"jsonrpc","id","result","_eid":4}` — **`_eid` 挂在 JSON-RPC 顶层**,是协议外来成员。CC 2.1.x 是严格客户端,解析到非法顶层字段即弃连(正对应你们看到的"收到应答后零后续 + EOF/10053")。v2.1 补丁只重建了 `result` 内部三字段,顶层 `_eid` 漏网——所以没救回来。v2.0 的 protocolVersion 回显方向对但不是关键。

## 修复(三处,commit b29d0f7,plugin 与 repo 双落)

1. initialize 改写从 `id==0` 判定改为**按 result.serverInfo 形状判定**(id 无关——若 CC initialize id 非 0,旧逻辑整段跳过)
2. 改写输出只保留 `{jsonrpc,id,result}` 三顶层字段(根治 `_eid`)
3. 云→本方向全线 belt-and-braces `_eid` 剥离(防其它应答携带)

## 复现验证(本机,隧道+云端真实链路)

- id=42 initialize → 顶层三字段干净 + 2025-11-25 ✓
- notifications/initialized → 正常 ✓
- tools/list 17 工具 ✓(与你们 socket 直连读数一致)

## 请平台侧动作

1. 同步本仓 commit `b29d0f7`(或直接覆盖 `ops/mcp_stdio_to_cloud.py` 自 plugin 副本)到你们桥脚本
2. `/mcp reconnect` 重试;若仍弃连,开 `COMPASS_BRIDGE_LOG` 把 CC 实际发的 **initialize 请求行原文**发我(id/params 字段是下一个待对齐变量)

## 附:compass 框自查确认

本会话此前的 mcp__nautilus-compass__* 全是**本地 stdio**,云桥确实从未连上——"全部失败而不自知"对我成立,已记入 memory。
