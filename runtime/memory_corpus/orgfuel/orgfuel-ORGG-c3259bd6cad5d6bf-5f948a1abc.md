---
name: orgfuel-ORGG-c3259bd6cad5d6bf-5f948a1abc
description: "判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 九 · 组件清单("
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-c3259bd6cad5d6bf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 P3_DYNAMIC_WEIGHT_PIPELINE_DESIGN_20261003 · 九 · 组件清单(实现顺序=依赖序)
## 九 · 组件清单(实现顺序=依赖序)

| 件 | 路径 | GPU |
|---|---|---|
| p3_delta.py(S1) | tools/ | 无 |
| REG-100 冻结件 | runtime/verdict_corpus/reg100.jsonl + sha 落档 | 无(一次性) |
| p3_ticket.py(S2) | tools/ | 无 |
| train_judge_lora.py 增量模式(S3) | tools/(热启动+replay 参数) | 4090 短租 |
| p3_gate.py(S4) | tools/ | 随 S3 机内 |
| p3_promote.py + ledger(S5/S6) | tools/ + runtime/judge_lora_p3/ | 无 |

首 delta 导出(G1/pusht verdict 入料)是管道外前置件,建议与 S1 实现同批做——导出即得首轮 delta 读数,可校准"≥200"触发门槛的现实性。
