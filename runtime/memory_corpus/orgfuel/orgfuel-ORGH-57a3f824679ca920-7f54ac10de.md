---
name: orgfuel-ORGH-57a3f824679ca920-7f54ac10de
description: "工具决策记录 migrate_from_v5.py compass v0.9 · v5-memory → compass"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-57a3f824679ca920
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 migrate_from_v5.py
compass v0.9 · v5-memory → compass observations migration · #8 fusion.

Reads ~/v5-memory/ (Nautilus V5/V6 自家 memory protocol if exists) and converts
each entry into a compass session_*.md file with proper frontmatter.

Usage:
  python migrate_from_v5.py [--dry-run] [--source ~/v5-memory] [--target <project>]

Default behavior:
  · source: ~/v5-memory (or env COMPASS_V5_MEMORY_DIR)
  · target: ~/.claude/projects/C--Users-chunx/memory/imported_v5/
  · dry-run: show what would migrate without writing

Schema mapping (best-effort · v5-memory exact format unknown · we infer):
  v5 entry fields (likely)              compass frontmatter
  ----------------------------------    --------------------
  title / subject / topic            →  name
  summary / description      
