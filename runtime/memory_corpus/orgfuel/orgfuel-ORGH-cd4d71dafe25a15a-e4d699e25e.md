---
name: orgfuel-ORGH-cd4d71dafe25a15a-e4d699e25e
description: "commit 66b08f0949ec 2026-05-06 v0.9.0-dev · cross-agent · MC"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-cd4d71dafe25a15a
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 66b08f0949ec 2026-05-06
v0.9.0-dev · cross-agent · MCP/A2A · LongMemEval-S 56.6%
Highlights:
- LongMemEval-S full-500 = 56.6% (DeepSeek V3.2 + 5-component pipeline · ~$1.5)
  paper SOTA tier (Zep 55-60%) at 1/15 cost vs commercial APIs
- Cross-agent memory federation (claude-mem can't do this)
  same user_id across Claude Desktop · Cline · Cursor · OpenClaw · Hermes
- MCP server v0.9 · 7 tools (4 new: ingest_obs · drift_history · session_search · profile)
- A2A adapter · 4 capabilities · Nautilus a2a-registry compatible
- npm wrapper @nautilus/compass-mcp ready
- Cursor extension scaffold (TypeScript)

v1.0 features (early access):
- E2EE crypto (compass_crypto · AES-256-GCM · 10/10 tests)
- RAID-2 reviewer (writer-reviewer separation · #7 fusion)
- 8 platform fusion points spec (#1
