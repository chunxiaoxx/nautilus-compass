---
name: orgfuel-ORGD-df8f8fc3a960cdd8-9eba090150
description: "[## 2. 七算子仲裁化映射(算子层×仲裁层合流)] | 算子 | 仲裁机制 | 状态 | |---|---|---|"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-df8f8fc3a960cdd8
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 2. 七算子仲裁化映射(算子层×仲裁层合流)] | 算子 | 仲裁机制 | 状态 |
|---|---|---|
| 写 | 写入门:fact_status(dirty bit)+写即声明(claims 入包) | #48 9/15 |
| 读 | provenance 召回:带可验回执的记忆优先 | Phase 2 |
| 选 | 门控=仲裁执行点(drift/QC/policy) | 在产 |
| 合并 | **冲突消解仲裁**:矛盾记忆按 验证历史×新鲜度×fact_status 排序,非时间覆盖 | Phase 2 |
| 忘 | **置信度经济(记忆的 PoS)**:衰减从时间函数升级为**共识函数**——被复算支撑的增值,无支撑的贬值 | Phase 2(schema 的 decay_rate 已在,measured) |
| 组合 | 推导过程入链,组合产物可审计 | Phase 3 |
| 评估 | 即 L2 共识本身 | paper2 论文级 |
