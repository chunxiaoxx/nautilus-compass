---
name: orgfuel-ORGG-437d1413f054e0ca-9c408c54b7
description: "判读档判例 2026-06-22-kernelbench-score-fuel-adapter-design · 5. "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-437d1413f054e0ca
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-kernelbench-score-fuel-adapter-design · 5. 测试(TDD)
## 5. 测试(TDD)
- **离线纯函数**(GPU-free·主体):`build_kb_fuel_sample` 字段/类型 · `is_a_class` 镜像对拍(强>弱过 / 双败拒 / strong=0 拒 / 同分拒)· `accumulate_kb_fuel` 幂等取优。
- **seed 验证**(gated GPU):attention 一条端到端 —— 强解 SDPA 1.727x(已验)+ doubao 在 attention 实测(V5 管线跑或 compass GPU 空档)→ 确认 A 类与否(诚实:attention 强解=SDPA 库调用·doubao 可能也会→须实测定;不成则换 stump 技能 leverage 表的真难倒题 p18/p51 algebraic-collapse)。
