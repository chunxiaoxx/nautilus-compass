# G1-B R1a Ephemeral Executor Key Admission Design

**Goal:** Replace the test-only R1a executor's precomputed Ed25519 key path with one Platform-challenged, process-local, single-use V5 signer while preserving the existing Protocol V2 operation, attempt, evidence, manifest, receipt, audit, and outbox contracts.

## Fixed owner input

- V5 authority baseline: `09660ca8d010fbcf48f37110d65d4d1223162c5c`
- V5 owner proposal: `4c18c5a70c16d1d6797f9b71ff96aa58e5a41a67`
- Contract path: `docs/contracts/m1-r1a-ephemeral-signer-v2.json`
- Contract SHA-256: `798c4cbdc0f209ecb39ec1161366a341b718323b47067a4d3d31630867135dfa`
- Entrypoint: `python-module:nautilus_v5_ephemeral_signer`
- Import policy: `isolated-v5-owner-modules-only-v1`

Platform must read the exact Git object at that full proposal SHA, verify ancestry from the fixed authority baseline, recompute the contract hash, and validate the complete contract allowlist. A branch name, descendant-only claim, copied JSON, or caller-supplied public key is insufficient.

## Trust boundary

Platform remains the only identity, registration, operation, attempt, and evidence authority. V5 owns only the restricted signer process and deterministic synthetic repair action.

The handshake is:

```text
Platform canonical challenge
-> isolated V5 process generates an in-memory Ed25519 key
-> V5 canonical announcement + proof of possession
-> Platform verifies source admission, challenge binding, TTL, identity/release/key, and PoP
-> Platform registers only that public key for the fixed executor
-> Platform issues and claims one bounded attempt whose lease cannot exceed key expiry
-> V5 signs the existing ExecutorExecutionEvidenceV1
-> Platform verifies the signature through the DB-backed registry
```

The private key and attempt secret never enter Platform, the database, logs, audit, outbox, evidence files, or exceptions. The announcement proof is an input to admission, not a new protocol table or durable business record.

## Canonical values

The Platform challenge and V5 announcement use the exact V5 owner formats:

- challenge version `m1-r1a-platform-announce-challenge-v1`;
- announcement version `m1-r1a-ephemeral-signer-announcement-v1`;
- algorithm `ed25519-v1`;
- executor `exec_r1a_synthetic_01`;
- release `rel_r1a_ephemeral_v2`;
- key id `key_r1a_ephemeral_v2`;
- maximum challenge lifetime 120 seconds.

Canonical JSON is UTF-8, sorted keys, compact separators, no NaN, and no CRLF. Duplicate or extra fields, non-canonical bytes, invalid UTC, invalid hashes/identifiers, an expired or overlong challenge, changed challenge bindings, malformed key/signature material, or invalid proof fail closed before registry writes.

## Registration and lifetime

The Platform admission result is a frozen value containing only the fixed executor identity/release/key, public verification material, challenge hash, announcement hash, and UTC validity window.

Registration is idempotent only for the identical fixed identity and identical public material. A changed release, key id, material, role, principal, or registration time is a conflict. The existing identity/key tables remain sufficient for this single local R1a chain; no migration or Protocol V2 schema change is allowed.

Every R1a service entrypoint re-derives source admission and requires the same ephemeral admission value. Operation issuance, attempt claim, and executor-evidence persistence all verify the DB registry contains the admitted public key. The operation and attempt expiry must not exceed the ephemeral admission expiry. A missing, expired, revoked, changed, or unregistered key fails before any operation/attempt/evidence/audit/outbox write.

## Non-goals

- No Task 5 vertical-chain implementation in this worktree.
- No Task 6 failure matrix or runtime acceptance evidence.
- No model, network, general RPC, shell, ToolGateway, Docker, production database, deployment, push, merge, FDE, Flywheel, or Compass write.
- No new session/task/evidence authority and no competing signing contract.
- No changes to frozen Protocol V2 contracts, conformance vectors, migrations, or existing V5 v1 owner files.

## Acceptance

The Platform follow-up is complete only when exact source read-back, pure challenge/announcement/PoP tests, registration and lease tests, existing R1a/Protocol V2 regressions, Ruff, format, compileall, Git checks, sensitive-capability scans, and an independent review all pass with High=0 and Medium=0. The resulting commit is a prerequisite for resuming the already preserved Task 5 RED; it is not runtime or deployment approval.
