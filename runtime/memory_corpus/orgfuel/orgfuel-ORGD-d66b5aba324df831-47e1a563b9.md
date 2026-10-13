---
name: orgfuel-ORGD-d66b5aba324df831-47e1a563b9
description: "[### L2 进化层——动态权重与 SSI 对接口] - **真值三级采样**(T1 传感器/T2 用户/T3 规则)"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-d66b5aba324df831
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[### L2 进化层——动态权重与 SSI 对接口] - **真值三级采样**(T1 传感器/T2 用户/T3 规则)→判分器按级加权训练,防混权污染
- **分域进化**:per-domain adapter(本次 CV 域测量=第一个候选域)——"每个域一个反射,共享一个脊柱(底模)"
- **SSI 上游卡位**(Ilya 9/22 动向:持续学习不冻权重+digital value function 需真值供给):我们的 T2 流(user_verdict)+带签名的 verdict 语料=他们缺的真值燃料。**反自指护栏**(9/16 定谳):自训只限小判分器,奖励只锚复算真值——组织不给自己当裁判发大模型
