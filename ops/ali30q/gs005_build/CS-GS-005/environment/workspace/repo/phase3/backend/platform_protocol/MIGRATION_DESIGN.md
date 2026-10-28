# Protocol V2 Task 2 Migration Design

This migration root is derived from the Task 1a contract at
`protocol-v2-contracts-v1` and its canonical conformance vectors. It is not a
domain schema and it does not use the legacy Core metadata root.

| Table | Contract-derived purpose | Stored values |
| --- | --- | --- |
| `platform_schema_version` | Dedicated Alembic version table | Revision identifier only |
| `protocol_identities` | Registered Platform, executor, and verifier identities | Opaque IDs, principal IDs, releases, fixed roles, UTC registration time |
| `protocol_identity_keys` | Public verification key registration | Opaque key and identity IDs, algorithm/version, public key material, fixed status, UTC timestamps |
| `protocol_operations` | Signed operation envelopes | Envelope opaque IDs, hashes, versions, UTC expiry, Platform signature, fixed delivery state |
| `protocol_attempts` | Bounded execution attempts | Operation/attempt/executor bindings, release, lease expiry, policy hash, exactly one input or grant hash |
| `protocol_manifests` | Immutable manifest bindings | Manifest hash, operation/attempt/executor bindings, UTC receipt time |
| `protocol_receipts` | Independent signed receipts | Receipt bindings, fixed decision/reason vocabularies, canonical reason-code array, signature, UTC issue time |
| `protocol_outbox` | Protocol delivery metadata | Opaque outbox ID, operation ID, event hash/type, fixed delivery state, UTC timestamps |
| `protocol_audit_events` | Append-only protocol audit metadata | Opaque audit ID, operation ID, event hash/type, UTC timestamp |

`protocol_operations` has no JSON payload column. Attempts, identities, and
keys are normalized into their own tables. The only collection-valued field is
the PostgreSQL receipt reason-code array, whose content is constrained by the
Task 1a validator before future command handling persists it. No table stores
source evidence, human or external account identifiers, credentials, tokens,
or delivery payload bodies.

Composite foreign keys bind Platform and verifier keys to their registered
identity/release, manifests to their exact attempt tuple, and receipts to their
exact manifest tuple. These database constraints preserve the contract chain
even if a future writer bypasses an application-level association lookup.
The registered identity role, principal, and release are immutable after
registration; PostgreSQL triggers also reject a Platform/executor role mismatch
or a verifier receipt whose principal matches the bound executor.
