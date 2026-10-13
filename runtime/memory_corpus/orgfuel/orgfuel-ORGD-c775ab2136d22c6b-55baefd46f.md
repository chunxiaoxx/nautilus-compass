---
name: orgfuel-ORGD-c775ab2136d22c6b-55baefd46f
description: "[## 1. 四命令(CLI)] | 命令 | 干什么 | 产出 | |---|---|---| | `vp build"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-c775ab2136d22c6b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 1. 四命令(CLI)] | 命令 | 干什么 | 产出 |
|---|---|---|
| `vp build <dataset>` | 打包数据集+口径+环境指纹 | verifypack 归档(data+manifest) |
| `vp verify <pack> [--l0-only]` | 两级验证(§2) | PASS/FAIL/PARTIAL + 分层定位(断在哪层) |
| `vp receipt <pack>` | 出回执(§3) | receipt JSON |
| `vp check <receipt>` | 验回执 | 哈希链校验 + 复现命令重跑 + 降采样抽查 |
