---
name: orgfuel-ORGG-f598effac081c910-fe5d39a60b
description: "判读档判例 2026-06-21-memory-capsule-evolution-design · 5. 发扬光大 ·"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f598effac081c910
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-21-memory-capsule-evolution-design · 5. 发扬光大 · 分阶段路线
## 5. 发扬光大 · 分阶段路线

| 阶段 | 内容 | 借鉴/缺口 | turf |
|---|---|---|---|
| **P0 · 防退化(最高危)** | ① W1 写回带 verdict 元数据(score/bucket/source)② 质量分接进 serving recall 排序 ③ 单条 revoke API(错胶囊标废停召回)| 补缺口①② | compass(W1/W2 客户端 + serving) |
| **P1 · 精度** | 胶囊结构化字段:triggers / env fingerprint / confidence / **失败边界**(when_not_to_use)| 借鉴1·补缺口③ | compass + V5(写端配合) |
| **P2 · 自然选择** | report 回流闭环:B 用完把成功/失败回写胶囊 → 喂质量分 | 借鉴2 | compass + V5 |
| **P3 · 进化/衰减** | 打通路 B 的 tier/forget/PoI 到 serving observations(复用 `poi_calculator`/`tier_promotion`)+ 可逆时间衰减 | 借鉴3·打通两条路 | compass |
| **对外 MCP** | 内部 A2A + 生命周期成熟后,再评估对外开放(数据自治前提·内部先跑通) | — | compass + 用户决策 |
