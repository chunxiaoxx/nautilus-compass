---
name: orgfuel-ORGH-e5220e82af5ff951-f42ede1c49
description: "commit bc21a1fd8e7c 2026-05-13 release(1.5.1): data hygiene "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-e5220e82af5ff951
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit bc21a1fd8e7c 2026-05-13
release(1.5.1): data hygiene · 4 signal gates + version-drift debt closed
#1 importance gate · session_*.md need drift=red · 767→56 entries (-92.7%)
#2 numeric_claims hook · 5 patterns · jsonl audit · cross_ref alert in recall
#4 query expansion · 18 keys · daemon hit 0.553
#5 archived_at decay · 30d+ drop unless query has history kw
#3 (loop_anchor) dropped · plugin no hook into /loop iteration

version aligned 1.5.1 across pyproject / __init__ / PLUGIN_VERSION
(was drifting at 1.2.0 / 0.9.5 / v0.7 since v1.5.0 release)
