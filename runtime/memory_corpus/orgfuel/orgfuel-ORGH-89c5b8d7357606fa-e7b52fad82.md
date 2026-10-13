---
name: orgfuel-ORGH-89c5b8d7357606fa-e7b52fad82
description: "commit 03bc23669dfd 2026-05-08 paper2 §6.5: cross-judge with"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-89c5b8d7357606fa
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 03bc23669dfd 2026-05-08
paper2 §6.5: cross-judge with Gemini 2.5 Pro · honest 28%/42% spread
Ran scripts/cross_judge_em_gemini_vertex.py on a stratified n=100
sub-sample of em_bge_v3_per_question.jsonl using Gemini 2.5 Pro via
Vertex AI (different vendor + different training data + different
judge calibration than the DeepSeek V4-flash answerer-judge stack).

Result: gemini_acc 28% vs deepseek_acc 42% on the same 100 questions,
Cohen kappa = 0.70 (substantial), 14 disagreements perfectly asymmetric
(DS=Y/Gemini=N), zero in the reverse direction.

Manual inspection of 14 disagreements shows BOTH judges have systematic
biases, not one-uniformly-correct:
  - V4-flash over-permits: scored empty/truncated preds as CORRECT (4 cases)
  - Gemini over-strict: scored "answer + extra context" 
