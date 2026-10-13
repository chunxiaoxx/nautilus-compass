---
name: orgfuel-ORGH-22865acc3c89bb1f-0b1416c14a
description: "commit 6cedf1ba3ae5 2026-06-06 feat(fde): expert-review pack"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-22865acc3c89bb1f
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 6cedf1ba3ae5 2026-06-06
feat(fde): expert-review packet generator (出复核包 · all 6 tasks) (#41)
build_packet renders one expert-facing packet per task: 题目 + checklist items
with soul 一审 ✅/❌ marked (for the human to challenge the AI judge) + veto flags
+ deliverable list (or LOST flag) + 专家复核表单 → source='expert' verdict. Reuses
load_fde_tasks (DRY). Real run: 6 packets, data_001 flagged deliverable-lost
(prod didn't persist model_output, no local _out), 002-006 list real artifacts.
6 tests green. NO LLM.

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>
