---
name: orgfuel-ORGD-9c182e1f257a93ad-5f6f5c7c1f
description: "[### 3.4 评测与升格协议] - 三门判据:J1 主判精度 / J2 校准 / J7 泛化(跨域 held-out"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-9c182e1f257a93ad
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### 3.4 评测与升格协议] - 三门判据:J1 主判精度 / J2 校准 / J7 泛化(跨域 held-out);
- **非实现者复算**:升格决策(1.7B→14B)必须由新鲜会话按预注册判据复算(档 PREFOR_JUDGE14B_UPGRADE,七门,U5 不劣门+U6 显著门);
- 14B 现状:smoke 五门全绿 [实测,10/5];升格复算待执行(判据已冻结,只许更严);
