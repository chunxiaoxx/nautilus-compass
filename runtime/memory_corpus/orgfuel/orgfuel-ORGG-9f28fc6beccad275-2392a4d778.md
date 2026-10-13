---
name: orgfuel-ORGG-9f28fc6beccad275-2392a4d778
description: "判读档判例 PREFOR_JUDGE14B_SMOKE_20261004 · 立项背景 ## 立项背景  - 判官现役 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-9f28fc6beccad275
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PREFOR_JUDGE14B_SMOKE_20261004 · 立项背景
## 立项背景

- 判官现役 = Qwen3-1.7B QLoRA(P2v2,verdict-judge 88.51%,J1/J2/J7 三门绿)。
- 14B 升格路线的唯一务实入口:14B dense QLoRA 在 A100 40G 单卡的管线可行性(smoke)。
- 前提事实:14B=提取器非训练基座(P1 检索头 BGE 82.94% 胜出 14B 67.74%),故本立项仅探判读器升格,不动检索头;2026 旗舰 MoE 化,单 40G 卡大模型在线更新无解。
- 基座:Qwen3-14B(在库 28G,模型库存档 runtime/model_inventory.md);Turbo 重下完成后可作对照,不设门槛不计判据。
