---
name: orgfuel-ORGH-bff98df205cf8ea0-342d0e8fb3
description: "commit 9f11825c8685 2026-05-21 feat(bench): Colab T4 runner "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-bff98df205cf8ea0
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9f11825c8685 2026-05-21
feat(bench): Colab T4 runner for LongMemEval-S accuracy benchmark
Adds bench/colab_longmemeval.ipynb + COLAB_INSTRUCTIONS.md so the full
500-question accuracy benchmark can be reproduced on Google Colab's free
T4 GPU. ~6-10h walltime.

Pipeline matches the v0.8 baseline (5/04 · 56.6% with GPT-4o judge):
  BGE-m3 dense top-50 → bge-reranker-v2-m3 rerank top-5 → Gemini Flash
  subject answer → Gemini Flash judge verdict.

T4 hosted on Tencent (43.173.164.32) was reclaimed (spot · 16d old memory
unreachable today). Colab path lets the bench run continue without
needing a paid GPU rebuild.

Resume support: checkpoints every 5 questions to results JSON · survives
Colab idle/12h disconnects (re-run cell 6, picks up from checkpoint).

Uses nautilus-compass==2.0.0 fr
