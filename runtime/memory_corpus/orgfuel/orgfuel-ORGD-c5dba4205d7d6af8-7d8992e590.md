---
name: orgfuel-ORGD-c5dba4205d7d6af8-7d8992e590
description: "[## 实验 B:量化漂移矩阵(部署精度纪律)] - **矩阵**:精度 {bf16, fp16, int8(bitsa"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-c5dba4205d7d6af8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 实验 B:量化漂移矩阵(部署精度纪律)] - **矩阵**:精度 {bf16, fp16, int8(bitsandbytes LLM.int8), int4(nf4 双量化)} × 解码 {greedy, T=0.3/top_p=0.9} = 8 配置;bf16+greedy 为基线锚。
- **读数**:每配置报 ①与基线判定一致率(主判维度 label)②J1 类二值 acc ③翻转题清单(sha16 锚随件)。
- **判门(冻结)**:某精度可进入生产部署 ⟺ 该精度 greedy 对 bf16 greedy 一致率 **≥99%**(292 题容错 ≤2 题);T=0.3 读数仅披露不判门。**预期假设(预注册)**:int8≥99% 过门、int4 显著不过(参考 E1 复算 4bit 0.8173 漂移信号);假设证伪照报。
- **产出**:《判分器部署精度纪律》判定表+NACRE 白皮书 §3.5 部署形态实证素材。
