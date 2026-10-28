# FDE Cross-Dialog SSOT 2026-07-21

## Purpose

This file is the shared coordination anchor for the FDE/ECC skills thread, the V5/Super Agent thread, and the Compass thread. It prevents three dialogs from inventing separate submission, QC, and fuel protocols.

## Current Decision

FDE now runs on an evidence-pack workflow, not a checklist-first workflow.

- External experts do not see skills, internal QC rules, 16-column buyer schema, or checklist tooling.
- External experts submit an Agent Evidence Pack through a Feishu Agent or a Feishu form.
- Internal agents use skills as operating instructions for intake, QC, feedback, accounting, buyer-sync preparation, and fuel distillation.
- Buyer scoring checklists are removed from the formal product workflow. Useful historical checklist rules can be absorbed into internal QC gates, then the standalone checklist skill should be archived or treated as a legacy reference.

## Agent Evidence Pack

Every external-agent-compatible submission should normalize to these fields:

| Field | Meaning |
|---|---|
| `task_id` | Assigned task or form-generated submission id |
| `expert_id` | Stable expert identity; map Feishu `open_id` once internally |
| `agent_tool` | WorkBuddy, Doubao, TRAE, ChatGPT, Claude, or Other |
| `conversation_evidence` | Screenshot, export file, shared link, or screen recording |
| `final_output` | The document, table, code, plan, report, or other final artifact |
| `source_materials` | Attachments, webpages, business materials, datasets, or references used |
| `human_confirmation` | Expert confirms the output was reviewed, source material is desensitized, and human judgment is responsible |

The compatibility layer is the evidence protocol, not per-tool UI automation. Do not create separate WorkBuddy, Doubao, TRAE, or Claude workflows unless a verified API integration later earns its keep.

## Ownership

| Dialog / Layer | Owns | Does Not Own |
|---|---|---|
| `nautilus-core` skills | ECC/FDE suite, external/internal wording, QC rules, skill de-duplication, this SSOT | V5 implementation, Compass ranking policy |
| V5 / Super Agent | Feishu intake, attachment digest, mechanical QC, `fuel_event`, buyer-sync payload, training-fuel exits | External expert UX policy, Compass recall policy |
| Compass | Fuel-event ingestion, recall, query-class breakdown, policy gates, measurable memory/routing uplift | Feishu writeback, buyer table synchronization, revenue accounting |
| External experts | Use any supported agent tool and submit evidence | Internal QC, skill loading, buyer schema, checklist generation |

## Canonical Workflow

```text
Expert uses any agent tool
  -> submits Agent Evidence Pack via Feishu Agent or form
  -> Feishu Base stores raw submission and attachments
  -> V5 fuel_intake reads records, downloads attachments, computes payload_hash
  -> mechanical QC writes feedback candidate
  -> internal QC agent applies ecc-fde-vertcase and buyer-feedback gates
  -> approved records produce buyer-sync payloads
  -> buyer sync stays gated until field mapping, permissions, desensitization, and idempotency are verified
  -> buyer feedback flows back to expert feedback, internal QC state, Compass memory, and training-fuel pools
```

## Fuel Pools

| Pool | Entry Criteria | Use |
|---|---|---|
| Gold Pool | Accepted by internal QC and buyer, preferably accepted on first pass | Distill strong agent workflows and examples |
| Repair Pool | Rejected once, then accepted after expert revision | Learn correction paths and feedback effectiveness |
| Reject Pool | Clear failure, unsafe material, missing evidence, or buyer rejection | Train risk detection, refusal, and QC gates |

## Buyer Acceptance Fuel 2026-07-21

`docs/business/FDE_BUYER_ACCEPTANCE_RULEBOOK_20260721.md` is the current internal calibration source for a completed buyer-acceptance workbook. The raw workbook remains outside Git; only deidentified rule records and the source snapshot hash may enter repository artifacts.

- Primary evidence: 22 reviewed rows on sheet `7月21日`: 17 accepted and 5 needing revision. The workbook also contains seven multi-round candidate repair trajectories.
- Normalize every observation with `feedback_source`, `source_snapshot_sha256`, `source_sheet`, `source_row`, `buyer_outcome`, `feedback_class`, `rule_tags`, `evidence_ref`, `redaction_status`, and `revision_of`.
- Accepted without feedback is a Gold candidate after privacy/provenance review. Accepted with suggestions carries advisory tags. `needs_revision` enters Repair, not Reject, unless a redline applies.
- Direct buyer revisions create scoped gates. Accepted-row suggestions are not automatic blockers. Compass only promotes a default after a measured positive delta.

## Phase 3 Interactive Trajectories 2026-07-22

`docs/business/FDE_PHASE3_INTERACTIVE_PROTOCOL_20260722.md` is the internal
source of truth for the current online-interaction phase. The unit of delivery
is a source-linked multi-round trajectory, not a standalone prompt or final
artifact.

- An approved online-interaction assignment requires Office Task mode, a fresh
  conversation per task, at least six question-answer rounds, relevant
  follow-ups, per-turn human feedback, and a share reference plus log
  identifier within 24 hours.
- P0 is a hard gate for task contract, scene/tag match, authenticity, safety,
  answerability, deduplication, interaction completeness, and trajectory
  coherence. P1 measures value dimensions and must not mask a P0 failure.
- `repair_required` is a candidate state. Only a source-linked, later accepted
  revision may become `verdict=Repair`; one-pass acceptance may become Gold.
- V5 owns the raw internal ledger and emits the redacted event envelope.
  Compass consumes it for replay and policy measurement; it neither receives
  raw conversations/attachments nor creates a second intake model.

## QC Gates From Buyer Feedback

These are internal gates. Do not make external experts read them as checklist instructions.

- Missing Agent Evidence Pack or unreadable evidence means return for补充.
- A topic-only row with no concrete demand is not gradable.
- L2/process tasks need enough concrete steps and real workflow context.
- Missing internal baseline is high risk: budget, ROI, conversion, costs, team/resources, audience/company profile, positioning, thresholds, reporting format, current process.
- External facts need source, date, product/spec, and scope.
- Do not invent approval tiers, retention years, sample thresholds, prices, tax rates, or project制度.
- Attachments must be used deeply, not merely named.
- Final output must have working links/files, usable formulas or weights when required, and no leftover AI labels.
- A task must state a concrete demand, output, constraints, source-material role, and acceptance criteria. Background material alone is not a task.
- When attachments are the reasoning surface, do not leak their answer-bearing contents into the prompt; require model inspection instead.
- Define every mapping, status, exception, or classification that controls the expected output.
- Remove real personal names, decorative markdown, and visible generation scaffolding before buyer-sync.

## Buyer Sync Gate

Automatic buyer sync is blocked unless all are true:

- `agent_qc_status=approved`
- required fields are mapped against the current buyer template or Base schema
- expert identity and internal-only fields are removed
- attachments and links are accessible
- `payload_hash` has not been synced before
- user or owner permission for the target buyer table has been verified
- read-after-write verification is possible

Until then, generate buyer-sync payloads only.

## Skill Routing

Active human-facing entries:

- `ecc-fde-external`: external expert onboarding, task submission, agent evidence pack guidance, safe answers.
- `ecc-fde-internal`: internal operations, dispatch, QC state, feedback, accounting, Feishu read/write gates.
- `ecc-fde-vertcase`: task-quality rules, buyer-feedback QC gates, case-production knowledge.

Tool-only or internal-only:

- `ecc-shared`: Feishu/Bitable/webhook/attachment/evidence normalization helpers.
- `fde-task-pipeline`: internal delivery orchestration only.
- `fde-row-assembler`: only when a verified buyer Excel/16-column export is required.

Legacy:

- `checklist-from-task`: remove from the formal workflow after useful rules are absorbed into QC gates.
- `ecc_fde_*` and archive copies: historical references only; they must not win routing over current `ecc-fde-*`.

## Verification Rule

No dialog should claim production readiness from design docs, self-report, screenshots, or generated files alone. The minimum verified chain is:

```text
submit test record -> read via API -> download attachment -> generate QC feedback -> write or prepare write -> read back / verify payload -> record evidence
```

For Compass, the equivalent rule is:

```text
fuel_event ingested -> query-class breakdown -> policy gate -> measured delta -> no default promotion without positive evidence
```
