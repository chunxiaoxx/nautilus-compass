---
name: orgfuel-ORGH-ad471c46558c6490-476adf10db
description: "工具决策记录 cross_judge_analysis.py compass · paper2 · cross-judg"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ad471c46558c6490
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 cross_judge_analysis.py
compass · paper2 · cross-judge agreement analysis.

Compares two LongMemEval-S evaluation runs (same subject · different judge)
to compute self-judge bias.

For paper §6 Limitations · we need:
  · agreement % (same verdict on same question)
  · per-type agreement
  · confusion matrix · where do judges disagree

Usage:
  python tools/cross_judge_analysis.py     --self  .cache/longmemeval_acc_m3_rerank_full_<v0.8_ts>.jsonl     --cross .cache/longmemeval_acc_m3_rerank_full_<crossjudge_ts>.jsonl     --output paper/results/cross_judge_analysis.json

Expected output:
  · overall_agreement: 0.95 → very low self-judge bias (good for paper)
  · overall_agreement: 0.80 → moderate · noted in limitations
  · overall_agreement: <0.70 → significant bias · paper claim weake
