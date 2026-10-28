# Phase 3 Existing Feishu Reuse Design

> Approved design, 2026-07-22. This design reuses the existing Zhiyong Nautilus
> Feishu application and its Bitable automation capability. It does not create a
> new Feishu application, expose secrets, read raw buyer submissions, or create
> online resources before the schema probe is reviewed.

## Goal

Operate Phase 3 through one online expert form and one internal Bitable ledger,
while preserving buyer-field ownership, third-party review evidence, revision
lineage, and the V5-to-Compass redacted export boundary.

## Grounded Asset Inventory

| Asset | Status | Reuse decision |
| --- | --- | --- |
| Zhiyong Nautilus enterprise self-built application | Existing; tenant token verified on 2026-07-22 | Reuse as the only Feishu application identity. |
| Bitable automation extension | Existing; its resource identifier is retained only in controlled configuration | Reuse as an internal Bitable trigger after field mapping and write permissions are verified. |
| Claude Code secret file | Existing; contains the application ID and secret | Keep as the controlled secret source; inject only into a short-lived process and never log values. |
| `ecc-shared` Bitable helper | Existing; token and read-back patterns are usable | Upgrade its Phase 3 mapping and tests; do not keep its legacy v06 schema as a Phase 3 contract. |
| Legacy FDE Feishu runners | Existing; operate assignment, QC, delivery, and settlement tables | Reuse their tenant-token, pagination, envelope-error, idempotency, and read-back patterns only. Do not reuse hard-coded table IDs or field maps. |
| Buyer Phase 3 Sheet | Existing external field and acceptance source | Read only for approved schema and buyer feedback fields. Do not make it a second operational ledger. |

The current Codex process did not inherit the Claude Code secret file. That was
an environment-loading gap, not an absence of an authorized application.

## Architecture

```text
Buyer Sheet (contract fields and buyer feedback)
              | controlled read / approved field map
              v
Our Bitable (the Phase 3 operational ledger)
  ^                    |                          |
  | online form        | Bitable automation       | eligible, redacted export
  |                    v                          v
External experts   ecc-shared adapter        V5 v3 JSONL + manifest
                                                  |
                                                  v
                                           Compass receipt
                                                  |
                                                  v
                                   controlled Bitable read-back
```

The automation extension is a trigger, not a judge. It may request a bounded
transition from `ecc-shared`, but it may not determine P0, buyer verdict,
`Repair`, or overwrite buyer feedback.

## Authority and Synchronization

Our Bitable is the only operational ledger for tasks, expert submissions, P0,
review records, `revision_of`, export state, and Compass receipts. The buyer
Sheet has field-level authority for the buyer's published contract, final
buyer result, and feedback category.

Synchronization is not a generic two-way copy:

1. An inbound adapter reads only mapped buyer fields and records a source
   reference, source revision marker, and import result in Bitable.
2. A new-task form submission carries the explicit task specification and the
   interaction evidence. After validation, one bounded, idempotent command
   creates a task draft and its first linked interaction attempt. A revision
   submission creates only a later attempt, linked through the internally
   resolved direct predecessor.
3. Internal reviewers write P0 and review fields in Bitable; the buyer's final
   result remains protected from automated overwrite.
4. An outbound adapter sends only the buyer-approved delivery fields with an
   idempotency key and stores its acknowledgement or block reason.
5. Buyer feedback is read back into the linked review record. A revision creates
   a new attempt with `revision_of`; a request for revision is never a Repair
   verdict.

Each mapped field has exactly one owner. Conflicts become `sync_blocked` with a
reason; they never trigger last-write-wins behavior.

## Authentication and Privacy

The application uses the tenant application flow:

```text
FEISHU_APP_ID + FEISHU_APP_SECRET -> tenant_access_token
```

Phase 3 does not require a user OAuth callback. `OAuth callback is invalid`
only matters for a later user-identity or cross-tenant OAuth flow, where the
registered redirect URI must exactly match the request. It is not a reason to
weaken or bypass the current application-identity path.

The adapter may use the controlled secret file in a short-lived process. It
must never print, commit, synchronize, or transmit the secret. Raw chat text,
attachments, share URLs, passwords, account identifiers, buyer identities,
and actual Bitable record IDs remain inside approved internal storage. Compass
receives only schema-approved redacted fields and hashes.

## Incremental Delivery

### Stage 0: Inventory and access proof

- Record the existing application, controlled automation-extension reference,
  secret-source location, and
  reusable runner capabilities in the operational asset registry.
- Verify tenant authentication and list only the target Bitable schema after
  the target base is identified.
- Do not write records or create a form.

### Stage 1: Buyer schema and field map

- Read the buyer's latest Phase 3 field names, allowed values, and 2026-07-22
  changes without exporting historical submissions.
- Produce a reviewed field ownership map: buyer source, internal owner,
  outbound delivery field, or prohibited field.
- Stop if buyer Sheet access is not authorized or any required field cannot be
  mapped without raw evidence.

### Stage 2: Internal Bitable and online form

- Reuse a confirmed internal Base, or create one only with explicit approval.
- Implement the four logical records: task, interaction attempt, review, and
  export receipt.
- Publish one online expert submission form with two bounded modes. A new task
  submission includes the required task specification (`title`, `task_type`,
  attachment-format tags, source materials, expected output, and key steps)
  plus its evidence pack; it may create one task draft and one linked first
  attempt. A revision submission may create only one later attempt for an
  existing task. Neither mode exposes or writes internal review, export, or
  settlement fields.

### Stage 3: Controlled one-record loop

- Run one authorized expert submission through P0, buyer feedback routing,
  `revision_of` validation, redaction, V5 manifest generation, Compass
  verification, and Bitable read-back.
- Use dry-run first for every outbound action. Retain hashes, record IDs, and
  receipts as evidence, but do not copy raw material into Git or Compass.

### Stage 4: Repeatable automation

- Connect the existing Bitable automation extension to the validated adapter.
- Enable idempotent inbound and outbound sync only after the one-record loop
  produces independent read-back evidence.
- Treat every schema drift, permission error, or missing receipt as a blocked
  state rather than retrying writes indefinitely.

## Existing Component Classification

| Component | Phase 3 use |
| --- | --- |
| Zhiyong Nautilus application | Required application identity and automation host. |
| `ecc-shared` | Required adapter and the only Bitable writer/read-back owner. |
| `ecc-fde-external` | External online form guidance and Evidence Pack contract. |
| `ecc-fde-internal` | P0, feedback classification, and review routing. |
| `ecc-fde-vertcase` | Task design that supports coherent six-or-more-round interaction. |
| `fde-task-pipeline` | State orchestration and explicit blocked outcomes. |
| Legacy checklist and row assembler | Historical/internal compatibility only; not delivery or verdict authority. |

No additional Skill is introduced. The work is a versioned adapter update and
field-map configuration inside these existing roles.

## Verification Gates

1. Tenant token probe succeeds without logging a secret.
2. Target Base and target Sheet schema are read back and compared with the
   approved field map.
3. A new-task form submission creates exactly one task draft and one linked
   first attempt; a revision submission creates exactly one later attempt. A
   form submission cannot modify a review or export record.
4. Every authorized write is followed by a Bitable read-back.
5. A retry with the same idempotency key creates no duplicate external write.
6. V5 accepts only eligible, redacted records and emits an official v3
   JSONL/manifest pair.
7. Compass returns a receipt that is matched back to the export record.

## Explicit Non-Goals

- No new Feishu application, independent ledger, or replacement automation
  system.
- No direct use of the legacy v06 field maps for Phase 3.
- No automatic buyer verdict, payment decision, or Repair assignment.
- No access to original acceptance materials beyond the schema and feedback
  fields explicitly needed for the approved map.
- No R3/Reborn change, push, merge, or raw-material export.
