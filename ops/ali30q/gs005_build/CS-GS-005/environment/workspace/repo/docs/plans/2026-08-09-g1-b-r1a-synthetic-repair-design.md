# G1-B R1a synthetic repair design

**Status:** plan-only candidate; no runtime task is authorized by this document

**Platform baseline:**
`21a36fd2cfc8a2223454d1f7c5bc542045910291`

## Outcome

G1-B defines one reviewable R1a implementation target for a deterministic,
synthetic code repair. It turns the G1-A result `ready_for_r1a_plan` into a
single design and implementation plan. It does not execute the plan.

The package proves that Platform, V5, Compass, and an independent verifier have
one compatible interpretation of the future chain before any runtime work is
authorized. The only current action is `draft_r1a_implementation_plan`.
Runtime, self-modification, model calls, tool execution, network, database,
Docker, dogfood execution, deployment, push, merge, business workflows, and
FDE work remain unauthorized.

Three approaches were considered:

1. Markdown documents alone are easy to read but do not prevent stale source
   pins or a widened scope from being presented as the approved plan.
2. Two documents plus an exact-schema, byte-bound plan package provide a
   fail-closed handoff without creating a runtime. This is the selected design.
3. A new planning service, review broker, or DMAS runtime would create another
   coordination system before the first task is defined and is rejected.

## Fixed authority inputs

### Platform

The Platform baseline is the G1-A commit above. Its committed evidence is:

- path:
  `phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json`;
- SHA-256:
  `f96c61157a977ad30f6299d5c4cbc01b0f965033511464a349bb7f4fd3127bea`;
- derived status: `ready_for_r1a_plan`;
- allowed action: `draft_r1a_implementation_plan`.

G1-B may not reinterpret historical O1 evidence as current runtime evidence.

### V5 action-owner input

Platform source-reads the existing V5 plan-only authorization:

- authority commit:
  `f560be28ecac550e754eff2b82e36ea91ecad0b6`;
- proposal commit:
  `cdd55315f03c145e7d83d5a0eddbfeeb5d951c94`;
- path: `docs/contracts/v5-r1a-plan-only-authorization-v1.json`;
- Git-blob SHA-256:
  `9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6`.

This input permits V5 to review and help draft the action-side plan. It does
not admit a V5 executor or any V5 runtime file. A later executor proposal is a
new owner input and requires a separate source-admission decision.

### Compass learning-boundary input

Platform source-reads the existing Compass read-only capsule:

- authority commit:
  `37efc4fc2f7455202c94515b29314af9e5e2e16e`;
- proposal commit:
  `e87234bbdc072bd10e9b88079c21f7c574361506`;
- path: `docs/contracts/m1-r1a-grounding-capsule-v1.json`;
- Git-blob SHA-256:
  `1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0`.

All seven Compass capabilities remain false. The capsule supplies one fixed
quality rule only: an accepted claim requires integrity and scope evidence;
otherwise the correct outcome is `review_required`. Compass holds no HMAC
secret and receives no memory, recall, ingest, model, network, tool, or write
authority.

## Single synthetic task

The task identifier is `synthetic_code_repair_v1`. It contains no business,
user, account, conversation, credential, local-path, or production data.

The future authorized harness creates a disposable synthetic module containing
a bounded integer-clamp defect. The requested behavior is fixed:

- values below the lower bound return the lower bound;
- values above the upper bound return the upper bound;
- in-range values are unchanged; and
- invalid bound ordering is rejected by the fixture oracle.

The V5 action-side candidate is a deterministic patch artifact. It may modify
only the disposable synthetic module and may not address any repository source
file. The expected positive outcome is `completed`. If required scope evidence
is absent, the correct bounded outcome is `review_required`, not a guessed
success.

The fixture bytes, expected patch bytes, test oracle, tool-policy document, and
opaque input identifier must each be canonicalized and SHA-256 pinned before a
future operation is accepted. The plan intentionally does not pin placeholder
hashes before those owner artifacts exist.

## Owner boundaries

### Platform and DMAS

Platform remains the only decision and protocol owner. It authenticates the
caller, validates source-admitted owner inputs, creates `operation_id`, signs
the `OperationEnvelopeV2`, records the operation, and owns protocol read-back.

For R1a, DMAS is a pure Platform selection function over a fixed tuple of
registered executor candidates. It compares only:

- required capability;
- registered role and active status;
- exact executor release;
- exact tool-policy hash; and
- the source-admitted owner decision.

Exactly one candidate is required. Zero or multiple matches fail before the
Platform envelope is issued and before any protocol write. The selection is
not a new service, queue, table, conversation router, marketplace, or ledger.
The chosen identity, release, and policy are bound into the subsequent
`ExecutionAttemptV2`.

The claim is not the pre-read by `attempt_id`. It is the committed
`accepted -> dispatched` compare-and-transition performed by
`ProtocolRepository.transition` in the same transaction as the attempt insert.
The future test must force two independent PostgreSQL sessions to submit
different attempt identifiers for the same accepted operation. Exactly one
transaction may commit; the loser returns the fixed
`attempt_claim_conflict`, and no losing attempt, audit, or outbox row remains.
If that RED shows the existing compare-and-transition is insufficient, only a
forward, single-head schema or repository change may close it. The plan must
not silently impose operation-wide uniqueness that would redefine general
Protocol V2 retry semantics.

### V5

V5 owns only the future bounded action adapter, deterministic candidate
artifact, and executor-authenticated `ExecutorExecutionEvidenceV1`. It must
independently recompute the attempt-scoped
`input_ref_hash` from an injected one-use secret and compare it with the value
recorded by Platform before producing an artifact or signing evidence.

The V5 signer is injected and corresponds to the exact registered executor
key. V5 signs the evidence `canonical_signing_bytes`, not the patch bytes in
isolation. The `executor_signature` therefore binds the operation, attempt,
input, policy, grounding capsule, fixture, executor release/key, result state,
and artifact hash. A caller cannot create valid evidence merely by copying a
registered executor identifier into a manifest.

The future V5 adapter has no model, environment-key, network, database, shell,
terminal, general tool gateway, source-write, self-modification, deployment,
push, or merge capability. Its owner proposal must pin its own identity,
release, key, files, fixture hashes, tests, and limitations. The current V5
plan-only waiver cannot admit that proposal.

### Compass

Compass owns the immutable capsule bytes and the interpretation of its single
quality rule. It does not execute the repair, select the executor, derive the
HMAC, inspect raw repository state, persist experience, or sign the protocol
receipt.

The capsule hash is a canonical input to Platform's attempt-scoped HMAC. It is
never copied directly into `ExecutionAttemptV2.input_ref_hash`. A changed or
unreadable capsule blocks before operation acceptance.

### Independent verifier

The verifier has a registered principal, release, and Ed25519 key distinct from
the executor. It receives a short-lived, attempt-bound manifest read grant,
reads only the referenced synthetic artifact, applies the candidate only to a
fresh disposable fixture, and runs the fixed oracle.

Before applying the patch, it independently resolves the registered executor
key and verifies `ExecutorExecutionEvidenceV1`, the operation, attempt,
executor release, tool policy, `input_ref_hash`, capsule, fixture, artifact
hash, and `ManifestV2.manifest_hash`. Only then may it sign
`IndependentReceiptV2.canonical_signing_bytes`. It cannot execute the original
task, edit an owner repository, select a different policy, or grant merge or
deployment authority.

### Three-frame review topology

Platform publishes one candidate full SHA. That same SHA is sent in parallel
to the V5 action owner and Compass learning owner. Each response is exactly:

- `ACK`, meaning High=0 and Medium=0 for that owner's boundary; or
- `CONFLICT`, carrying an exact full commit, path, test command, and test
  result that reproduces the conflict.

Platform independently reads both responses and owner blobs, resolves every
conflict, and creates the final plan decision. No fourth coordinator, review
broker, copied SSOT, or conversation transport runtime is created.

## Data flow

The future, separately authorized R1a execution follows exactly this order:

```text
fixed synthetic request
-> OperationRequestV2
-> caller credential verification
-> source-read current V5 and Compass inputs
-> DMAS pure unique-candidate selection
-> Platform-signed OperationEnvelopeV2
-> ProtocolService.accept_operation
-> Platform derives attempt-scoped HMAC input_ref_hash
-> ExecutionAttemptV2
-> ProtocolService.record_attempt (claim)
-> V5 verifies HMAC and emits bounded candidate patch
-> V5 signs ExecutorExecutionEvidenceV1
-> Compass rule requires integrity and scope evidence
-> ArtifactV2 + ManifestV2
-> ProtocolService.record_execution_evidence_and_manifest
-> short-lived ManifestReadGrantV1
-> independent verifier re-verifies executor evidence and artifact bytes
-> independent verifier applies patch to disposable fixture and runs oracle
-> independently signed IndependentReceiptV2
-> ProtocolService.record_receipt
-> outbox claim and local acknowledgement without network delivery
-> separate Platform database read-back
```

The positive receipt is `accepted` with `policy_satisfied`. It attests that the
fixed repair evidence satisfies the bounded policy; it does not approve a
source merge, deployment, production use, or experience promotion.

Exact replay returns the original operation, attempt, manifest, receipt,
audit, and outbox records with zero growth. A changed replay conflicts and
does not alter the original records.

## Attempt-scoped grounding binding

The HMAC input is canonical JSON with exactly:

- `attempt_id`;
- `bound_capsule_hash`;
- `derivation_version=m1-attempt-input-hmac-v1`; and
- one source-admitted opaque input identifier.

Platform creates a one-use secret after the attempt identifier exists. The
secret is injected into the bounded V5 adapter only for the attempt, is never
stored in Platform, Compass, evidence, logs, artifacts, manifests, receipts,
or Git, and is destroyed after the adapter returns. V5 recomputes the HMAC and
uses constant-time comparison. The verifier checks that the execution evidence
and manifest remain bound to the exact Platform-recorded `input_ref_hash`.

The future implementation must reuse or separately source-admit the reviewed
M0 binding semantics. It may not import code at runtime from a historical
worktree or treat ancestry alone as source admission.

## Executor-authenticated execution evidence

`ExecutorExecutionEvidenceV1` is an additive Platform-owned wire contract; it
does not change the frozen `ManifestV2` or Protocol V2 conformance vectors. Its
exact allowlist is:

- `evidence_version`;
- `operation_id` and `attempt_id`;
- `input_ref_hash`;
- `executor_id`, `executor_release`, and `executor_key_id`;
- `bound_capsule_hash`, `fixture_hash`, and `tool_policy_hash`;
- `artifact_hash` and fixed `result_state`;
- canonical UTC `produced_at`;
- `signature_algorithm=ed25519-v1`; and
- `executor_signature`.

Its `canonical_signing_bytes` exclude only `executor_signature`. Platform
publishes canonical conformance vectors and V5 consumes those vectors; V5 does
not create a second canonical contract. At acceptance time, Platform resolves
the exact active executor identity, release, role, key ownership, algorithm,
and public key from the DB-backed registry and verifies the signature.

A future forward migration adds only `protocol_executor_evidence`, containing
the approved opaque identifiers, hashes, version, fixed state, UTC timestamp,
algorithm, evidence hash, and protocol signature. It stores no patch bytes,
fixture bytes, raw evidence, prompt, path, secret, token, account, or private
key. `ProtocolService.record_execution_evidence_and_manifest` verifies that:

1. the evidence exactly matches the Platform-recorded attempt, including
   `input_ref_hash`, executor release, and tool-policy hash;
2. the evidence capsule and fixture hashes are the source-admitted values;
3. its artifact hash equals the single artifact hash in the manifest;
4. the executor signature verifies against the registered executor key; and
5. the evidence row, manifest row, state transition, audit event, and outbox
   event commit in one transaction.

The verifier reads the persisted evidence and manifest, independently verifies
the same signature and bindings, and only then reads the artifact through the
grant. Forged evidence, a substituted artifact, wrong key/release, changed
binding, or changed replay fails closed. Exact replay returns the original
evidence and manifest without row, audit, or outbox growth.

## Failure matrix

| Stage | Failure | Receipt | Persistent result |
| --- | --- | --- | --- |
| Plan admission | wrong Platform/V5/Compass commit, path, hash, schema, or widened authority | none | no runtime work may begin |
| Caller/source gate | invalid credential, expired request, changed fixture or capsule | none | zero protocol writes |
| DMAS selection | zero or multiple eligible executors, wrong release or policy | none | zero protocol writes |
| Operation idempotency | same caller/key with changed payload | none | original operation unchanged; no new events |
| Attempt claim | wrong executor, release, lease, HMAC, policy, or two-session concurrent claim | none | one winner; loser `attempt_claim_conflict`; no losing row/event |
| Action boundary | path escape, unapproved capability, nondeterministic patch, forged/substituted evidence, or wrong executor key | none | transaction rollback; no evidence/manifest/receipt |
| Grounding rule | valid bounded artifact lacks required scope evidence | `accepted/policy_satisfied` for a `review_required` artifact | no repair-success claim |
| Manifest/grant | artifact, manifest, storage reference, nonce, expiry, or attempt tamper | none | state remains at last valid record |
| Verifier | executor/verifier principal or key reuse, wrong release, signature, oracle, or binding | none | no receipt |
| Positive path | exact bounded repair and oracle pass | `accepted/policy_satisfied` | one receipt and required audit/outbox |
| Exact replay | byte-identical command replay | original record | zero row/audit/outbox growth |
| Changed replay | same identity/key with changed binding | none | conflict; original records unchanged |

No precondition failure is converted into a signed success. A signed
`review_required` path is permitted only when a valid, bound artifact honestly
reports that outcome under the fixed Compass rule.

## Rollback

G1-B planning changes only three Platform plan-package files and their static
test. Before later execution is separately authorized, rollback is simply
abandoning the isolated branch; no runtime state exists.

For the future R1a harness:

- no owner repository file is modified by the task;
- candidate patches apply only to a disposable fixture;
- every protocol command is transactional;
- injected failures roll back the complete command;
- executor evidence and manifest are verified and committed atomically;
- outbox acknowledgement performs no network send;
- exact replay is idempotent;
- a unique disposable Platform database is dropped by its exact validated
  name and independently read back as absent;
- exactly the plan-allowlisted `protocol_executor_evidence` migration and table
  may be added, with one migration head; and
- no other migration/table, production service, model state, Compass memory,
  or business state is created.

Failure never authorizes fallback to a legacy database, production runtime,
general tool, another executor, or an unpinned owner artifact.

## Evidence and completion boundary

The plan package binds the Platform baseline, G1-A evidence, V5 waiver,
Compass capsule, both plan documents, one task, one operation chain, and the
two-owner review topology. It contains no credentials, signatures, private
keys, task payloads, patch bytes, local paths, database URLs, or business data.

G1-B is complete only when:

1. the package and static tests pass against the exact files;
2. the same Platform candidate full SHA is reviewed by both V5 and Compass;
3. each owner returns `ACK`, or every `CONFLICT` is fixed and re-reviewed;
4. both owner reviews report High=0 and Medium=0;
5. Platform repeats source read-back for both owner blobs;
6. focused tests, G1-A tests, Ruff, format, compileall, diff/show checks pass;
7. the Platform worktree is clean; and
8. no runtime, model, tool, network, database, Docker, deployment, push, merge,
   dogfood execution, or FDE action occurred.

Completion authorizes only a later user decision on whether to execute the
R1a implementation plan.

## Stop conditions

Stop and report a conflict if any fixed commit, path, or hash cannot be read;
V5 and Compass assign the same component incompatible meanings; the current
Protocol V2 vocabulary cannot represent the result; the HMAC secret would need
to be persisted or exposed to Compass; verifier independence cannot be
preserved; executor-authenticated evidence cannot be added without a
versioned contract and forward migration; the task requires a model, network,
general tool, repository write,
production data, or FDE input; or either owner retains a High or Medium
finding.

Do not reinterpret a stop as permission to widen the plan. Platform must
return the precise conflict and wait for a versioned owner decision or new user
authorization.
