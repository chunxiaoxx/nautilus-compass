---
name: orgfuel-ORGH-c40e44f08fbadedf-72ae41902c
description: "commit b1de6aa9b7fb 2026-05-11 ship(ops): #106 v1.4 followup"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-c40e44f08fbadedf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b1de6aa9b7fb 2026-05-11
ship(ops): #106 v1.4 followup · 2 ops files (github channel migration + SMTP template)
#106 audited on cloud · 4 bullets resolved:

| bullet | finding | action |
|---|---|---|
| canonical_url dupe | 0 dupes in metadata | already clean · close |
| unknown_channel github | github (2) + github_issue (3) · same channel split | ship migration SQL |
| SMTP creds | 0 env vars · 1 approved email post stuck | ship .env template |
| review pending | 0 pending (34 approved + 18 rejected) | already clean · close |

ops/migrate_github_issue_channel.sql
  · BEGIN/COMMIT transaction
  · UPDATE platform_marketing_review SET channel='github' WHERE channel='github_issue'
  · UPDATE platform_channel_registry SET status='deprecated' WHERE channel='github_issue'
  · audit before/
