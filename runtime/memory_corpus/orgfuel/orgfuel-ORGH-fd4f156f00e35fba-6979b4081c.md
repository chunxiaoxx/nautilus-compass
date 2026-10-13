---
name: orgfuel-ORGH-fd4f156f00e35fba-6979b4081c
description: "commit 54476bd80604 2026-05-21 ﻿docs(v1.7.1): S_GBrain skill"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-fd4f156f00e35fba
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 54476bd80604 2026-05-21
﻿docs(v1.7.1): S_GBrain skillpack SPEC + RAID dispatch batch plan
Closing the trio of design specs and preparing for platform agent dispatch
instead of solo-shipping the implementation.

paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md (~370 lines)
- GBrain 5-step skill cycle (concept/prototype/evaluate/codify/cron)
- Python clean-room rewrite · NO fork of MIT TypeScript source
- 5 modules ~300 LOC · 1-2 week sprint
- 10 smoke cases + resource budget enforcement (LLM-free at ingest)
- SKILL.md frontmatter schema + handler.py contract
- Storage layout: skills/{concepts,prototypes,codified,retired}/
- Companion to SPEC_GBRAIN_ADAPTER.md (framing) - this is implementation

paper/RAID_DISPATCH_BATCH_PLAN.md (~290 lines)
- 16 bounty manifest covering S3 (5) + S4 (6) + S_GBr
