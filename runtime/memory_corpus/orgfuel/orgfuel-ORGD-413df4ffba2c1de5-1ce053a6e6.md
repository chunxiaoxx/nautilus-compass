---
name: orgfuel-ORGD-413df4ffba2c1de5-1ce053a6e6
description: "[### 3.1 实验设计] - **B 臂(基线)= 8/29 全量 evidence,不重跑**:同判据(subje"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-413df4ffba2c1de5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 3.1 实验设计] - **B 臂(基线)= 8/29 全量 evidence,不重跑**:同判据(subject=doubao-seed-2-0-pro-260215 / judge=glm-5.3-flash / 同 retrieval 配置),500 题分型数字即为基线。
- **A 臂(摘要层)= 只跑三短板型 322 题**(ms 133 + tr 133 + ssa 56),ZMM_SUMMARY_LAYER=1,其余 env 与 8/29 全量一致。
- 高分三型不跑不比(未改动,理论字节不变;全量时顺带回归验证)。
