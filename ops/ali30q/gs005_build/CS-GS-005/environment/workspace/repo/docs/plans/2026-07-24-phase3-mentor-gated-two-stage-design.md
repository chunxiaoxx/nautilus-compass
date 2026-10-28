# Phase 3 Mentor-Gated Two-Stage Task Design

## Goal

Restore the required business gate: an expert submits a high-difficulty
question first, Nautilus evaluates that question, and only an eligible question
may proceed to the Doubao Office Task interaction. Keep the expert experience
simple while retaining Bitable read-back as the sole business authority.

## Product Decision

An expert must never copy a task code, choose a Bitable table, manually match
a UID, or look for a second public Form link. The visible task flow is:

```text
Submit question
  -> receive Mentor task card after automatic precheck passes
  -> complete the Doubao interaction
  -> submit interaction evidence from the same task card
```

The registration step happens once before this flow. The expert may see an
expert-information form, but all task continuation is initiated by Zhiyong
Mentor.

## Authoritative Data Model

Phase 3 moves from one overloaded submission table to two related task tables.
They are not independent ledgers.

| Canonical table | Owns | Relation |
| --- | --- | --- |
| `第三期专家` | expert profile, enablement, Mentor session scope | one expert to many questions |
| `第三期题目预审` | question, field tags, source attachments, precheck decision, task lifecycle | linked to one expert; one question to many interaction attempts |
| `第三期交互成果` | Doubao Office Task evidence, six-turn metadata, screenshots, link and log identifier | linked to exactly one eligible question and inherited expert |
| `第三期审核与反馈` | automated P0 records, buyer feedback category and final verdict | linked to the question and, when present, an interaction attempt |
| `第三期导出与回执` | eligibility, V5 manifest and Compass receipt | linked to the accepted interaction attempt and root question |

`豆包UID` remains a user-supplied consistency field for buyer alignment. It is
not a key, a security proof, or a cross-table join rule. All task relationships
are created by Nautilus after read-back.

## Expert-Facing Flow

```text
Recruiting message / group
  -> Zhiyong Mentor registration entry
  -> expert-information capture and Mentor session binding
  -> question-precheck Form
  -> Nautilus question P0
       -> repair / blocked: Mentor explains the next step
       -> eligible: Mentor sends one task card
  -> Doubao Office Task, at least six meaningful turns
  -> same Mentor task card opens the interaction-evidence submission page
  -> Nautilus creates and links the interaction row
  -> interaction P0 -> buyer queue / repair / block
```

The interaction page is not a broadly shared Bitable Form. It is a
Mentor-launched continuation page in the existing application. This avoids
assuming that a public native Form can safely prefill or conceal a relation
field. It still collects the required images, trajectory link, log identifier,
turn metadata and expert confirmation.

## Hidden Continuation Handle

When question P0 returns `eligible_for_interaction`, Nautilus issues a
short-lived, single-use opaque continuation handle. It is carried by the
Mentor card and the authenticated application session; it is not shown as a
task code or Bitable record identifier.

On interaction submission, Nautilus verifies all of the following before it
creates or links a Bitable row:

1. The card/session belongs to the bound Mentor expert scope.
2. The handle is active, unexpired and belongs to an eligible question.
3. The question has not already consumed the handle for the same submission.
4. The request version and idempotency key have not been processed.

Nautilus then creates the interaction record, writes the question/expert
relations, marks the handle consumed, and reads both records back. A duplicate
delivery returns the original linked result; an expired or cross-expert card
returns a generic Mentor recovery action without exposing internal identifiers.

The handle is technical session state, not a business ledger. Bitable remains
the only source for task, review, lineage and export state.

## Agent Responsibilities

| Component | Responsibility | Must not do |
| --- | --- | --- |
| Zhiyong Mentor | onboarding, training, task-card delivery, status explanation and repair coaching | read/write Bitable directly, expose IDs, issue business verdicts |
| Zhiyong Nautilus | Bitable read-back, question P0, interaction P0, relation writes, idempotency, buyer mapping and downstream receipt write-back | claim buyer acceptance, expose raw evidence, create a parallel ledger |
| Bitable automation extension | emit a bounded metadata event after question-form creation | score, decide P0, decide verdict or invoke V5/Compass directly |
| V5 | sign the eligible deidentified v3 event and manifest | read Bitable, raw conversations or private evidence |
| Compass | validate the v3 artifact and sign its receipt | write business state, judge buyer feedback or inspect human data |

## State Model

Question states are `precheck_pending`, `precheck_running`,
`eligible_for_interaction`, `question_repair_required`, and `blocked`.
Interaction states begin only after question eligibility: `interaction_draft`,
`interaction_qc_running`, `buyer_ready`, `repair_required`, `blocked`,
`buyer_accepted`, or `buyer_rejected`.

`eligible_for_interaction` is an automated routing result, not a buyer pass.
The later interaction P0 is the only place that evaluates the six-turn Office
Task evidence. Buyer acceptance, settlement, V5 export and Compass import stay
behind their existing Bitable read-back gates.

## Automation and Recovery

The normal route is automatic. The operations team handles only exceptions:

- a question that needs repair receives Mentor guidance and a fresh precheck
  continuation;
- an expired task card can be reissued only when the precheck remains eligible;
- a duplicate interaction submission is idempotent rather than a second task;
- a UID mismatch is routed as an expert-profile correction, not a guessed link;
- a missing image, link or log identifier becomes `repair_required`, with a
  Mentor explanation based on a reason code.

No group message, spreadsheet note or developer chat can repair a relation or
advance a state.

## Migration and Cleanup Boundary

The user has authorized deletion of the empty default `数据表` and a maintenance
window. That authorization does not authorize the prior unified-table
maintenance plan, because it would preserve the wrong external flow.

Before mutation, the implementation must perform a metadata-only inventory of
the archived question-precheck and interaction-result tables. It may reuse a
compatible table/view configuration or recreate it with the approved fields,
but it must not read business rows or acceptance material. After the new five-
table schema and routes pass read-back verification, obsolete tables and Forms
are deleted or retired in one controlled transaction sequence. The former
unified task table cannot remain a second production entry.

## Acceptance Criteria

1. An expert has no visible task ID or cross-table matching step.
2. A question cannot open an interaction submission until Nautilus records
   `eligible_for_interaction` in Bitable.
3. Every interaction record read-backs with exactly one root question and one
   expert relation.
4. A repeated card action or repeated network delivery cannot create a second
   interaction task.
5. A cross-expert, expired or consumed continuation handle cannot create a
   relation.
6. Mentor can show the expert's next step without seeing raw buyer feedback,
   Bitable identifiers or another expert's record.
7. V5 and Compass continue to consume only accepted, deidentified downstream
   artifacts under the signed four-value contract.
