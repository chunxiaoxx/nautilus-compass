---
name: orgfuel-ORGD-ff8d35bdc228e8a6-fb5d43019a
description: "[## M2 · 自助闭环(赌注 · 提审通过后)] - [ ] **T3 signup 迁移+加固**:v0.9 si"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-ff8d35bdc228e8a6
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## M2 · 自助闭环(赌注 · 提审通过后)] - [ ] **T3 signup 迁移+加固**:v0.9 signup 端点迁入正式服务,补防枚举(登录失败统一文案)+ 限流。判据:signup→login→JWT→recall 本人空间 e2e。
- [ ] **T4 token 自助管理**:登录用户创建/列表/撤销 agent token,scopes 限定本人 project(服务端强制,不信任客户端传 scope)。判据:四步 e2e = signup → create token → agent 用 token recall 命中 → 撤销后 DENY。
- [ ] **T5 primary project 自动初始化**:新用户首登录自动建 `u_<id>_memory` 空间。判据:新 signup 用户无参数 recall 返回空结果而非 4xx/500。
