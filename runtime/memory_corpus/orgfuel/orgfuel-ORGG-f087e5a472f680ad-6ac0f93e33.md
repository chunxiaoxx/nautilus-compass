---
name: orgfuel-ORGG-f087e5a472f680ad-6ac0f93e33
description: "判读档判例 METRICS_DIALECTIC_SYNC_20261001 · 辩证结论：合流 C，分治 V（非"同一度"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-f087e5a472f680ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 METRICS_DIALECTIC_SYNC_20261001 · 辩证结论：合流 C，分治 V（非"同一度量衡两种参数化"）
## 辩证结论：合流 C，分治 V（非"同一度量衡两种参数化"）

**为什么不合流**：乘法 I_eff = C × V 中的 V 是**覆盖率**（越大越好），除法 η = C/V 中的 V 是**成本**（越小越好）——两者互反。覆盖 80%→95% 但时延翻三倍时，I_eff 说变好、η 说变坏——两个判断都对，因为它们不是一回事。写成"同一度量衡"则审稿人必问"到底改进还是退步"。

**定稿结构**：
- **I_eff = C × V⁺**（V⁺=覆盖率）→ 论文 3 世界观度量衡（总量）；可证伪性在退化点（空环 V⁺=0 / 盲区 V⁺∝C）
- **η = C / V⁻**（V⁻=成本 FLOPs/时延）→ 工程优化目标（效率）；死刑条款 P-CV-1/P-CV-2 只挂这里
- **C 合流双轨**：主=描述长度比（审计/对外），辅=有效秩（几何/对内）
- **V 分治**：V⁺=Σαwca（覆盖×准确×真值加权）与 V⁻=flops+time，两符号永不混用
- 各自独立证伪：η 死了不拖 I_eff，I_eff 活着不让 η 诈尸
