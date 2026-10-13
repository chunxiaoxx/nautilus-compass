---
name: orgfuel-ORGH-db4ed3c6aad01fab-e5a40eed94
description: "工具决策记录 verdict_corpus_exporter.py verdict_corpus_exporter · "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-db4ed3c6aad01fab
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 verdict_corpus_exporter.py
verdict_corpus_exporter · SSI×Jev 提案 P1:verdict→训练集聚合器 v0。

目标(SSI_JEV_DYNAMIC_JUDGE_PROPOSAL_20260930.md P1):把仓内散落的 verdict
工件聚合成统一训练集格式,喂三态判分器(pass/fail/insufficient_evidence)。

纪律:
  · 只导出,不改判;带真值标签(label_origin 可溯)才进 train_set,
    其余诚实进 unlabelled 池——不拿判分器自报冒充标签。
  · 每条带 source 路径 + 内容 hash(可溯源,复算可对账)。
  · 输出 manifest:计数、源清单、schema 说明(报数纪律:如实报数)。

用法:python tools/verdict_corpus_exporter.py [--out runtime/verdict_corpus]
