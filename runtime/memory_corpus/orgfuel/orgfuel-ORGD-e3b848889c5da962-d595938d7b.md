---
name: orgfuel-ORGD-e3b848889c5da962-d595938d7b
description: "[## 一、与 JEV 架构的关系:上下游,不是同一个东西] - **JEV**=判分数据与证据体系(数据层):判官语料"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-e3b848889c5da962
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 一、与 JEV 架构的关系:上下游,不是同一个东西] - **JEV**=判分数据与证据体系(数据层):判官语料(1454+)、criteria 库、证据三层标注、TrustedJev 域校准仪器——它管"**数据从哪来、可信度怎么标、域适配怎么校准**";
- **NACRE 主线**=消费这些数据训练出的判分模型机制(模型层):压缩(SFT)×验证(三态+判据预注册)×因果倒置(delta registry→再训练)——它管"**模型怎么训、怎么升级、错了怎么回流**";
- **关系**:JEV 是 NACRE 的营养与质检体系。JEV 产好数据→NACRE 吃数据长能力→NACRE 判错产生的勘误又回流 JEV——一条上下游河,不重复造轮子的第一层含义就是:别在 NACRE 里再写一遍 JEV 的数据治理。
