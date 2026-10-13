---
name: orgfuel-ORGH-629e5fc68034384e-e549a8a80b
description: "commit 1dd274f0170a 2026-06-24 feat(lifecycle): wire access "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-629e5fc68034384e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1dd274f0170a 2026-06-24
feat(lifecycle): wire access axis (reinforce_count) into tier_promotion_driver
Closes the LLM-WIKI2 gap: reinforce_count accumulated (access events) but never
drove tier promotion. Driver now runs two companion axes per file — impact
(cumulative_impact, existing) then access fallback (reinforce_count via canonical
recall.promote_lifecycle_tier, rising 1/5/20_access thresholds, promote-only,
naturally idempotent). 6 new TDD + 11 existing driver tests green (35 total).

Honest scope: built+tested LOCAL only. NOT deployed to box (gated). Local corpus
reinforce is ~all 0 (accrues on box daemon via fleet recall), so this de-sparsifies
the box 9720 corpus over time, not the local benchmark.
