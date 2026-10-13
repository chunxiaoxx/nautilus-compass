---
name: orgfuel-ORGH-bc43262e8c4c03df-a77d49d0dc
description: "commit 32040bbc07f3 2026-06-08 feat(fde): AutoLab A-cluster "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-bc43262e8c4c03df
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 32040bbc07f3 2026-06-08
feat(fde): AutoLab A-cluster eval + avoidance-corpus adapter
eval: 官方 task 文件编译+计时打分 (log-stretch reward)·fence-strip 剥 markdown 围栏·{reward,feedback} 契约·feedback 末段=grounding fail_reason。
corpus: round-N eval reward → 可检索避坑语料 + 批次平衡警示原子 (correctness-first 课自动编码)。
RSI grounded-retrieval 首验 (V5 radix_sort 2-arm) 生产验证: Δmean +0.013·p≈0.013·可靠性 92vs69%。
