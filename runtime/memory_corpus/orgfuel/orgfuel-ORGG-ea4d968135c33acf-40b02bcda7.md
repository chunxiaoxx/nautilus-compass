---
name: orgfuel-ORGG-ea4d968135c33acf-40b02bcda7
description: "判读档判例 2026-06-03-p5-v14-poi-emission-design · 跨对话框契约状态(已锁) #"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ea4d968135c33acf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-03-p5-v14-poi-emission-design · 跨对话框契约状态(已锁)
## 跨对话框契约状态(已锁)

`cnt_compass_v5_recall_demand_c1`,双侧拍板 **(A)**:
- V5 实际打 `/v1/v14/recall`(`compass_client.py:220`),当前 params `{q, top_k, scope, project}` 无 agent_id
- `/v1/v14/recall` = 云端 adapter → daemon:9876 BGE-m3(V5 真语义召回);`/v1/recall` = 旧 keyword fallback(拒降级)
- **序列**:① compass 给 v14 recall 加 emission(gating · 本设计)→ ② V5 加 1 行 `agent_id=nautilus-prime-001`(ready-on-signal)→ ③(可选)V5 selector 决策点 wire
- join 口径:`candidate.actor == agent_tool_calls.agent_id` 严格相等 + 24h 窗
