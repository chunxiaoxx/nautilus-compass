---
name: orgfuel-ORGG-06187225717db426-afd4bb9a6d
description: "判读档判例 2026-06-06-compass-cloud-substrate-design · 4. 多 agent"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-06187225717db426
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-cloud-substrate-design · 4. 多 agent 鉴权(Phase B · gated G-token)
## 4. 多 agent 鉴权(Phase B · gated G-token)

云 daemon 暴露 ~17 MCP 工具(token-gated TCP · 复用 v5 已建传输)+ per-agent scope(Phase B authz 层 · 见 2026-06-06-compass-mcp-3agent-dogfood-design.md)。平台签 v5/v7/kairos token + 注册 endpoint。
