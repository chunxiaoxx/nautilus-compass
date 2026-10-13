---
name: orgfuel-ORGG-db6f1a440233704f-2516ed34b7
description: "判读档判例 NACRE_WHITEPAPER_V1 · 第二章 三支柱(全部实证在档) ## 第二章 三支柱(全部实证在"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-db6f1a440233704f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 NACRE_WHITEPAPER_V1 · 第二章 三支柱(全部实证在档)
## 第二章 三支柱(全部实证在档)

### 2.1 压缩:判分知识 → 小权重

- 1454 条判例语料 → 1.7B 基座 LoRA 判分器,**主判精度 88.51%,三门判据(J1 精度/J2 校准/J7 泛化)全绿** [实测,2026-09-30,P2 milestone];
- 三态 verbalizer 天然校准:verbalizer 层即输出分布,无事后温度调节 [实测];
- 反例基线:纯 prompt 工程(66.2%)+架构天花板实证 [实测,判分器语料 1454 档案]——压缩进权重是量级差异,不是增量优化;
- 结论:判分知识可以、且只能通过参数压缩获得产品级精度。

### 2.2 验证:三态不猜 + 证据分层

- 每条结论性陈述强制标注 [实测]/[推断]/[不可验],[推断] 必带 upgrade_path——制度正本 docs/metering/JUDGING_EVIDENCE_TIERS_20261003.md;
- 市场侧证据:数据交易市场无公认验收标准(一级市场调研:模厂只能抽检,后验同批数据两家结果不同 [实测,DATA_VENDOR_BENCHMARK_SERIES 档])——三态判定就是可购买的"验收";
- 运营侧证据:G1-full 预注册门槛未过→未证实分支成立照报收束(配对 McNemar p=0.8126) [实测,函 9791];L3 Round 1 双臂格式缺陷照报+归因勘误留痕 [实测,函 9895]——**负结果是纪律强度的证据,不是失败**。

### 2.3 因果倒置:判例 → 燃料 → delta → registry

- P3 增量管线六段:白名单门→domain 门槛→增量 LoRA→REG-100 金标
