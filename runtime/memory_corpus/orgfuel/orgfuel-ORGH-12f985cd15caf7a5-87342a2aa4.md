---
name: orgfuel-ORGH-12f985cd15caf7a5-87342a2aa4
description: "commit 00cab61c7a11 2026-05-21 feat(v1.7.1): llm-wiki2 fuse "
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-12f985cd15caf7a5
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 00cab61c7a11 2026-05-21
feat(v1.7.1): llm-wiki2 fuse · declarative lifecycle memory
5 new frontmatter fields · schema-declared write-time-LLM-free 4-tier
promotion + Ebbinghaus decay (no LLM at lifecycle).

· session_writer.py: SYSTEM_PROMPT 扩 5 lifecycle fields
  (tier/decay_rate/forget_at/promote_after/reinforce_count)
· mcp_server.py: tool_ingest_obs args parse + emit + inputSchema 各 5
  properties · LIFECYCLE_TIERS enum · default by tier table
· recall.py: promote_lifecycle_tier (LLM-free deterministic · ~110 LOC)
  · Rule A access reinforce · Rule B promote check · Rule C forget check
· paper/LLM_WIKI2_FUSE_DESIGN.md: design doc + 5 spec smoke cases
· tests/test_lifecycle_fuse.py: 8/8 pass (5 spec + 3 edge)

Prior art (verbatim audit 2026-05-21):
· llm-wiki2 (rohitg00 gist · 5K
