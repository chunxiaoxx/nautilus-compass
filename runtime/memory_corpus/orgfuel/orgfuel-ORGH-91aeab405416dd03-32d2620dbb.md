---
name: orgfuel-ORGH-91aeab405416dd03-32d2620dbb
description: "commit 7f3821607407 2026-06-24 feat(bench): eval_recall --mo"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-91aeab405416dd03
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 7f3821607407 2026-06-24
feat(bench): eval_recall --mode {flat,poi,tier,gemini} + honest Stage-1 A/B readout
Stage-1 internal A/B benchmark for Goal B lifecycle value (B1 value gate).
TDD rerank() switches per mode (6/6 green). Run on local 1106-memory corpus:
bge-m3 baseline MRR=0.836; lifecycle D1/D2/D3 all Δ MRR +0.000 — corpus has
0 cumulative_impact files + tier 99%% working (metadata absent), NOT proof
lifecycle is useless. Real signal needs box 9720 corpus. Ledger updated honest.
