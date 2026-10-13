---
name: orgfuel-ORGG-fd133e8750c19f91-5fc993d9a7
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · 目标 ## 目标  让 L3"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-fd133e8750c19f91
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · 目标
## 目标

让 L3 PoI 递归闭环在**生产路径**真正落地。当前 candidate emission 只在 `recall.py` 的 hook/CLI/daemon 路径 fire,而平台 agent(V5)走的是云端 HTTP `/v1/v14/recall`(8770)—— 该路径不 emit candidate。本设计给 `/v1/v14/recall` 加 candidate emission,并在本地搭 reconciler,使:

```
平台 agent 调 v14 recall → candidate(带 actor=agent_id)→ agent 行动 → outcome(agent_tool_calls)
→ reconciler join → cumulative_impact 累积到被引用 memory → 下次 recall boost_top_k 用上
```
