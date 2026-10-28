# FDE Phase 3 Interactive Trajectory Protocol

## Scope

This is the internal, deidentified implementation protocol for the current
online-interaction phase. It converts the buyer's interaction guide and
crowd-task quality rubric into routing, QC, and fuel rules. It does not copy
the buyer documents, passwords, account identifiers, source attachments, or
raw conversations into Git.

The formal delivery unit is a **trajectory**, not a single prompt, screenshot,
or final artifact.

## External Operator Contract

Apply this contract only when the assignment explicitly says it is an online
interactive task.

1. Use the project-approved Doubao Office Task mode. Do not use a project
   account or mode for private tasks, account trading, public posting, or any
   work outside the assignment.
2. Start a fresh conversation for each complete end-to-end task. Parallel
   conversations are allowed, but their evidence must not be mixed.
3. After the first answer, conduct at least five further relevant exchanges.
   A qualifying trajectory therefore has at least six question-answer rounds.
4. Judge every model turn with a deliberate thumbs-up or thumbs-down, selected
   labels, and a concrete free-text reason. Ratings without a reason are not
   human review evidence.
5. Finish and share the full conversation within 24 hours of starting it, then
   submit the share reference and the platform log identifier with the final
   artifact.

An unusable first response may be marked abandoned. Do not pad it with
irrelevant turns merely to meet a count.

## Form Entry Boundary

The external path now has exactly two public Feishu Forms:

1. The expert-information form collects exactly the ten approved profile
   fields. It does not collect phone, email, Feishu account, agent history, or
   unrelated recruitment data.
2. The unified task-and-interaction form collects `UID`, the task, first and
   second category, related attachment and source, follow-up plan, name,
   Doubao UID, the required Doubao Office Task mode, turn count, conversation
   images, trajectory link, log identifier, and expert attestation. The first
   category is the verified single-select list; the second category remains
   free text so domain experts can refine it. A return submission may also
   carry the opaque repair reference supplied by the Mentor; first submissions
   leave it empty. A repair reference is bound to one authenticated expert,
   expires under the configured policy, and may be used by only one return
   submission.

One form submission creates one Bitable submission record containing both the
task and its completed trajectory. There is no separate public pre-screen or
result-supplement form, and experts do not need to match two records manually.

After Bitable read-back, Nautilus runs automatic P0 routing. It may route a
record to the buyer queue, `repair_required`, or `blocked`; it cannot create a
buyer acceptance. The Mentor returns only expert-scoped, redacted guidance for
the next action. For a repair, the expert uses the same unified Form and enters
the Mentor-provided opaque repair reference; the Form alone creates the new
record. Nautilus validates the authenticated expert binding, ownership, expiry,
single-use claim and predecessor state before writing the internal `revision_of`
link. Form views do not expose P0
internals, buyer feedback, `revision_of`, verdict, export, or Compass fields.

## Task Design Rules

- At least 90% of the batch must be authentic white-collar work, research, or
  decision tasks. Personal-life tasks are capped at 10%.
- Keep the buyer's first-level category unchanged; operators may refine lower
  levels only when that makes the scenario more precise.
- Each task must center one primary decision or deliverable. Do not combine
  unrelated product, technology, marketing, and market-analysis requests into
  an incoherent prompt.
- Attachments must be credible and support the requested decision. Do not use
  AI-generated or conflicting materials, generic macro sources for a specific
  company decision, repetitive policy packs, or low-quality media articles.
- Prefer text and structured data. Where materials are used, the target range
  is 10-500 MB and rich structures such as multi-sheet workbooks, formulas,
  tables, scans, footnotes, HTML exports, logs, and JSON are useful. This is a
  design preference, not a reason to invent a file.
- HTML, interactive pages, and frontend demos are encouraged. They must be
  complete, openable, editable, and verifiable artifacts, not code snippets.
  Their acceptance criteria must cover real data where required, interaction
  states, mobile readability, empty/error states, text layout, and editability.

## P0 Admission Gates

Every item must pass all P0 gates before it can be buyer-synced or considered
as learning fuel:

| Gate | Requirement |
|---|---|
| `task_contract` | The combined trajectory makes one task, final output content, output format, constraints, and information sources understandable. |
| `scene_tag_match` | Stated industry, role, and work scenario agree with the actual task. |
| `authenticity` | The scenario, facts, and expert knowledge level are realistic and internally coherent. |
| `safety` | No personal data, confidential business information, illegal content, or unsafe request. |
| `answerability` | Given materials or clearly public retrieval paths can support the task. |
| `dedupe_conflict` | No material duplication with the task pool and no conflict among prompt, data, and artifact. |
| `interaction_mode` | The approved Office Task mode and a distinct conversation were used. |
| `trajectory_completeness` | `turn_count >= 6`, every model turn has human feedback, and the final share reference plus log identifier are present within the deadline. |
| `trajectory_coherence` | Each follow-up addresses a defect, uncertainty, decision, or artifact from the prior context; topic jumps and padding fail. |

## P1 Value Assessment

P1 is a value score, not a substitute for P0. The current internal acceptance
target is at least two applicable P1 dimensions, subject to an updated buyer
threshold. Score the following dimensions separately:

- industry depth and correct professional boundaries;
- multi-dimensional comparison, sensitivity, grouping, or period analysis;
- industry-specific delivery standards and structured presentation;
- decision structure such as trade-off, matrix, prioritization, or SWOT;
- a dependency chain where a later step uses an earlier result;
- a dated or current data requirement with a credible acquisition route;
- direct mapping from output to an operational business action;
- verifiable evidence, sources, or citations;
- structured expression such as a table, comparison matrix, or clear list.

The per-turn human score should describe usability from 0 (unusable) to 4
(highly usable). It is evidence for diagnosis; it is not an automatic buyer
acceptance score.

## Repair and Lifecycle

```text
draft -> interaction_ready -> trajectory_submitted -> P0/P1 review
      -> buyer_feedback -> accepted | repair_required | rejected
```

- A buyer revision request creates `repair_required`, not a Gold or Repair
  verdict. Preserve `before`, buyer feedback, and `after` references.
- The same task may be reworked and resubmitted once after a failed review. In
  an explicitly declared alignment period, up to two further submissions are
  allowed. Exhausted items are retired rather than endlessly repaired.
- Only a later accepted, source-linked revision can receive `verdict=Repair`.
  A one-pass accepted item can receive `verdict=Gold`; an explicit rejection
  receives `verdict=Reject`.

## Internal Event Boundary

Bitable read-back is the only business ledger. It retains the authorized
evidence references and the `revision_of` relationship. V5 does not retain or
operate on raw evidence. It receives only a deidentified projection after the
Bitable eligibility gate, then signs and produces a v3 event and manifest. A
Compass-facing v3 export contains only schema-approved, redacted state and
hashes. Its `task_id` is an opaque mapping from the internal Bitable task
anchor; it is not an actual Bitable record ID.

Do not export `revision_of`, Bitable record identifiers, raw conversation text,
attachment contents, account identifiers, share URLs, passwords, buyer identity,
or per-turn human-feedback text. Compass receives a controlled feedback hash,
trajectory hashes, P0 state, final verdict, feedback class, and other
schema-approved metadata only.

The interactive process is performed by the human operator; automation verifies
metadata, routes feedback, produces the redacted event, and measures later
reuse.

## Pressure Cases

1. A six-round dialogue changes from finance to unrelated travel requests:
   fail `trajectory_coherence`.
2. A dialogue has six rounds but ratings contain only clicks and no reasons:
   fail `trajectory_completeness`.
3. A polished dashboard uses fabricated or contradictory attachment data:
   fail `authenticity` and `dedupe_conflict`.
4. An item is revised after buyer feedback but not yet accepted: retain it as
   `repair_required`; do not mint a Repair capsule.
