---
name: orgfuel-ORGD-dfe97ea1119e0252-d868455e50
description: "[## 二 · 提案:verdict-judge(动态权重三态判分器)] - 判分器部署后**持续学习**:每条新人工复"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-dfe97ea1119e0252
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 二 · 提案:verdict-judge(动态权重三态判分器)] - 判分器部署后**持续学习**:每条新人工复核/独立复算结果=真值标签 → 在线小步更新(LoRA 增量)
- **上岗门**:新权重必须过回归门(历史 100 条判例零退化)才切换——动态但有闸
- 这是"验证业务本身长出验证引擎"(总纲原句)的实体化:verdict 越多→判分器越准→热路径判得越快→verdict 更多
