# FDE Buyer Acceptance Rulebook 2026-07-21

## Purpose

This is the internal, deidentified bridge between a buyer-accepted workbook and the ECC-FDE skills, V5 fuel intake, and Compass policy gate. It is a rule source, not an external-expert checklist and not a reason to expose buyer material.

## Evidence Boundary

- Source: private buyer-acceptance workbook, sheet `7月21日`.
- Snapshot: locally retained outside Git; SHA-256 `E331414912D47DD3CAFBCE2AFC63583CC85839A857B01A70C1BC40722C21FED2`.
- Primary sample: 22 reviewed rows: 17 accepted and 5 needing revision.
- Subsets: 13 accepted without comment, 4 accepted with an advisory, 5 Repair candidates. The `三期交互示例` sheet contains seven multi-round candidate repair trajectories and requires separate deidentification before any training use.
- This file stores no task titles, personal names, buyer identity, attachment contents, links, or original feedback text.

## Rule Registry

| Rule tag | Class | Scope | Buyer evidence | Required internal behavior |
|---|---|---|---|---|
| `task_contract` | blocking | All task types | Two revised rows were judged to have an incomplete or unclear demand. | A task must state the decision/problem, expected outputs, constraints, source-material role, and acceptance criteria. A policy or background list alone is ungradable. |
| `attachment_discovery` | blocking when attachments are the reasoning surface | Attachment-backed tasks | One revised row exposed too much attachment substance in the prompt. | State the task and expected use of the materials, but do not paraphrase the answer-bearing contents of attached files. The model must inspect the supplied material itself. |
| `operational_definition` | blocking when the term drives output | Workflow, automation, and data tasks | A revised row lacked a folder-identification rule and a status-definition rule. | Define or attach every mapping, classification, boundary, calculation basis, and exception criterion needed to make the result reproducible. |
| `identity_and_style` | blocking | All buyer payloads | Two revised rows flagged real names and visible generation traces. | Replace real personal names with roles or placeholders. Remove decorative `**`, prompt scaffolding, local traces, and other visible AI-generation markers. |
| `baseline_completeness` | advisory | Strategy, staffing, finance, and operating decisions | An accepted row asked for clearer employee scope, compensation/incentive resources, and financing timing. | Add only the baselines needed for the requested decision: resources, time, budget/cost, target population, current state, or constraints. |
| `data_granularity` | advisory | Comparative and financial analysis | An accepted row asked for platform-level cost detail. | Match source granularity to the decision. Aggregate figures are insufficient when the decision compares channels, entities, periods, or products. |
| `attachment_capacity` | preflight | Agent workflows with many or large files | An accepted row asked whether the chosen agent could upload all required files. | Before assignment, record file count, type, size, upload method, batching plan, and fallback. Do not discover tool limits after a task is submitted. |
| `repair_closure` | blocking after revision | Any revised artifact | Multi-round examples show that a verbal claim of repair is insufficient. | Re-open the changed artifact, link each feedback item to a concrete change, and re-check the original source, arithmetic, citations, and current-versus-scenario wording. |
| `source_temporal_scope` | blocking | External facts, law, regulation, pricing, tax, and policy | Multi-round examples required official traceability, correct calculations, and explicit validity periods. | Cite the exact source, date, product/spec or rule identifier, scope, and time validity. Mark unresolved or future states as `待确认` or scenario, not fact. |

## Promotion Policy

- A direct buyer `needs_revision` observation promotes its rule to a blocking gate only for the matching task shape.
- Repeated direct observations may become a suite-wide gate. In this snapshot, `task_contract` and `identity_and_style` already have two observations each.
- Accepted-row suggestions are advisory. They may improve a task, but they cannot reject it unless their stated condition applies.
- Multi-round feedback is a Repair trajectory only after the pair is deidentified, source rights are checked, and the revised artifact is available for comparison.
- Compass may make a rule default only after a query-class or held-out comparison shows a positive measured delta. Do not promote from count alone.

## Fuel Record Contract

Each deidentified acceptance observation emitted to V5/Compass uses:

```json
{
  "feedback_source": "buyer_acceptance_20260721",
  "source_snapshot_sha256": "...",
  "source_sheet": "7月21日",
  "source_row": 0,
  "buyer_outcome": "accepted|needs_revision",
  "feedback_class": "blocking|advisory|repair_trajectory",
  "rule_tags": ["task_contract"],
  "evidence_ref": "secure-local-reference",
  "redaction_status": "verified",
  "revision_of": null,
  "observed_at": "ISO-8601"
}
```

Routing:

- accepted without feedback -> Gold candidate after privacy, provenance, and output-quality checks.
- accepted with feedback -> Gold candidate plus advisory tags.
- needs_revision -> Repair Pool; preserve the before/feedback/after linkage when a revision is later accepted.
- redline, fabrication, or unredactable material -> Reject Pool.

## Pressure Cases

1. A row repeats a policy or background list but never states the decision, output, or acceptance criteria: return `needs_revision` with `task_contract`.
2. A task lists the substantive contents of every attached source rather than requiring inspection of them: return `needs_revision` with `attachment_discovery`.
3. A workflow depends on a category, mapping, status, or exception rule that is neither defined nor supplied: return `needs_revision` with `operational_definition`.
4. A final payload contains names, decorative markdown, or visible generation scaffolding: block buyer-sync with `identity_and_style`.
