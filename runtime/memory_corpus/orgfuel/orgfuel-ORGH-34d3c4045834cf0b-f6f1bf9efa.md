---
name: orgfuel-ORGH-34d3c4045834cf0b-f6f1bf9efa
description: "commit 9a1edea3b1d8 2026-09-22 feat(jev-trust): 域3 embodied-"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-34d3c4045834cf0b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9a1edea3b1d8 2026-09-22
feat(jev-trust): 域3 embodied-qc-labeling 闭环——C=0.689 首个 DISCOUNT 域
按书面规范标注关节角序列:n=120 acc 50%/Brier 0.206/ECE 0.311/
C=0.689→DISCOUNT(三域梯度 0.953→0.866→0.689)。错误结构=全 yes
策略(召回 100%/精确率 50%/假阳性率 100%):正例含近阈尖峰全中,
负例全误报,置信 0.6 档占半——与 mini-DCR email-choice 50%@91%
同构=分类面结构性弱点。对标注管线含义:Jev QC 建议不可直接执行;
jev-trust 的 DISCOUNT/有效置信机制首次在第三方域触发设计作用。
独立手算四指标精确一致,验签 VALID,判据全绿,待非实现者复算。

Co-Authored-By: Claude <noreply@anthropic.com>
