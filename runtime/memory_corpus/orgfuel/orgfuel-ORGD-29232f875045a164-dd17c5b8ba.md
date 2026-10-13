---
name: orgfuel-ORGD-29232f875045a164-dd17c5b8ba
description: "[## 正文] - LongMemEval-S 检索 P@1:0.890(我们)vs 0.774(mem0 2.0.19"
metadata:
  type: reference
  source: org_fuel:docs
  pf_id: ORGD-29232f875045a164
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

[## 正文] - LongMemEval-S 检索 P@1:0.890(我们)vs 0.774(mem0 2.0.19 复现,同题同判据,各用默认嵌入)
- LongMemEval-S 端到端 500 题:42.6% → 75.4%(读取端路由的功劳;剔除 71 道判官故障题是 81.6%,双口径披露)
- 检索延迟 p95 0.34-0.80s(LLM controller 方案 26.9s)
- mem0 官方自报 94.4%,口径与我们不可比(harness/判官/被测模型都不同),不拉踩,说清楚就好
