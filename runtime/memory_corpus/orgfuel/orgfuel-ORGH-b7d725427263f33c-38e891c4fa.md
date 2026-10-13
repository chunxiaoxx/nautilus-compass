---
name: orgfuel-ORGH-b7d725427263f33c-38e891c4fa
description: "commit 40a8b6325572 2026-05-06 fix(stress_audit): SQLite str"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-b7d725427263f33c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 40a8b6325572 2026-05-06
fix(stress_audit): SQLite string literals require single quotes
bug: line 1006+ "syntax error near 'ip'" — double-quoted SQL strings
in SQLite are identifier refs (column names), not string literals.
JSON metadata "{\"ip\":...}" was parsed as column-ref to nonexistent ip.

fix: emit single-quoted SQL literals · keep JSON inner double-quotes intact
verified locally with awk shell-escape for printf single-quote nesting
