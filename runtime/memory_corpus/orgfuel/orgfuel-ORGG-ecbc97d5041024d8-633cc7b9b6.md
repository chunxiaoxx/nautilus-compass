---
name: orgfuel-ORGG-ecbc97d5041024d8-633cc7b9b6
description: "判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 6. 开放决策"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ecbc97d5041024d8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-06-compass-mcp-3agent-dogfood-design · 6. 开放决策(需 brainstorming / 用户 / 平台)
## 6. 开放决策(需 brainstorming / 用户 / 平台)

1. **v7 的 dogfood 用例未定**(plan 标"待定")。v7 是什么 agent?消费 compass 什么?→ 需 V5/用户定。
2. **scope 存哪**:JWT claim(平台签时塞)vs compass 本地表(compass 自管)。倾向本地表(G-turf ·
   平台只签身份不管权限)· 但需平台 token 带稳定 agent_id。
3. **kairos/v7 消费编排归属**:确认 compass 只开 substrate 通道,不 wire 它们的调用逻辑(§2 张力)。
