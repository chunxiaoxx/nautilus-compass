---
name: orgfuel-ORGD-490b4b99cac5670b-1bb33762bb
description: "[## M1 · 迁移底座(无悔 · 8770 退役 9/15 前后均可动工)] - [ ] **T1 多用户模型转正*"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-490b4b99cac5670b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## M1 · 迁移底座(无悔 · 8770 退役 9/15 前后均可动工)] - [ ] **T1 多用户模型转正**:v0.9 的 users/agents/observations(user_id 外键)沉淀为 8097 正式服务的数据 schema。判据:建表 + 建用户/agent/obs 读写 smoke 通过。
- [ ] **T2 鉴权层统一**:Bearer JWT(人)+ scoped token(agent)双轨,复用 tokens.json 机制;header-only 身份在代码层禁止(compile 期或启动自检)。判据:五项矩阵(冒充 401/无凭证 401/投毒写 401/合法 JWT 200/不一致 header 401)在新服务重跑全绿。
