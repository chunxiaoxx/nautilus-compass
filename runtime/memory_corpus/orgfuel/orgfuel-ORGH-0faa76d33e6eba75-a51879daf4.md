---
name: orgfuel-ORGH-0faa76d33e6eba75-a51879daf4
description: "commit 11e17818db04 2026-06-23 feat(lifecycle): wire tier-we"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-0faa76d33e6eba75
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 11e17818db04 2026-06-23
feat(lifecycle): wire tier-weight into daemon production ranking (Task 4)
The LIVE recall path is daemon.py (its own _rrf_fusion/_rerank_top), so the
recall.py render_v02 wiring only covered the local fallback. Add
_apply_tier_weight_prod after _rerank_top, reusing recall.apply_tier_weight
(DRY). Opt-in COMPASS_PROD_TIER_WEIGHT=1 · default OFF (byte-identical ranking)
· mutually exclusive with cross-encoder rerank (its tuples keep non-monotonic
dense scores, so a score-sort would corrupt rerank order). Verified: tie→higher
tier wins, real cosine gap preserved, OFF=passthrough, both-on=rerank wins.
