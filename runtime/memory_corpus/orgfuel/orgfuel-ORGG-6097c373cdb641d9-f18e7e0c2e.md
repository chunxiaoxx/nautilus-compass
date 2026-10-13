---
name: orgfuel-ORGG-6097c373cdb641d9-f18e7e0c2e
description: "判读档判例 2026-06-21-memory-capsule-evolution-design · 6. 最小改动接线"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6097c373cdb641d9
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-21-memory-capsule-evolution-design · 6. 最小改动接线点(soul agent 实证·2-3 处·都在 compass 客户端)
## 6. 最小改动接线点(soul agent 实证·2-3 处·都在 compass 客户端)
1. **`compass_fleet_memory.py:write_learning`** — W1 写回附 verdict 元数据(reward/score/bucket/source)作质量等级标签。已只在 reward=1.0 触发,加标签即可。**= 晋升门。**
2. **`compass_fleet_memory.py:compass_recall_pits`** — recall 加质量过滤(只召回高质胶囊)+ **family 键统一为 `bench_family`**(顺带修今天发现的不一致)。**= 喂高质胶囊 + 键对齐。**
3. (可选)serving 侧同 `bench_family` 下新胶囊晋升时对旧低分衰减/淘汰。

**family 键不一致根因(已定位)**:`task_family`(claim 池键·恒 `distillation_fuel`)vs `bench_family`(复利键·真实族名 `requests`/`kernelbench-stump`)被混用在同一形参。**canonical 复利键 = `bench_family`**,W1/W2 都只用它。修复点 = `compass_fleet_memory` 或 V5 的 `build_fuel_desc`。
