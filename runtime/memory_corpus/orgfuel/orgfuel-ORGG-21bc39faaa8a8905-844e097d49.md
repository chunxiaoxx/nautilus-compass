---
name: orgfuel-ORGG-21bc39faaa8a8905-844e097d49
description: "判读档判例 2026-09-22-assay-head-charter · 五 · 分阶段(与现有里程碑挂钩) ## 五"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-21bc39faaa8a8905
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-09-22-assay-head-charter · 五 · 分阶段(与现有里程碑挂钩)
## 五 · 分阶段(与现有里程碑挂钩)

**Phase 0(现在-10/26):zero-shot baseline**
用 hosted Jev 直接当 pre-verdict(不改权重):输入=题卷描述(state=diff 摘要,
question=「will this pass tests?」)。零训练成本,出一致性读数。**这不需要任何
GPU,本周可做**。

**Phase 1(M2 后):SFT 冷启动**
语料 ≥2,000 行时,LoRA 微调 0.6B(参考 NanoJev 训练配方,GPU 短租半天)。
产出=assay-head-v0.1,部署为 MCP 工具(assay_pre_verdict)。

**Phase 2(M3 后):RLCD 校准精调**
用校准损失精调(CE→Brier 渐进),目标是 ECE ≤0.05(预筛不需要 0.01,边缘
自然走人工)。**成本不对称加权**在此步引入。

**Phase 3(远期):在线学习**
分级判分试点产生的新 verdict 实时回流=持续校准(信任即订阅的内部版)。
