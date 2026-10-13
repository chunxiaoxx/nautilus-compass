---
name: orgfuel-ORGH-a58b2e0130653f6c-e1d835ea6a
description: "commit ad996459c8bc 2026-05-11 feat(ops): cross-dialog notif"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-a58b2e0130653f6c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit ad996459c8bc 2026-05-11
feat(ops): cross-dialog notifier · Telegram push on new outbound session
Closes the missing wire for cross-dialog flywheel handoff (compass-dialog ↔
platform-dialog).

Problem: when compass-dialog ingests a session_*.md with thread_id=
compass-platform-handoff + thread_role=outbound · platform-dialog has no
way to know · unless it happens to thread_recall on next user prompt.
Sessions sat in compass memory for hours · this is the same gap that made
"L2 not live" misdiagnosed today (V7 09:09 fix went uncoordinated for 8h).

ops/cross_dialog_notifier.py · 5 min poll · stateful dedup
  · scans ~/.claude/projects/*/memory/session_*.md
  · matches: thread_id in [compass-platform-handoff, compass-dogfood-L3,
    spec-V7-actuator-collapse] + thread_role=outbound
  ·
