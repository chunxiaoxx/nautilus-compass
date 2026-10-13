---
name: orgfuel-ORGD-8a3da5650d23ce7c-265e80ff54
description: "[## 三 · 根治四刀 v3.2(结构性,非调参)] - cache 值 (mtime, vec) → vec=np."
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-8a3da5650d23ce7c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 三 · 根治四刀 v3.2(结构性,非调参)] - cache 值 (mtime, vec) → vec=np.float32[1024];旧 pkl 读入时惰性转换(一次性);cosine 改 np.dot(顺带 5-10x 提速)。
- 效果:驻留内存降 8x——10 项目全驻 ~6.4G→**<1.2G**。LRU 基本不再触发,**churn 根因消失**。
