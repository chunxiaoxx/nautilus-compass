---
name: orgfuel-ORGH-6ca728c3c449b06a-e4dcbf05b4
description: "工具决策记录 org_fuel_docs.py ORG-FUEL-V0 docs 源采集抽取器:docs/**/*.md"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6ca728c3c449b06a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 org_fuel_docs.py
ORG-FUEL-V0 docs 源采集抽取器:docs/**/*.md 正本 → 候选判例 JSONL。

抽取规则:正本里带结论+读数/判据/判定的段落块(markdown 表格行、结论行)。
输出:runtime/org_fuel/candidates_docs.jsonl(候选,待 judge 判定)。
