---
name: orgfuel-ORGG-6f4c0bd2a1088b4c-17d050bfce
description: "判读档判例 PRECOR_ORG_FUEL_V0_20261007 · 二、流水线(v0 单框,半自动) ## 二、流水"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-6f4c0bd2a1088b4c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 PRECOR_ORG_FUEL_V0_20261007 · 二、流水线(v0 单框,半自动)
## 二、流水线(v0 单框,半自动)

1. **采集**:queue.md 轮次条目+session 记忆条目(111 条)解析为事件;
2. **抽取**:规则抽"判断/动作+结果"对(含:实验判门读数/勘误/审计 finding/崩溃修复/决策后果);
3. **判定**:每候选经 NACRE judge(实例 v1)三态判"是否构成有效判例";抽 10% 人工复检;
4. **入册**:verdict=有效 且 anchor∈{L0,L1} → delta registry(fuel_eligible=true)+corpus_pipeline 计数。
