# Phase 3 Single-Chain Agent Workflow Design

## Goal

Operate the Phase 3 vertical-domain interactive-trajectory program through one
auditable workflow. Normal cases should route without manual spreadsheet
matching or manual P0 scoring, while experts, buyer reviewers, and operators
continue to provide the human inputs that cannot be fabricated by an agent.

This design also removes obsolete Phase 3 tables and forms so that the
official workflow has exactly two external entries and one Bitable authority.

## Decisions

1. The current Phase 3 Bitable Base is the sole business authority. Its
   read-back, rather than messages, screenshots, agent reports, or local
   files, proves task state, buyer result, revision lineage, and export state.
2. Only two external Forms remain: `第三期专家信息采集（正式）` and
   `第三期任务与交互提交（正式）`.
3. All `归档_20260723_*` tables are obsolete. They will be deleted only after
   a metadata-only dependency check confirms they are not one of the four
   canonical tables and have no active automation or published Form.
4. Zhiyong Nautilus is the only identity allowed to make post-Form business
   writes. Its worker is the sole automated P0 and state-transition executor.
5. Zhiyong Mentor is the external expert interface. It receives an
   expert-scoped, redacted projection and cannot read or write Bitable
   business records directly.
6. The Bitable automation extension is a bounded event trigger only. It
   cannot score a submission, set `verdict`, decide buyer acceptance, or
   create a parallel ledger.
7. V5 and Compass consume only eligible, deidentified records after buyer
   acceptance. They do not inspect raw conversations, attachments, identity,
   links, or buyer feedback text, and they do not decide task state.
8. Reborn may consume a signed, deidentified workflow summary and issue a
   non-authoritative action certificate. It has no Bitable credentials and no
   P0, buyer, or export decision authority.

## Authoritative Records

| Table | Responsibility | External entry |
| --- | --- | --- |
| `第三期专家` | Expert profile, enablement, and training state | Expert information Form |
| `第三期任务与交互提交` | One question plus its complete interaction trajectory and revision lineage | Unified task-and-interaction Form |
| `第三期审核与反馈` | P0 outcome, buyer feedback category, and final verdict | None |
| `第三期导出与回执` | Deidentification eligibility, V5 manifest, and Compass receipt | None |

No other table is a current Phase 3 task, review, or operational status
source. The team guide is a Feishu Wiki or cloud-document package, not a
second Bitable ledger.

## Runtime Flow

```text
Expert Form
  -> Bitable expert record
  -> bounded Form-created trigger
  -> Nautilus read-back, validation, idempotent controlled write-back
  -> redacted Mentor projection
  -> expert onboarding, training, and status guidance

Unified task-and-interaction Form
  -> Bitable submission record
  -> bounded Form-created trigger
  -> Nautilus read-back, Phase 3 P0, controlled review/write-back
  -> buyer_ready | repair_required | blocked
  -> Mentor next-step or repair guidance

Buyer feedback
  -> approved buyer-field adapter
  -> Nautilus normalization and Bitable read-back
  -> accepted + P0 passed + deidentified
  -> V5 signed v3 event and manifest
  -> Compass independent verification and signed receipt
  -> Nautilus verifies both signatures and writes the receipt result
```

Every trigger carries only a route, Bitable record reference, and record
version. Nautilus derives an idempotency key from those values, reads the
authoritative record, validates a versioned field map, writes the permitted
next state, and reads the record back before emitting the next event.

## Automated Decisions and Human Inputs

| Step | Automated | Human input that remains required |
| --- | --- | --- |
| Expert intake | Required-field validation, qualification routing, onboarding projection | Expert supplies truthful registration and Doubao UID |
| Task intake | Completeness, Phase 3 protocol, safety, duplicate/conflict, six-turn evidence, and repair routing | Expert authors the question and interaction trajectory |
| Repair | Single-use repair reference, eligibility verification, reason-code guidance | Expert submits a new corrected record |
| Buyer review | Mapping and category normalization only | Buyer issues pass, repair, or reject result |
| Export | Eligibility and deidentification gates, manifest/receipt verification | None after the buyer result exists |

`buyer_ready` is a routing result, never buyer acceptance. The system must not
promise payment or export until buyer acceptance is read back.

## Application Boundaries

### Zhiyong Nautilus

Nautilus exposes four authenticated, idempotent routes:

1. `expert_submitted`
2. `submission_created`
3. `buyer_feedback_recorded`
4. `compass_receipt_recorded`

It receives the trigger, fetches only approved fields from Bitable, runs the
versioned rule set, makes the narrow permitted write, and records a
non-sensitive execution event. Failure leaves the Bitable business state
unchanged, records a machine-readable reason code, and routes the case to the
operator exception view.

### Zhiyong Mentor

Mentor receives only the expert's display handle, task-scope handle, next
step, reason code, repair reference when relevant, and a versioned knowledge
package. It provides onboarding, a 15-minute training path, Office Task
guidance, status explanation, FAQ, and repair coaching. It never receives
another expert's state, raw buyer feedback, raw evidence, or Bitable record
identifiers.

### V5 and Compass

V5 produces a signed v3 manifest only from an eligible deidentified snapshot.
Compass verifies it in isolation and signs a receipt bound to `task_id`,
`event_id`, `payload_hash`, and `manifest_hash`. Nautilus verifies both
signatures and the binding before writing receipt state. The prior loose hash
formats and unsigned receipt contract are retired rather than adapted in
parallel.

## Team Operating Model

The team does not run the business from a chat thread or manually pair two
Forms.

| Role | Daily action | Does not do |
| --- | --- | --- |
| Recruiting | Publish approved copy, invite candidates to the expert Form, build the community | Maintain a separate candidate ledger or promise acceptance |
| Trainer / operator | Use the Mentor materials, hold training, inspect only exception and buyer queues | Manually score normal P0 cases or alter task state outside Bitable |
| Expert | Work in Doubao Office Task, complete at least six relevant turns, submit one unified record | Submit a pre-screen and later result as unrelated records |
| Buyer liaison | Ensure approved field map and read back buyer feedback | Interpret agent status as buyer acceptance |
| Technical owner | Maintain field maps, event routes, alerts, and rules | Create another app, Form, or state store |

The operator-facing package will be published as one Feishu Wiki/cloud-document
entry with five reading sections: start here, recruiting, expert onboarding,
submission and repair, and operator SOP. It links to the official Forms and
the Base's filtered operational views but never duplicates their state.

## Cleanup and Rollout Sequence

1. Metadata-read the Base tables, views, sharing state, and automation
   bindings. Delete all obsolete `归档_20260723_*` tables after verifying the
   four canonical tables are excluded. Read back the remaining table list.
2. Run the existing fail-closed maintenance workflow: make the unified task
   Form private, add the approved seven fields, read back schema and Form
   metadata, then republish only on success.
3. Verify the two existing app identities, event subscriptions, message
   permissions, Bitable permissions, automation-extension binding, and
   failure logs. No secret belongs in Git, documentation, or messages.
4. Implement the Nautilus event endpoints and rule versions with tests,
   idempotency, controlled writes, and read-back checks.
5. Implement Mentor redacted projections, status-query contract, onboarding,
   and repair cards.
6. Align the offline V5/Compass dual-signature contract and test tamper,
   missing-field, invalid-signature, and binding-mismatch rejection.
7. Run one authorized real record through the complete available route. Each
   state advance must be independently visible in Bitable read-back. Do not
   manufacture a buyer verdict or reuse a developer conversation as evidence.

## Acceptance Gates

- Bitable contains exactly the four canonical tables after cleanup.
- Exactly two external Forms are published, with the approved field sets and
  no Base viewing grant for form users.
- A duplicate event does not advance a record twice, and a stale record
  version cannot overwrite a newer result.
- Mentor can explain the expert's own next step but cannot expose another
  expert's data or internal evidence.
- P0 produces only `buyer_ready`, `repair_required`, or `blocked`; it cannot
  set a buyer verdict.
- A repair record has complete validated lineage before it can be called
  `Repair`.
- V5/Compass output cannot reach Bitable without valid signatures and exact
  four-value binding.
- The team operations package contains no business-state copy and no raw
  acceptance material.

## Non-goals

This design does not automate buyer judgment, grant Reborn a writer role, add
another app identity, use Codex/Claude developer chats as a queue, or expand
the scope into the embodied-data project. It does not read or export raw
acceptance materials.
