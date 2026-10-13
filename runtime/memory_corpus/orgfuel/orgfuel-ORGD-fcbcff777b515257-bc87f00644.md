---
name: orgfuel-ORGD-fcbcff777b515257-bc87f00644
description: "[# 五个战场各测什么] | 战场 | 性质 | 回答的问题 | 结果 | |---|---|---|---| | LM"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-fcbcff777b515257
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[# 五个战场各测什么] | 战场 | 性质 | 回答的问题 | 结果 |
|---|---|---|---|
| LME-S e2e 500 题 | 自建 harness 主场 | 方法效应 | 42.6 → 75.4 |
| 检索对打 mem0 | 同题同判据 | 相对优势 | P@1 0.890 vs 0.774 |
| LOCOMO-10(n=1986) | 客场换数据集 | 泛化 | P@1 0.644 vs 0.592 |
| EverMemBench | 第三方公开榜 | 防自吹 | 44.4-47.3 vs Mem0 37.09 |
| LME-V2(451 题) | 上游官方基准 | 社区可比 | 40.0 / 38.4(untuned 19.6/12.8) |
