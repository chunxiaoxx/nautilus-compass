---
name: orgfuel-ORGG-ffd3299921fa6ddb-7f42af0a37
description: "判读档判例 2026-06-22-flywheel-convergence-design · 1. 有机耦合图(齿轮 ="
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-ffd3299921fa6ddb
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-06-22-flywheel-convergence-design · 1. 有机耦合图(齿轮 = 注册 agent + 常驻服务;对话框 = 外圈建造者)
## 1. 有机耦合图(齿轮 = 注册 agent + 常驻服务;对话框 = 外圈建造者)

```
┌──────────── 系统层(自转传动链 · 不依赖对话框 · §0-ARCH)────────────┐
│  ① 燃料源/出题      ② 解题 producer      ③ 验证 verifier            │
│  dispatch+mint   →  注册 agent(整数id) →  soul-scorer 服务          │
│  (FDE题/auto-mint/  (V5 daemon=9000002    (pass@k门/is_substantive) │
│   SWE·KernelBench)   已注册)                  │                     │
│      ▲                                        ▼                     │
│  ⑦ 更强 solver    ⑥ 回灌 grounding       ④ 结算/账本               │
│  蒸馏→新producer ← compass recall回灌 ←  平台 settle +              │
│  (从未跑)          (W2·LIVE)             capability_evolution(整数) │
│                        ▲                      │                  
