---
name: orgfuel-ORGG-3e524dd97bb2fbeb-da25e1b0dd
description: "判读档判例 2026-06-21-memory-capsule-evolution-design · 3. 有机耦合架构"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-3e524dd97bb2fbeb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-21-memory-capsule-evolution-design · 3. 有机耦合架构(各方角色)
## 3. 有机耦合架构(各方角色)

```
各 agent(V5/kairos)  ──W1 写胶囊(learning + 结构化边界 + verdict 元数据)──┐
       ▲                                                                    ▼
       │ W2 召回(质量过滤 + 语义 + 失败边界匹配)              compass 记忆层(胶囊存储)
       │                                                       · bge-m3 语义召回(已上线)
       │                                                       · 质量排序(接 PoI·待)
       └────────────────────────────────────────────────────  · 生命周期 promote/decay/revoke(接路B·待)
                                                                         ▲
soul:verdict(reward/overall_pass/bucket)= 胶囊的 validate/promote 门 ───┘(已隐式生效·只差带元数据)
平台:dispatch/verdict-bus = 信号源(不用改)
对外 MCP:compass serving 已是雏形(compass.nautilus.soci
