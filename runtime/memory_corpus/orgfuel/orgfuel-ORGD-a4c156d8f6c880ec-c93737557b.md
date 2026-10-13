---
name: orgfuel-ORGD-a4c156d8f6c880ec-c93737557b
description: "[## 升级 2 · 新节:Verification as Reflex(验证即反射)] - **L0 反射层**:验证"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-a4c156d8f6c880ec
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 升级 2 · 新节:Verification as Reflex(验证即反射)] - **L0 反射层**:验证器嵌入写入路径(记忆写入门/训练交付门/外发回执门),延迟预算 30ms 级(实测 P50=30.1ms/P95=42.2ms,吞吐 118 items/s)
- **L1 记忆层**:判定→语料→重训闭环;验证经验压进 25.7MB adapter——「智能=压缩×验证」的物理实现是**验证自身的再压缩**
- **L2 进化层**:真值三级采样(T1 传感器/T2 用户裁决/T3 机械规则)+分域 adapter;反自指护栏(自训只限小验证器,奖励只锚可复算真值)
