---
name: orgfuel-ORGG-d3d35818c7d58fc8-5f6f21ddd7
description: "判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 四、风险与回滚 ## 四、风险与回滚  "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-d3d35818c7d58fc8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 MACMINI_MIGRATION_PLAN_20261011 · 四、风险与回滚
## 四、风险与回滚

| 风险 | 概率 | 回滚 |
|---|---|---|
| Mac mini bash 兼容 | 低(brew bash 5) | 回 Windows |
| Python 包版本冲突 | 中(pyenv 隔离) | 回 Windows |
| BGE 模型 MPS 不支持 | 中(fallback CPU) | 判读走 A100 |
| 记忆文件格式差异 | 低(纯 JSON/MD) | 逐文件验证 |
| 网络环境差异 | 低(Mac mini 同局域网) | — |
