# G1-A automatic constitutional gate design

**Status:** approved planning target; implementation and runtime not authorized

**Platform owner baseline:**
`ac0323c3cc59da81e734fd1dae8babf7dfe6b0c2`

## Outcome

G1-A is a Platform-owned, pure, fail-closed gate that decides only whether an
R1a implementation plan may be drafted. It converts immutable owner evidence
into exactly one derived result:

- `ready_for_r1a_plan` with no reason codes; or
- `blocked` with the complete, sorted reason-code inventory.

The input document cannot select its own outcome. A ready result grants only
`draft_r1a_implementation_plan`; it grants no runtime, repository write,
database, model, network, tool, deployment, business workflow, FDE, push, or
merge authority.

## Why a new version is required

`m1-r1a-plan-admission-v1` couples plan readiness to a fresh O1 runtime
acceptance whose V5 and Compass revisions equal the current owner proposals.
The active constitution simultaneously prohibits runtime and database work.
Changing v1 evidence fields without a new O1 run would be a false attestation.

G1-A therefore introduces a versioned planning-only admission. It preserves v1
unchanged, treats the accepted O1 artifact only as historical capability
provenance, and source-binds current V5 and Compass blobs separately. Historical
O1 proves neither current runtime readiness nor current owner approval.

## Fixed V5 input

The V5 input is immutable for this gate:

| Field | Required value |
| --- | --- |
| authority commit | `f560be28ecac550e754eff2b82e36ea91ecad0b6` |
| proposal commit | `cdd55315f03c145e7d83d5a0eddbfeeb5d951c94` |
| authorization path | `docs/contracts/v5-r1a-plan-only-authorization-v1.json` |
| file SHA-256 | `9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6` |

Platform must independently prove all of the following from the configured V5
GitHub authority clone:

1. both full commits resolve as commits;
2. the authority commit is an ancestor of the proposal commit;
3. `git show <proposal>:<path>` returns the exact bytes whose SHA-256 is pinned;
4. the JSON has an exact field schema and exact fixed values;
5. `runtime_authorized` is `false`;
6. the only allowed action is `draft_r1a_implementation_plan`;
7. runtime implementation, model, tools, network, cloud, Docker, file writes,
   database, deployment, merge, and FDE remain prohibited; and
8. V5 grants neither Platform nor Compass repository-write authority.

The local `authority_clone_path` string inside the signed blob is descriptive
provenance only. Platform trust comes from its injected authority repository
plus commit/path/hash read-back, never from a path supplied by the blob.

## Required Compass owner input

Current verified fact: Compass authority commit
`37efc4fc2f7455202c94515b29314af9e5e2e16e` resolves, but
`docs/contracts/m1-r1a-grounding-capsule-v1.json` is absent there. G1-A must
therefore currently derive `blocked` with `compass_owner_input_missing`.

Platform must not author the missing Compass file. The Compass owner must
submit, from a clean isolated owner worktree:

- a full authority commit and full proposal commit;
- the exact path `docs/contracts/m1-r1a-grounding-capsule-v1.json`;
- SHA-256 of the exact Git blob bytes;
- owner-focused tests and static checks marked passing; and
- a capsule with no raw business, user, conversation, account, credential, or
  local-path data.

The capsule consumer contract has exact fields and fixed semantics:

- owner is `compass` and scope is `no_business_data`;
- workload is the synthetic R1a planning target only;
- the capsule hash is an input to the Platform-owned attempt-scoped binding,
  never equal by definition to `ExecutionAttemptV2.input_ref_hash`;
- derivation owner is Platform;
- one fixed synthetic quality rule may yield `review_required`;
- `drift_write`, `ingest`, `model`, `network`, `recall`, `source_write`, and
  `tool` are all `false`; and
- no experience promotion, memory write, or runtime authorization is present.

Platform reads and parses the blob at the submitted commit. A matching hash of
an unknown or widened JSON shape is insufficient.

## Historical O1 provenance

The gate source-binds the existing accepted O1 artifact by its Platform commit,
fixed path, SHA-256, internal Task 6 revision, and historical V5/Compass
revisions. Its role is exactly `historical_capability_provenance`.

The historical revisions are intentionally not required to equal current owner
proposals. Any attempt to relabel the artifact as current runtime evidence,
execution authorization, or current owner acceptance is rejected.

## Exact decision pipeline

```text
parse exact schema
-> verify planning-only authorization is all false except the named action
-> read historical O1 commit/path/hash/internal bindings
-> read current V5 commit ancestry/path/hash/JSON scope
-> read current Compass commit ancestry/path/hash/JSON scope
-> derive complete blockers
-> compare the document's claimed decision to the derived decision
-> return ready_for_r1a_plan or blocked
```

Every source read occurs before a ready result is returned. A malformed source,
unknown field, wrong value, missing commit, wrong ancestry, wrong path, hash
mismatch, noncanonical JSON, or authority widening raises a fixed admission
violation instead of becoming an alternate decision.

## Fixed blocker vocabulary

- `v5_owner_input_missing`
- `v5_plan_input_pending`
- `compass_owner_input_missing`
- `compass_plan_input_pending`

Invalid or tampered evidence raises `AdmissionViolation`; it is not converted
to a self-selected blocker. Reason codes are unique and canonical-sorted.

## Required negative matrix

G1-A must reject:

- short, unknown, or wrong V5/Compass commits;
- an incorrect ancestry relation;
- wrong authorization or capsule path;
- changed blob bytes or supplied hash;
- extra top-level or nested fields;
- a V5 waiver with any additional allowed action or missing prohibition;
- any `runtime_authorized=true` or other authority flag set to true;
- a Compass capability set to true;
- a capsule whose attempt binding makes `input_ref_hash` equal the capsule hash;
- a historical O1 artifact relabelled as current evidence;
- missing owner input paired with claimed commit, hash, path, tests, or capsule;
- incomplete, duplicated, unsorted, or self-declared decision reasons; and
- any attempt to authorize dogfood operations, a runtime, database, model,
  network, deployment, push, merge, or FDE.

## Evidence and ownership

Platform owns the evaluator, versioned evidence document, source-readback tests,
and final decision. V5 owns only its already frozen waiver. Compass owns only
its capsule proposal. The coordinating conversation transports owner receipts;
it does not become a source of truth.

No new SQL model, migration, queue, service, DMAS ledger, or cross-repository
copy is created. Git owner artifacts remain in their repositories; Platform
stores only immutable pins and the derived planning decision.

## Completion

G1-A is complete only when:

1. V5 exact source read-back passes against the fixed input above;
2. Compass supplies a clean current owner commit and the capsule passes exact
   source and semantic validation;
3. the gate independently derives `ready_for_r1a_plan` with no reasons;
4. focused tests, all Platform protocol tests, Ruff, format, compileall, and
   diff/show checks pass;
5. an independent reviewer reports High=0 and Medium=0; and
6. all worktrees are clean local commits with no push, merge, or deployment.

Until item 2 is satisfied, the only honest terminal report is
`blocked: compass_owner_input_missing`.
