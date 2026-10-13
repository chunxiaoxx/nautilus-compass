---
name: orgfuel-ORGH-c374ecf5d38e8dbf-f253429f90
description: "commit 1f440e3dd9d3 2026-05-08 promo: refresh all 5 outreach"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c374ecf5d38e8dbf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 1f440e3dd9d3 2026-05-08
promo: refresh all 5 outreach docs to v1.0 stable + v3 EverMemBench
Update all forum / outreach / news / PWC drafts to reflect:

1. Version bump 1.0.0-rc2 -> 1.0.0 stable across headers, install
   commands, body text (5 files affected).

2. EverMemBench number: single-run 44.4% expanded to dual-run honest
   reporting:
     Run 1 (2026-05-07, n=500) = 44.4%
     Run 2 (2026-05-08, n=497) = 47.3%
     Cross-run mean = 45.84% (+3.29 pts vs MemOS 42.55)
   Run 2 saw 3 questions skipped on topic 04 due to transient DeepSeek
   5xx errors.

3. PWC submission table extended with Run 1 / Run 2 / Mean rows for
   leaderboard accuracy.

4. PWC challenge-Q&A line updated: 44.4% -> 44.4-47.3% range.

Files: outreach_emails_2026-05-08.md, forum_refresh_2026-05-07.md,
ha
