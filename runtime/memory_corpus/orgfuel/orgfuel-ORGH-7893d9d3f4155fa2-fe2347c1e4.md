---
name: orgfuel-ORGH-7893d9d3f4155fa2-fe2347c1e4
description: "commit 2f2efefda70f 2026-04-30 paper: behavior steering A/B "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-7893d9d3f4155fa2
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2f2efefda70f 2026-04-30
paper: behavior steering A/B · cross-vendor preliminary evidence
Cross-vendor behavior steering A/B across 6 production LLMs · 6 vendors:
  · gemini-2.5-pro    (Google)     Δ=+0.035  t=+0.67
  · gemini-2.5-flash  (Google)     Δ=-0.034  t=-0.75
  · MiniMax-M2.7      (MiniMax)    Δ=+0.010  t=+0.20
  · doubao-seed-2.0   (ByteDance)  Δ=+0.046  t=+0.89
  · deepseek-v3.2     (DeepSeek)   Δ=+0.029  t=+0.40
  · glm-5.1           (Zhipu)      Δ=-0.025  t=-0.51

Pooled n=120 paired prompts (judge=Moonshot Kimi-k2.6, independent):
  · Net Δ=+0.010, paired t=+0.47 (n.s.)
  · 4/6 subjects net positive
  · 2 negative subjects share highest A baselines (0.85, 0.87) — ceiling effect

Per-axis paired t-test (df=119):
  · verify    Δ=+0.003  t=+0.10 (n.s.)
  · destruct  Δ=-0.0
