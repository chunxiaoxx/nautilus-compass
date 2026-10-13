---
name: orgfuel-ORGG-83aba619e6a0c82f-f14ba529d8
description: "判读档判例 NACRE_WHITEPAPER_V1 · 第三章 技术架构 ## 第三章 技术架构  ### 3.1 基座"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-83aba619e6a0c82f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_WHITEPAPER_V1 · 第三章 技术架构
## 第三章 技术架构

### 3.1 基座与判分头

- 基座:Qwen 系 1.7B(现役)/14B(升格线);判分头=三态 verbalizer(PASS/FAIL/UNVERIFIABLE);
- 不追求通用能力:基座越小,判分知识的密度越高,部署成本越低(热路径 P95 42.2ms@A100、5.9G VRAM [实测,10/1 装前申报档]);

### 3.2 delta registry(sha 棘轮)

- 每个合规 delta 携带 sha16 锚定;registry 只追加不覆写;任何部署可声明"我运行在 registry@vN";
- 复算协议:任何人按公开命令独立复验判定(判例集 16 案全带复算命令 [实测]);

### 3.3 训练管线(P3 六段)

燃料白名单四类(independent_recompute / human_review / official_rule / three_vendor_final)——**判官自产标签永久禁入**(防自指护栏);domain 门槛防单一域过拟合;REG-100 零翻转门。

### 3.4 评测与升格协议

- 三门判据:J1 主判精度 / J2 校准 / J7 泛化(跨域 held-out);
- **非实现者复算**:升格决策(1.7B→14B)必须由新鲜会话按预注册判据复算(档 PREFOR_JUDGE14B_UPGRADE,七门,U5 不劣门+U6 显著门);
- 14B 现状:smoke 五门全绿 [实测,10/5];升格复算待执行(判据已冻结,只许更严);

### 3.5 部署形态

- 热路径 API(A100 实测吞吐 118 条/s);PyPI `nautilus-compass`(assay)3
