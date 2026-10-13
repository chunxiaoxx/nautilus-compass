---
name: orgfuel-ORGH-1323212609dd8caf-ef4663d91c
description: "commit 351adaebecd7 2026-05-13 feat(anchors): self_audit v1."
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1323212609dd8caf
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 351adaebecd7 2026-05-13
feat(anchors): self_audit v1.2 · +2 pos +2 neg cross-dialog close-loop pair
closes #135 (铁律入库 part 2/2):

positive +2 · outbound written after inbound consumed · partial-status posted mid-ship
negative +2 · silent-ship on agent side (ssh-grep required to discover) · terminal-only signaling

pairs with existing feedback_cross_dialog_bidirectional_close_loop.md · now covered
from both sides · behavioral rule in feedback · drift signal in anchors · drift_check
fires on session_*.md that violate cross-dialog contract before ingest_obs

anchors version 1.1.0 → 1.2.0 · counts 22+26 → 28+28
