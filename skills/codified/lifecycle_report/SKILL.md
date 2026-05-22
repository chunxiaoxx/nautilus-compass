---
name: lifecycle_report
status: codified
version: 1.0.0
tier: episodic
description: Scan project memory for v1.7.1 lifecycle frontmatter · report tier distribution + promotion candidates (reinforce_count >= promote_after) · NO LLM.
inputs:
  - project (str, optional): project slug · defaults to active project
  - mem_dir (path, optional): override · skip project resolution
outputs:
  - tier_distribution (counts by working/episodic/semantic/procedural/unset)
  - decay_status (now_active/expired/never)
  - promotion_candidates (list of {path, current_tier, next_tier, reinforce_count, promote_after})
  - total_memories
---

# lifecycle_report

Aggregate the 4-tier lifecycle schema landed in v1.7.1 across a project's
memory directory. Identifies memories ripe for tier promotion using the
LLM-free deterministic rule: `reinforce_count >= promote_after`.

## When to use

- Pre-promotion audit: which working-tier memories should be promoted to
  episodic? Which episodic to semantic?
- Decay sweep: which memories have hit their `forget_at` ISO8601 timestamp?
- Tier health check: ratio of working/episodic/semantic/procedural memories.

## Why codified

- Frontmatter parsing is stable (won't change · v1.7.1 fixed schema)
- Deterministic output · no LLM
- Used by the 4-tier paradigm validation per paper3 cite (llm-wiki2 fuse)
