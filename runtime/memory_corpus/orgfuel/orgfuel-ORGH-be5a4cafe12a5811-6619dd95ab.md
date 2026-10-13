---
name: orgfuel-ORGH-be5a4cafe12a5811-6619dd95ab
description: "commit 6db8f31a6c77 2026-05-06 paper §6.5 · 5-topic n=500 fi"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-be5a4cafe12a5811
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6db8f31a6c77 2026-05-06
paper §6.5 · 5-topic n=500 final · compass 41.0% e2e on EverMemBench
Replaces n=100 single-topic preliminary with n=500 cross-topic final:

  recall@20      94.8%  (BM25 baseline 38.1% · +56.7 pts dense+rerank)
  e2e accuracy   41.0%

Per-topic: 01=40 · 02=38 · 03=42 · 04=45 · 05=40 (CV 6%)

Position vs paper Table 4 (GPT-4.1-mini · 9-subtask Avg):
  Full Context (no mem) 37.44 · MemoBase 34.27 · Mem0 37.09
  Zep 39.97 ← compass +1.0
  compass 41.00 ← independent · fills EverCore gap
  MemOS 42.55 ← compass -1.5

Cost: 76 min wall · $1.50 (DeepSeek API)
Hardware: single T4 · CPU-friendly (10K msgs encode in 20s)

Honest framing throughout:
  - "compass between Zep and MemOS" (no SOTA claim)
  - V4-flash vs GPT-4.1-mini caveat documented
  - Profile Understand
