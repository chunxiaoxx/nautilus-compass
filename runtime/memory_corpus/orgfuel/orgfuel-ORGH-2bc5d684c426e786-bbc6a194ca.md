---
name: orgfuel-ORGH-2bc5d684c426e786-bbc6a194ca
description: "commit c582531f4b28 2026-05-10 feat(ops): compass_l2_metrics"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-2bc5d684c426e786
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit c582531f4b28 2026-05-10
feat(ops): compass_l2_metrics.py · L2 evidence dashboard cron
Reads verification_log.jsonl · counts compass MCP calls per session_id
(agent_type plumbing TBD #104) in 24h window · writes JSON to
/var/log/compass-l2-metrics.json · cron */5 min.

Output schema includes l2_evidence_gate with agents_meeting_gate /
agents_below_gate / agents_absent lists for the platform helix
dashboard. Today returns 32 calls/24h all from compass-dialog testing ·
expected agents (V5/V6/Kairos/V7-souls) all in absent list until
platform-side wires the cycle prompt patch.

Real evidence captured live: /var/log/compass-l2-metrics.json on
cloud VM · readable by platform helix or any other consumer.
