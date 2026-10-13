---
name: orgfuel-ORGH-d0cc832361bf497b-fff7183b30
description: "commit 4172bdbd3e66 2026-05-21 ﻿feat(v1.7.1): S_GBrain modul"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-d0cc832361bf497b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 4172bdbd3e66 2026-05-21
﻿feat(v1.7.1): S_GBrain module 1 · skills_pkg/skill_loader.py · dynamic skill import
NEW · nautilus_compass.skills_pkg subpackage (GBrain 5-step cycle clean-room rewrite)

skills_pkg/__init__.py · subpackage marker · storage layout docstring
skills_pkg/skill_loader.py · ~110 LOC
  - parse_skill_md · frontmatter parse + required field validation
  - is_codified_path · security whitelist (only skills/codified/ allowed)
  - load_handler · importlib dynamic load + execute() signature check
  - SkillSchemaError · explicit exception for invalid frontmatter
  - VALID_STATUSES = (concept/prototype/codified/retired)
  - REUSES storage.l1_grouper.parse_session_frontmatter
  - NO LLM · pure schema + importlib

pyproject.toml · add nautilus_compass.skills_pkg
skills/ + s
