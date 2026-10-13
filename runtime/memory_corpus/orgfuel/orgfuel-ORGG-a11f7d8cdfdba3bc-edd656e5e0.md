---
name: orgfuel-ORGG-a11f7d8cdfdba3bc-edd656e5e0
description: "判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 10. Def"
metadata:
  type: reference
  source: org_fuel:grain_r4
  pf_id: ORGG-a11f7d8cdfdba3bc
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

判读档判例 2026-08-15-compass-dogfood-mvp-rescue-design · 10. Definition of done
## 10. Definition of done

The rescue is complete when a fresh machine process can:

1. run `nautilus-compass doctor`;
2. run one bounded real coding A/B through `nautilus-compass loop run`;
3. reproduce the signed/read-back decision;
4. show the result without reading source files or development chat;
5. leave Compass runtime flat unless Gate B passes.

Commit counts, test counts, schemas, and worktree activity are supporting
evidence only. They are not the product outcome.
