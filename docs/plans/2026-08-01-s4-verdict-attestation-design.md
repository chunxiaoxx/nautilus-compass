# Compass S4 Verdict Attestation Design

## Goal

Add the second immutable fact type to the Compass S4 external post-training
flywheel: an independently produced verdict that is cryptographically bound to
one admitted episode.

S4-3 answers only **what a verifier established about an episode**. It does not
turn that fact into a scalar reward, change recall, update a route preference,
generate a capsule, execute a skill, or train model weights. Those learning
decisions remain later stages with separate replay gates.

## Strategic position

The design combines stable boundaries from several established lines of work
without importing their whole runtime:

- Agent Lightning's separation between agent execution and learning.
- RLDS and LeRobot's episode-oriented trajectory boundary.
- CloudEvents and OpenTelemetry's stable event identity and trace lineage.
- SLSA/in-toto's subject, predicate, attester, and evidence-attestation model.
- Event Sourcing's append-only facts and deterministic replay.
- Waddle and Voyager's reusable executable-skill direction.
- AlphaEvolve and Darwin Godel Machine's evaluator-gated candidate evolution.

Compass occupies the layer those systems do not jointly provide: deciding which
experiences are admissible, independently verified, useful on held-out work,
transferable, distillable, and eventually eligible for forgetting. S4-3 builds
the verification fact needed by that layer; it does not claim the later value
closure already exists.

## Alternatives considered

### A. Directly write a PoI score from the action outcome

This is small but unsafe. The action-producing agent would effectively grade its
own work, one noisy result would immediately affect behavior, and the old mutable
`proof/poi_*` path would become a second authority. Rejected.

### B. Record a verdict and immediately update recall or capsule state

This closes more arrows in one pull request but makes attribution impossible: a
regression could come from verification, scoring, retrieval, or distillation.
It also prevents held-out replay from acting as the promotion gate. Rejected.

### C. Two-stage convergence: independent verdict now, learning later

S4-3 records only verified facts and derives episode state. S4-4 will calibrate
PoICritic and policy candidates from repeated replay evidence. This is the chosen
approach because it creates a measurable signal without allowing that signal to
mutate behavior prematurely.

## Event model

The existing narrow-waist envelope remains
`compass.flywheel.event.v1`. Its field set and canonical hashing algorithm do not
change. S4-3 extends the allowed pair of `event_kind` and `payload_schema`:

| `event_kind` | `payload_schema` | Meaning |
| --- | --- | --- |
| `episode` | `compass.experience_packet.v0` | An action trajectory summary |
| `verdict` | `compass.verdict_packet.v0` | An independent verification fact |

Keeping the envelope at v1 is intentional: S4-2 defined it as the common
protocol for later linked event kinds. Unknown kinds, schemas, and keys still
fail closed. Existing episode bytes and event hashes remain unchanged.

## VerdictPacket v0

`VerdictPacket` is an immutable dataclass with an exact field allowlist:

- `episode_id`: the episode being evaluated.
- `episode_event_hash`: the canonical hash of that admitted episode event.
- `outcome`: exactly `success`, `failure`, `partial`, or `inconclusive`.
- `verifier_kind`: exactly `physical`, `software_test`, `human_review`,
  `external_acceptance`, or `simulation`.
- `verifier_version`: a non-empty version identifier for the verifier.
- `verifier_policy_hash`: a strict `sha256:<64 lowercase hex>` hash of the
  verifier policy, test suite, rubric, or success-detector configuration.
- `evidence_hash`: a strict SHA-256 hash of an external evidence bundle or
  manifest.
- `environment_fingerprint_hash`: an optional strict SHA-256 hash identifying
  the relevant robot, simulator, software, or workflow environment.
- `failure_class`: an optional safe taxonomy token. It is classification, not
  free-form evidence or reasoning.

The envelope's `agent_id` identifies the verifier. Raw sensor streams, videos,
dialogue, attachments, credentials, personal information, customer identities,
URLs, model chain-of-thought, and executable code are not verdict payloads. They
remain in an access-controlled artifact store; Compass receives hashes only.

Neither `reward`, `confidence`, `PoI`, nor `capsule_candidate` appears in this
packet. An inconclusive verdict is evidence that verification ran but does not
assert success or failure.

## Lineage and admission

A verdict is accepted only when all of these checks pass:

1. The envelope and VerdictPacket are exact-schema, canonical JSON.
2. The verifier `agent_id` is both a registered agent and a registered verifier.
3. `parent_event_id` identifies an already admitted `episode` event.
4. The verdict and parent have the same `episode_id`.
5. `episode_event_hash` exactly matches the parent's canonical event hash.
6. The verifier is not the action agent that produced the episode.
7. That verifier has not already emitted a verdict for the same episode.
8. The source ID and event hash do not conflict with accepted history.

The action and verifier may run in one operating-system process for local tests,
but they must use different registered logical identities. Identity is supplied
by the caller; Compass does not create another agent registry.

Orphans, wrong-parent events, wrong hashes, self-verdicts, unregistered
verifiers, repeated-verifier verdicts, unknown schemas, and unsafe values are
quarantined with stable reason codes. Quarantine stores only safe identifiers,
reason codes, and fingerprints, never the rejected raw input.

## Multiple verdicts and conflicts

Different registered verifiers may evaluate the same episode:

- No conclusive verdict: `awaiting_verdict`.
- One or more conclusive verdicts with one shared outcome: `verified`, with that
  outcome exposed separately.
- Two or more different conclusive outcomes: `verdict_conflict`, with no
  inferred reward or winning verdict.
- `inconclusive` verdicts never outvote or dilute a conclusive verdict.

The reducer is order-independent. It sorts lineage hashes and derives the same
state from the same event set regardless of insertion or query order. A conflict
is a durable fact requiring a later explicit resolution event; S4-3 does not
silently prefer a verifier, timestamp, or majority.

## Storage and migration

S4-2's `flywheel_events` table permits only one row per `episode_id`. S4-3 needs
one episode plus zero or more verdict events, so the table becomes a generic
append-only event journal with:

- unique `source_event_id`;
- unique `event_hash`;
- indexed `episode_id` and `event_kind`;
- a partial unique constraint allowing exactly one `episode` event per
  `episode_id`;
- a partial unique constraint allowing at most one `verdict` per verifier and
  episode;
- immutable update/delete triggers.

Opening an S4-2 database performs one transactional, fail-closed migration. The
migration validates every legacy envelope, copies its canonical bytes and hash
unchanged as an `episode` row, verifies row counts, installs the new indexes and
triggers, and only then commits. Any mismatch rolls back the whole migration.
Tests must prove that reopening preserves every legacy byte and event hash.

This is one journal evolution, not a second verdict database or mutable workflow
table. Runtime state remains a pure projection of the journal.

## API evolution

- Add `gep/verdict_packet.py` for VerdictPacket validation and normalization.
- Extend `gep/flywheel_event.py` with exact event-kind/payload-schema dispatch
  while retaining the current episode API and canonical bytes.
- Extend `FlywheelEventLog` to validate parent lineage and verifier roles before
  append.
- Retain `CompassS4AgentHarness.record()` as the single thin structured-event
  entry point.
- Extend `EpisodeState` with `verified_outcome` and sorted verdict hashes while
  preserving its existing episode source ID and event hash fields.
- Extend the pure reducer to derive `awaiting_verdict`, `verified`, or
  `verdict_conflict`.

No daemon, listener, chat import, Feishu path, robot SDK, trainer, or scheduler is
added.

## Security and provenance

S4-3 adopts SLSA-style attestation semantics but does not yet implement a network
trust fabric. The verifier identity, version, policy hash, evidence hash, parent
ID, and parent hash make the local fact content-addressed and replayable.

Cross-machine producers will later require signed attestations such as DSSE
before promotion. That future signature gate must wrap the same canonical event;
it must not change previously accepted event hashes or silently trust a transport
identity.

Code-as-policy and robot skills remain external artifacts. A verdict can attest
to their execution result but cannot cause Compass to execute them.

## Testing strategy

Development is test-first. Required coverage includes:

- strict VerdictPacket construction, normalization, immutability, enum and hash
  validation;
- unchanged S4-2 episode canonical bytes and hashes;
- valid episode-to-verdict admission and read-back;
- orphan, wrong parent, wrong episode hash, wrong episode ID, self-verdict,
  unregistered verifier, repeated verifier, and unknown-key rejection;
- duplicate and source/event-hash conflict behavior;
- one episode with consistent, inconclusive, and conflicting verifier sets;
- reducer order independence and no input mutation;
- transactional S4-2 database migration with byte/hash preservation and rollback
  on corrupt legacy data;
- restart persistence and append-only trigger enforcement;
- quarantine proof that raw sensitive input is never persisted;
- installed-wheel imports and one-shot harness use;
- Python 3.9, 3.10, and 3.13 CI compatibility.

Focused tests, the full GEP suite, Ruff, wheel build/install smoke tests, and
`git diff --check` must pass before completion.

## Evaluation after S4-3

S4-3 creates a trustworthy measured signal but does not claim improvement. S4-4
may use repeated verdict events to construct PoICritic and policy candidates,
but promotion remains blocked until an experiment holds model, task budget, and
runtime constant and shows positive held-out delta without protected-class
regression.

The longer-term benchmark stack has two independent axes:

1. Memory competence: LongMemEval and MemoryAgentBench, including knowledge
   updates, temporal reasoning, abstention, and selective forgetting.
2. Experience-to-impact: unseen software, FDE, simulation, and later physical
   tasks where the only treatment is access to previously verified experience.

Recall accuracy alone is not the product claim. The decisive result is that a
future action succeeds more often, costs less, recovers better, or avoids a
known failure because an independently verified prior experience was selected.

## Non-goals

- No PoI formula or old `proof/poi_*` integration.
- No reward inference, preference update, recall reranking, capsule generation,
  forgetting mutation, or world-model training.
- No LLM judge as the sole authoritative verifier.
- No model-weight SFT, RL, DPO, or distillation.
- No signed cross-machine transport in this pull request.
- No raw trajectory or evidence storage in Compass.
- No robot control loop or skill execution.
- No claim of SOTA or closed RSI loop from schema and storage alone.
