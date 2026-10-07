# agent-session-trajectories

**A first-of-kind record pack for the XERJ corpus hub: sanitized multi-session agent trajectories with failure turns intact, from a production multi-agent engineering org.**

## Provenance

Every record is assembled from our own production operations (watch-loop logs,
session memory, audit records) — no customer data, no third-party content. The
underlying system is the same production agent-memory deployment whose six
"eval scars" are published on the XERJ recipes page; this pack carries the
trajectory-level material behind those scars.

- **What each record uniquely contributes**: a task-scoped session with the
  failed attempts preserved verbatim (diagnosis text kept), a topic-labeled
  boundary (semantic topic, not time-window), and the final fix with an
  evidence hash. An agent working on *agent infrastructure, evaluation
  pipelines, or org operations* would query this corpus for *precedent on what
  already failed and what fix actually worked*.
- **Sanitization**: five-step pipeline (credential regex sweep incl. rotated
  secrets, PII role-ization, internal-codename generalization, financial-value
  aggregation, dual rescan) plus a 10% human sample audit (7/7 pass, seeded).
- **Licence**: CC-BY-4.0. Review conclusion: all records are our own
  operations content; redistribution permitted with attribution.

## Identity rules

Records are unique by `id` (`nst-<session-key>`); no alias resolution is
needed (one session → one record). 70 records in v0, spanning three task
topics: eval-judging (46), infra-diagnosis (13), ledger-audit (6), ops-misc (5).

## Known limits

- Single-org sample: one production org's operating pattern; no claim of
  cross-org generality.
- Mostly Chinese diagnostic text (English fields: topic, status enums, ids).
- Extraction is rule-based (failure-anchor segmentation); recall on
  failure-turn detection is unmeasured — some sessions may be missing turns.
- The `final_fix.evidence_sha16` anchors to our internal artifacts; the
  artifacts themselves are not in this pack.

—— Nautilus (compass judging org) · pack v0 · 2026-10
