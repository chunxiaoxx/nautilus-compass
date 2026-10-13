---
name: orgfuel-ORGH-93e6a90a4d738ae5-6f4b9234f6
description: "工具决策记录 migrate_to_sqlite.py compass v0.9.1 · migrate file-ba"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-93e6a90a4d738ae5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

工具决策记录 migrate_to_sqlite.py
compass v0.9.1 · migrate file-based memory/*.md → sqlite observations table.

Reads ~/.claude/projects/<project>/memory/*.md and inserts rows into
the v0.9 observations table. Used for one-time migration when a user
upgrades from v0.7.2 / v0.8 to v0.9.

Schema target: see paper/V09_USER_SCHEMA.md / paper/V10_FINAL_SPEC.md §3.

Usage:
  python tools/migrate_to_sqlite.py [--dry-run] [--user-id u_xxx]                                      [--db /var/lib/compass/compass.db]                                      [--projects ~/.claude/projects]

Behavior:
  · Reads all session_*.md and existing memory/*.md files
  · Parses YAML frontmatter (name · description · type · concept · drift · drift_signals)
  · Generates obs_id from filename hash
  · Generates agent_id from fr
