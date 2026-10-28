# ADR: Nautilus Platform Protocol V2

**Status:** Accepted architecture. This document authorizes no runtime, database, deployment, or external-system change.

## Decision

Nautilus Platform is a domain-neutral verified-collaboration protocol layer. It
provides authenticated operation handling, immutable manifest metadata,
independent signed receipts, idempotency, reliable delivery, and audit. It is
not a business workflow engine, a customer acceptance system, a training
system, or a second business ledger.

New Platform persistence will use a separate nautilus_platform PostgreSQL
database and a separately provisioned application role. It begins from empty,
forward-only migrations. It must not reuse the legacy Core public schema, its
historical Alembic graph, or its runtime create_all startup path.

## Context

The legacy Core backend combines historical marketplace, wallet, task,
identity, and FDE-related ORM models under one metadata root. Application
startup calls Base.metadata.create_all(...), while the historical Alembic graph
is not a trustworthy production migration authority. A prior schema-baseline
experiment also showed that a legacy public schema fingerprint is not portable
across reconstruction: historical column ordinals and server-rendered
constraint text differ, and the baseline included FDE business tables.

The earlier pure verified-work contract contains useful safety invariants:
immutable executor binding, expiry-bound lease, canonical artifact manifest,
independent verifier, signed receipt, and replay-safe settlement. It also
hard-couples all work to legacy Core agent_id, settlement, capability, and
survival models. That coupling is not appropriate for a generic protocol layer,
and it must not become an indirect FDE ledger.

## Authority Boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| Domain system | Business workflow, acceptance policy, source records, people, attachments, and final decisions | Platform protocol state |
| Nautilus Platform | Service authorization, protocol operations, protected manifest metadata, receipt verification, outbox delivery, and audit | Domain task state, domain verdicts, buyer decisions, or raw evidence |
| Executor | A bounded execution attempt and manifest submission | Independent decision, settlement, or domain write-back |
| Independent verifier | An attested decision under one registered verification policy | Work allocation, business state mutation, or direct settlement |
| Learning system | Independent learning evidence and append acknowledgement | Platform or domain state mutation |

For FDE Phase 3, the FDE repository remains the sole end-to-end owner and
Bitable read-back remains the sole business authority. The FDE adapter decides
whether a read-back fact is eligible for a protocol request and whether a
returned protocol receipt warrants a controlled write-back. Platform does not
interpret FDE rules or directly decide a Bitable mutation.

## Protocol Records

The initial records are intentionally narrow. They contain opaque references,
version identifiers, hashes, timestamps, and fixed reason codes. They do not
contain task text, user profile fields, external account identifiers,
conversation content, attachments, credentials, or domain-specific verdicts.

### OperationEnvelopeV2

Represents a request to execute or verify a bounded protocol operation.

Required fields:

- operation_id: Platform-generated opaque identifier.
- caller_id: registered service identity, not an end-user identity.
- source_ref_hash: salted hash of a source-side reference; the source system
  retains the reverse mapping.
- source_version: immutable source read-back or source-event version.
- operation_kind: registered generic capability name.
- policy_version: required execution or verification policy version.
- idempotency_key: caller-scoped duplicate-protection key.
- expires_at: UTC expiry.

The Platform may record only protocol delivery states: accepted, dispatched,
manifest_received, receipt_verified, failed, and expired. These states describe
protocol handling, not a domain outcome.

### ManifestV2

An immutable submission binding an operation and an attempt to a canonical list
of protected artifacts. Each item contains only artifact_id, media_type,
sha256, byte_size, and a protected storage_ref. The manifest body is canonical
JSON and the Platform stores its manifest_hash. Artifact bytes and raw source
content stay in the owning system.

### IndependentReceiptV2

An immutable, signed claim from a registered verifier. It includes the
operation, attempt, manifest hash, verifier identity and release, policy
version, one of accepted, rejected, or blocked, fixed reason codes, timestamp,
key id, and signature. The Platform verifies all bindings and the signature
before accepting it. An accepted protocol receipt is not a buyer verdict,
payment authorization, or domain final state.

### DeliveryOutboxV2 and AuditEventV2

The same transaction that accepts a manifest or receipt records an append-only
audit event and any required delivery request. A worker may retry delivery;
duplicate acknowledgements are harmless. A downstream acknowledgement never
changes a source-domain decision.

## Security and Privacy Rules

1. No raw business evidence, personal identifiers, external account IDs,
   prompts, dialogue text, screenshots, file bodies, tokens, or credentials in
   Platform tables, logs, metrics, outbox payloads, or learning projections.
2. The source adapter alone can translate source_ref_hash to a source record.
   Platform staff and services do not need that reverse mapping.
3. Unknown fields and unregistered policy, caller, verifier, or key ids fail
   closed.
4. Receipt signatures cover canonical JSON excluding the signature field. Key
   rotation is explicit and auditable.
5. Direct database access is unavailable to executors and verifiers. All
   writes pass through authenticated command handlers.

## Lifecycle

    source read-back
      -> source-owned eligibility decision
      -> Platform operation accepted and deduplicated
      -> executor receives bounded dispatch
      -> manifest received and bound
      -> independent verifier returns signed receipt
      -> Platform verifies receipt and emits outbox event
      -> source adapter independently decides any source write-back
      -> source read-back confirms business fact

An unavailable executor, verifier, learning system, or source adapter changes
only the relevant protocol-delivery state. It cannot synthesize a receipt,
advance source business state, or authorize settlement.

## Explicit Non-Goals

- Replacing a domain ledger or mirroring its state.
- Replacing human, buyer, or domain-specific decisions.
- Storing source evidence for convenient debugging.
- Automatically paying, changing reputation, or updating survival scores in
  the first vertical slice.
- Migrating, repairing, or deleting legacy Core database tables.
- Creating an FDE workflow, Skills set, Feishu automation, form, or Bitable
  write path.

## Reuse and Disposition

| Existing asset | Disposition |
| --- | --- |
| Pure verified-work contract | Reuse its hash, binding, independence, expiry, and idempotency invariants after removing legacy accounting assumptions. |
| Legacy agent_identity_map | Remains a legacy Core compatibility mapping. It is not an FDE external-expert identity authority and is not copied into Platform. |
| Legacy Task, AcademicTask, wallet, reward, capability, and survival models | Historical systems. No V2 record may write or infer their business state. |
| Historical Alembic tree and runtime create_all | Freeze as legacy evidence. Do not treat either as the migration root for Platform. |
| Failed public-schema migration experiment | Retain only as negative design evidence. Do not merge, deploy, or use it as a baseline. |

## Acceptance Gates

No production use is permitted until all gates below independently pass:

1. The empty-database migration root upgrades, downgrades, and upgrades again
   in a disposable PostgreSQL environment with one unambiguous head.
2. Unit tests prove duplicate commands, changed-payload replay, expired
   operation, manifest tampering, unregistered caller, executor-verifier
   conflict, invalid signature, and duplicate delivery acknowledgement.
3. A deterministic, non-business vertical slice proves one operation,
   manifest, independent receipt, audit event, and retry-safe outbox delivery.
4. Logs and storage inspection prove that no protected source content or
   external-person identity is written to Platform.
5. Any domain adapter is separately reviewed as a versioned dependency. For
   FDE, this additionally requires Bitable read-back on both sides of a
   controlled write-back request.

## Consequences

This decision creates a deliberate boundary rather than a replacement
application. It costs one isolated database and explicit adapter contracts, but
removes the risk that a generic execution feature silently becomes a duplicate
business ledger. Settlement and score projections remain possible optional
capabilities only after their authority, accounting source, and independent
acceptance evidence are separately approved.
