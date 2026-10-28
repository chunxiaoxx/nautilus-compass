# M1 R1a Plan Admission Design

## Scope

This design defines a static, fail-closed overlay for deciding only whether an
M1 R1a implementation plan may be written. It does not authorize a runtime,
model, network, database, deployment, business workflow, or FDE action.

Platform Protocol V2 Task 6 remains the sole adjudicator. Its generic adapter
review template is recorded as `reference_only`: a synthetic M1 planning
decision must not represent itself as a domain adapter or create a second
authority.

## Decision object

`m1-r1a-plan-admission-v1` has exactly these sources:

- Platform O1 candidate provenance and its V5/Compass pin status;
- the V5 G0 owner input; and
- the Compass read-only grounding-capsule owner input.

The parser accepts no extra fields. It derives the decision from those fields;
the document cannot select its own outcome. Evaluation requires an injected,
read-only Git read-back for the three owner authorities. It resolves full
commits, checks ancestry or non-ancestry, and recomputes the pinned Task 6,
O1-evidence, and submitted-capsule SHA-256 values. A
`ready_for_r1a_plan` result only allows a later planning task. It never
authorizes implementation or runtime execution.

Every submitted owner input must name its authority and proposal with full
40-character Git SHAs, report passing owner tests, and set
`runtime_authorized` to `false`. A submitted Compass input must also supply a
64-character capsule hash and an exact all-false capability map for
`drift_write`, `ingest`, `model`, `network`, `recall`, `source_write`, and
`tool`.

## Current read-back

The versioned evidence at
`phase3/backend/docs/evidence/m1-r1a-plan-admission-v1.json` is intentionally
blocked. It records four independently checkable gaps:

1. `platform_o1_historical_candidate`: Platform O1 is labelled historical, so
   its submitted acceptance evidence cannot be reused as a fresh R1a result.
2. `v5_o1_revision_unresolvable`: the O1-attested V5 revision is not resolvable
   in the current V5 GitHub authority clone.
3. `compass_o1_revision_noncanonical`: the O1-attested Compass revision is not
   an ancestor of the current Compass authority branch.
4. `compass_owner_input_missing`: no current, read-only Compass grounding
   capsule owner proposal is supplied.

The absent Compass input uses `null` proposal/capsule bindings and `not_run`
tests; it does not claim unverified hashes or passing tests. The V5 plan-only
waiver is source-bound: its proposal commit is
`cdd55315f03c145e7d83d5a0eddbfeeb5d951c94`, it is reachable from V5 authority
commit `f560be28ecac550e754eff2b82e36ea91ecad0b6`, and the fixed waiver blob
`docs/contracts/v5-r1a-plan-only-authorization-v1.json` hashes to
`9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6`.
This clears the former `v5_g0_pending` blocker but does not resolve the
separate historical O1 V5-revision blocker.

## Unblocking evidence

To replace this blocker decision, each owner must provide a fresh, clean,
versioned, read-only input from its own authority repository. Platform must
then re-verify O1 using those current pins. An independent read-only reviewer
must find High=0 and Medium=0 before the derived result can become
`ready_for_r1a_plan`.

No owner may use this overlay to change another owner's repository, authorize
runtime work, or interpret FDE business data.
