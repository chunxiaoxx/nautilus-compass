---
name: orgfuel-ORGH-c67a78a880ad668e-59b59584d1
description: "commit daad2e8f8ea9 2026-06-23 feat(lifecycle): reinforce_co"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c67a78a880ad668e
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit daad2e8f8ea9 2026-06-23
feat(lifecycle): reinforce_count +1 on recall hit (access-driven promotion)
Phase 1 Task 1 · close the LLM-WIKI2 access loop. recall.reinforce_on_recall_hit
bumps each recalled file's frontmatter reinforce_count (Rule A access event ·
the input promote_lifecycle_tier reads to advance the tier ladder). Wired as a
guarded, never-breaks-recall block on the daemon recall path (disable via
COMPASS_NO_REINFORCE=1). DRY frontmatter rewrite mirrors tier_promotion_driver.
+3 tests (bump 0to1 / accumulate+insert-missing / safe-on-bad-input). 22 pytest pass.
