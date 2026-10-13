---
name: orgfuel-ORGH-025bc3a3559b37ea-b588edf576
description: "commit 74c732457e6f 2026-06-24 plan(benchmark): compass 记忆 b"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-025bc3a3559b37ea
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 74c732457e6f 2026-06-24
plan(benchmark): compass 记忆 benchmark 方案 — 把价值变数字(B1 价值门闭合)
阶段1 内部A/B(复用 eval_recall.py 加 --mode 开关·D0 flat/D1+PoI/D2+tier/D3+Gemini·MRR/P@k 逐组delta)=最快·dogfood。
阶段2 外部 LongMemEval/LoCoMo 对标 leaderboard=对外展示。
诚实原则:D2-D0≈0 就老实说 lifecycle 没用·绝不编分。真跑留 fresh session(R3)。
