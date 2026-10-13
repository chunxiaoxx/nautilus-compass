---
name: orgfuel-ORGG-b0f8de1a11d1850d-10615f7652
description: "判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 三 · 路线图(挂总纲 "
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-b0f8de1a11d1850d
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930 · 三 · 路线图(挂总纲 W3-W4)
## 三 · 路线图(挂总纲 W3-W4)

| 阶段 | 内容 | 判据 |
|---|---|---|
| P1 语料 | W42 verdict 聚合器:verdict 库→训练集导出器(判因/三态/签名元数据) | ≥500 条带标签 |
| P2 基线 | Laya 决策头三态 LoRA(本地 GPU 或 4090 短租) | held-out 三态 acc≥85%,校准 ECE≤0.1 |
| P3 动态 | 在线更新管道(新 verdict→LoRA 增量→回归门→上岗) | 回归门 20 连绿 |
| P4 装载 | compass 写入门(灰度 10%)→ assay G1 腿 → F15 第一腿 | 各点对照人审一致率≥90% |
