---
name: session_audit
status: codified
version: 1.0.0
tier: episodic
description: Scan project memory · age distribution + ungrouped count (L1 build readiness) + per-namespace entity stats · NO LLM.
inputs:
  - project (str, optional): project slug · defaults to active
  - mem_dir (path, optional): override mem_dir resolution
  - lookback_days (int, default 30): age bucketing threshold
outputs:
  - total_sessions
  - age_distribution (fresh / recent / aged · session counts per bucket)
  - ungrouped_count (sessions not covered by L1 index)
  - entity_namespace_stats (counts per ns: wiki/people/companies/concepts/sessions)
---

# session_audit

Pre-L1-build readiness check · before triggering `cli_self_evolve --all`,
this skill tells you which projects have enough ungrouped sessions to
make L1 collapse worthwhile (threshold default 3 in self_evolve).

## When to use

- Pre-L1-build: which projects should I run self_evolve on?
- Memory health: are sessions piling up uncollapsed?
- Entity graph: how many `[[ns/name]]` links across the corpus?

## Why codified

- 3 distinct call-sites already (CLI / self_evolve / paper3 metrics)
- Single pure-Python scan · O(N) over .md files · deterministic
- Reused by lifecycle_report internally (DRY)
