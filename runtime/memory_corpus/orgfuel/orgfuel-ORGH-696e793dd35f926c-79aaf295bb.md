---
name: orgfuel-ORGH-696e793dd35f926c-79aaf295bb
description: "commit cf94363b2c1b 2026-05-07 paper2 §4.6(a): add per-type "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-696e793dd35f926c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit cf94363b2c1b 2026-05-07
paper2 §4.6(a): add per-type breakdown of Neo4j -6.2 pts negative finding
The aggregate -6.2 pts looks like uniform damage but is actually concentrated:
single-session-user -25.0, knowledge-update -12.5, all four other types 0.0.

Both hurt types share a structural feature: the canonical answer lives in
one specific session, but the question's entity vocabulary appears across
many distractor sessions. Graph reranking promotes the distractors out of
top-k. This sharpens the closed-haystack explanation: the issue is not 'graph
adds noise everywhere' but 'graph hurts session-level disambiguation when
entities recur across the haystack'.

Data source: paper/results/experiments_20260505.csv rows 14-15 (DeepSeek-V3.2
thinking sample baseline vs thinking-graph-neo4j
