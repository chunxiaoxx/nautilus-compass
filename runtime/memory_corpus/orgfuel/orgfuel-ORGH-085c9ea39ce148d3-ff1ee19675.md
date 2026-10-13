---
name: orgfuel-ORGH-085c9ea39ce148d3-ff1ee19675
description: "commit 756261fcf08a 2026-05-11 docs(specs): DISPATCH_PROTOCO"
metadata:
  type: reference
  source: org_fuel:commits_r5
  pf_id: ORGH-085c9ea39ce148d3
  corpus: orgfuel-v2
  sm_verdict: unparsed
---

commit 756261fcf08a 2026-05-11
docs(specs): DISPATCH_PROTOCOL + 3 spec drafts for L5 dogfood
specs/DISPATCH_PROTOCOL.md · L5 dogfood protocol
  · L2 evidence gate prerequisite (≥10 daily calls × 3 agents × 3 days)
  · 5-condition review gate · drift_check + proof-of-recall self-cite required in PR body
  · One spec at a time · not 3-at-once dump
  · Anti-pattern: dispatch before wire (305 / P1-1 mode)

specs/SPEC-S1-anchor-learner.md · suggested_owner: V5 · 3 days
  · Weekly cron auto-tune anchors_*.json based on verification_log FP/FN signal
  · V5 domain fit (already does similar log analysis)
  · status: draft · NOT dispatched · waiting L2 evidence gate

specs/SPEC-S2-proof-of-recall.md · suggested_owner: self · 5 days
  · Protocol-level kill of P1-1 fake-closure
  · recall returns reca
