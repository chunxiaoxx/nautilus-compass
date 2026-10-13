---
name: orgfuel-ORGH-8f5c519448da26ab-fe6b935668
description: "commit b6ff7bfd15c0 2026-05-11 fix(ops): L2 metrics · nautil"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-8f5c519448da26ab
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit b6ff7bfd15c0 2026-05-11
fix(ops): L2 metrics · nautilus-v5 → nautilus-prime-001 alias
V5 production agent_id is 'nautilus-prime-001' not 'nautilus-v5'. The
EXPECTED_AGENTS list in compass_l2_metrics.py had the wrong name · so
dashboard always showed V5 absent even when V5 was calling daily.

Found during 7-claim self-verification this morning:
  meeting gate showed: nautilus-prime-001 · 23 calls/day · gate hit
  absent showed:      nautilus-v5         · phantom name · never used

After fix:
  meeting: kairos, nautilus-prime-001, nautilus-v6 (3 platform agents · all gate hit)
  absent:  claude-code-platform-dialog (human · expected), v7-souls-fusion (TBD)

This was the "测错表" pattern that anchors_self_audit v1.0 is designed
to catch · ironically the monitor itself had the same bug.

V
