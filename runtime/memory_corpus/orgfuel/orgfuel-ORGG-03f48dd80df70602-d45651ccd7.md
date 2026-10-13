---
name: orgfuel-ORGG-03f48dd80df70602-d45651ccd7
description: "判读档判例 PRECOR_BC_VERDICT_20261007 · 二、结论四条 ## 二、结论四条  1. **部署"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-03f48dd80df70602
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_BC_VERDICT_20261007 · 二、结论四条
## 二、结论四条

1. **部署纪律 v1 定案**:判分器生产部署只允许 **bf16 或 fp16**;int8 差 2 题不过预注册门,照 FAIL 报;int4 禁用;
2. **模板复原正确性独立确认**:bf16 三态 acc 0.8797 与生产评测 0.885 同域(PRECOR 自验证门 0.80 过)——E1 复算所用管线与本次管线同模板族;
3. **精度-一致性阶梯实测成立**:fp16(1.0)≫int8(0.9828)>int4(0.9416)——漂移与量化强度单调,方向与 E1 3B 实验互证;
4. **E1 复算 U 态的归因补强**:判分器对量化敏感是系统性现象(两代模型实测),软维度门单列(PRECOR-C 产数)更必要。
