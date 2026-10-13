---
name: orgfuel-ORGH-2a440b0c2ded8205-487fe3ec70
description: "commit 9798b708f948 2026-05-22 chore: bump 2.0.0 → 2.0.1 · s"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2a440b0c2ded8205
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 9798b708f948 2026-05-22
chore: bump 2.0.0 → 2.0.1 · ship M2 filter + L3 session_writer fix
v2.0.0 tag was pushed before two source-level fixes for the "真"
emphasis-overuse contagion landed:

  - 184d13d · session_writer.py SYSTEM_PROMPT bans "真" as emphasis
              adverb (L3 source-level fix for future session writes)
  - 5c46c8c · recall.py adds strip_zhen_emphasis() filter applied to
              memory body/description at output layer (M2 mechanical
              defense for hook-injected context)

Without this version bump, cloud deployments at ~/nautilus-compass/ and
/opt/nautilus-compass-v1/ report "version=2.0.0" but the actual files
predate both fixes. V5/V6/V7 continued generating "真X" style session
memories on cloud (session_writer untouched) and compass-mcp-tcp /

