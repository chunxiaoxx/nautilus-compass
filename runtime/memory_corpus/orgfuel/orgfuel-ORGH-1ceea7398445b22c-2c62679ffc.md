---
name: orgfuel-ORGH-1ceea7398445b22c-2c62679ffc
description: "commit 2422d7f2f605 2026-06-06 feat(fde): expert-review → Po"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-1ceea7398445b22c
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 2422d7f2f605 2026-06-06
feat(fde): expert-review → PoI settle (north-star fuel intake) (#42)
The human expert verdict (复核状态/分项分) is the first non-self-referential PoI
signal (anchor #3). It does NOT flow through the fde_verdicts bus/SETTLE_SOURCES
(that is soul's checklist path) — it flows through the DIRECT credit_from_verdict
adapter, which had no production caller (tests only). settle_expert_reviews reads
filled 飞书 review records and credits fde-capsule-<task_uid> (SAME key soul/bus
+ capsule pipeline credit → compounds). Idempotent via 复核时间 watermark. e2e
verified: data_004 通过 → +0.84 on the shared capsule key. 4 tests green. NO LLM.

Co-authored-by: nautilus-platform-saas-dialog <saas-dialog@nautilus.social>
