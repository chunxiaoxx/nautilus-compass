---
name: orgfuel-ORGH-e2993cff761c0964-46cb94e4b2
description: "commit ea9b8f8e2101 2026-05-21 ﻿feat(v1.7.1): S_GBrain modul"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e2993cff761c0964
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ea9b8f8e2101 2026-05-21
﻿feat(v1.7.1): S_GBrain module 2 · skills_pkg/skill_registry.py · state machine + promotion
skills_pkg/skill_registry.py · ~150 LOC
  - load_registry / save_registry / rebuild_registry · _skill_registry.json maintenance
  - promote · strict state machine (concept→prototype→codified→retired)
  - PROMOTE_FROM_TO / DEMOTE_FROM_TO edge tables
  - list_by_status · directory-based enumeration
  - increment_review_count · frontmatter mutation + registry refresh
  - codified_at timestamp auto-populated on promotion
  - NO LLM · JSON state machine + filesystem rename only

tests/test_skill_registry.py · 11/11 pass

Refs: paper/SPEC_GBRAIN_SKILLPACK_REWRITE.md section 3
Next: skill_evaluator + skill_cron_emitter + cli_skill (3 modules · finish S_GBrain)
