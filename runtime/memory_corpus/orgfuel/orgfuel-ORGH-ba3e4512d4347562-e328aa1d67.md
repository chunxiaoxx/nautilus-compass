---
name: orgfuel-ORGH-ba3e4512d4347562-e328aa1d67
description: "commit 553a22a89b19 2026-05-21 ﻿feat(v1.7.1): S_GBrain modul"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-ba3e4512d4347562
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 553a22a89b19 2026-05-21
﻿feat(v1.7.1): S_GBrain modules 3-5 · evaluator + cron_emitter + CLI (V2.0 COMPLETE)
skills_pkg/skill_evaluator.py · ~115 LOC
  - run_smoke · subprocess pytest with timeout enforcement
  - SkillBudgetExceeded · resource_budget violation exception
  - evaluate · run_smoke + frontmatter update (last_eval_at/pass) + review_count bump
  - NO LLM · pure subprocess

skills_pkg/skill_cron_emitter.py · ~115 LOC
  - validate_crontab · strict regex (rejects shell injection · ;&|$` etc)
  - emit_cron_script · safe bash wrapper
  - emit_crontab_line · standard crontab format
  - emit_for_skill · one-shot orchestrator

bin/cli_skill.py · ~135 LOC argparse CLI
  - compass-mcp skill init <name>
  - compass-mcp skill list --status <status>
  - compass-mcp skill promote <name
