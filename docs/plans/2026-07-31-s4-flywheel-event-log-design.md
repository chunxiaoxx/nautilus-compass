# Compass S4 Flywheel Event Log Design

## Goal

Turn `ExperiencePacket` into the first durable input of the Compass S4 external
post-training flywheel without building a mutable workflow engine. The runtime
boundary is one strict, immutable event protocol. Every later stage will emit a
new linked event instead of editing earlier experience.

This change implements only `episode` admission. Verdict, policy preference,
capsule, and replay events are later PRs.

## Why an append-only event log

The flywheel is heterogeneous: episodes may come from robot harnesses, software
tests, FDE tasks, simulations, or authenticated human workflows. They should not
need separate storage contracts. A stable event envelope is the narrow waist:

```text
episode -> verdict -> policy_preference -> capsule -> replay_episode
```

The output of one stage becomes the input of the next. History is never
overwritten, so reward changes, repairs, forgetting, and promotion decisions keep
their lineage. SQLite supplies transactions, uniqueness, and restart durability;
it is not the business workflow or the source of inferred rewards.

## Event envelope v1

`FlywheelEvent` is immutable and accepts an exact allowlist of fields:

- `schema_version`: exactly `compass.flywheel.event.v1`
- `event_kind`: exactly `episode` in this PR
- `source_event_id`: stable non-empty producer identifier
- `episode_id`: stable non-empty episode identifier
- `parent_event_id`: optional lineage identifier
- `agent_id`: positive integer; booleans are rejected
- `occurred_at`: timezone-aware RFC 3339 UTC timestamp ending in `Z`
- `payload_schema`: exactly `compass.experience_packet.v0`
- `payload`: strict `ExperiencePacket` frontmatter
- `payload_hash`: `sha256:<64 lowercase hex>` over canonical payload JSON

The payload must contain `episode_id`, and it must equal the envelope's
`episode_id`. Unknown envelope or payload fields fail closed. Canonical JSON uses
UTF-8, sorted keys, compact separators, and rejects NaN/Infinity. `event_hash` is
derived from the canonical normalized envelope and is not trusted from input.

The envelope references executable policies and evidence by hashes in future
schemas; it never executes arbitrary code. Code-as-policy artifacts belong in a
sandboxed artifact store with explicit tool and skill versions.

## Admission and idempotency

`CompassS4AgentHarness` is a thin deterministic adapter around `FlywheelEventLog`.
It receives structured mappings from registered runtimes and never imports chat,
Codex, Claude, Feishu, or robot SDK code.

Admission returns an immutable receipt with one of four statuses:

- `accepted`: a new valid event was appended
- `duplicate`: the same `source_event_id` and `event_hash` already exist
- `conflict`: the same `source_event_id` refers to different content
- `quarantined`: schema, hash, timestamp, payload, or agent registration failed

The log receives a set of registered integer agent IDs from its caller. It does
not create another agent registry. Replaying a valid event is idempotent; existing
bytes are never overwritten.

## Storage

The SQLite file contains two append-only tables:

1. `flywheel_events`: accepted canonical envelopes, keyed by
   `source_event_id`, with a unique `event_hash`.
2. `flywheel_quarantine`: safe rejection receipts containing reason code,
   source identifier when safely available, and a fingerprint. Raw unknown input
   is not persisted because it may contain credentials, links, or personal data.

Writes use explicit transactions. The database is reopened in restart tests to
prove persistence. No mutable `pending/finalized/failed` column is added.

## Pure reducer

Runtime state is a derived view, not a mutable source of truth. The first reducer
maps admitted `episode` events to `awaiting_verdict`. Later PRs will extend the
same pure function for linked verdict and promotion events. Given the same ordered
events, it must always return the same state.

## Failure handling

- Invalid schema or unknown keys: quarantine with `invalid_schema`.
- Payload hash mismatch: quarantine with `payload_hash_mismatch`.
- Unregistered agent: quarantine with `unregistered_agent`.
- Existing source ID with different content: quarantine receipt plus `conflict`.
- Duplicate content: return `duplicate`; do not append another event.
- SQLite failure: raise; never report acceptance without a committed row.

## Security and trust boundary

An action-producing agent may submit an episode, but it cannot assign its own
verdict, PoI, capsule promotion, or routing preference. `capsule_candidate` remains
an observation-level hint only; independent later gates decide promotion.

Physical verification will be treated as strong external evidence, not infallible
truth. Sensor, calibration, verifier-version, and environment lineage belong in
later verdict events.

## Acceptance

- Replaying one valid event 100 times produces one accepted row.
- Reopening the database preserves canonical bytes, hashes, and derived state.
- Same source ID with different content cannot overwrite the original.
- Invalid, hash-mismatched, and unregistered events leave safe quarantine receipts.
- A one-shot harness fixture completes without chat/runtime framework imports.
- Focused GEP tests, full GEP tests, Ruff, and `git diff --check` pass.

## Non-goals

- No daemon, scheduler, network listener, or chat dependency.
- No `ingest_obs` integration or existing governance changes.
- No verifier/evaluator join, PoI calculation, reward inference, policy mutation,
  capsule generation, skill execution, Merkle tree, world model, or model training.
- No Feishu, FDE, robot, or buyer-system writes.
