---
name: orgfuel-ORGH-6b86ad5d3ba0c07b-86787782d6
description: "commit 7cf573d011a6 2026-05-09 feat(drift): v2 · detect reca"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-6b86ad5d3ba0c07b
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 7cf573d011a6 2026-05-09
feat(drift): v2 · detect recall-fired-but-not-consumed drift signal
This is the third leg of the recall consumption fix. v0 made bodies
visible; v1 made anti-anchor lessons surfaced; v2 adds the active
detection: if recall surfaces file paths and the agent never issues
Read on those paths, the agent is operating from titles only. That's
the failure shape that kept reproducing the same mistakes despite
recall hitting the right files.

New module recall_consumption.py:
- Locates active session jsonl via CLAUDE_SESSION_ID env or freshest
- Walks back to N most-recent records carrying a recall block (not N
  user turns · long sessions have many short turns without recall)
- Extracts memory file paths from recall stanzas
- Walks forward checking subsequent assista
