# Compass S4 Verdict Attestation Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add independently verified, hash-bound verdict events to the existing append-only S4 flywheel without allowing verdicts to mutate PoI, recall, routing, capsules, or model weights.

**Architecture:** Extend the existing `compass.flywheel.event.v1` envelope with one exact `verdict` payload schema, evolve the single SQLite journal transactionally from one-event-per-episode to a multi-event journal, and derive episode status with a pure order-independent reducer. The action agent and verifier remain separate registered identities; raw evidence stays outside Compass and is represented only by hashes.

**Tech Stack:** Python 3.9+, frozen dataclasses, canonical JSON, SHA-256, SQLite transactions/partial indexes/immutable triggers, pytest, Ruff, setuptools wheel smoke tests.

---

### Task 1: Define the strict VerdictPacket v0 schema

**Files:**
- Create: `gep/verdict_packet.py`
- Create: `tests/gep/test_verdict_packet.py`

**Step 1: Write the failing constants and round-trip tests**

Create tests that require the exact outcome/verifier enums, all mandatory hashes,
an optional environment hash, an optional safe failure token, immutable values,
and detached JSON-ready output.

```python
from dataclasses import FrozenInstanceError

import pytest

from gep.verdict_packet import (
    OUTCOMES,
    VERIFIER_KINDS,
    VerdictPacket,
    from_args,
    to_payload,
)


H1 = "sha256:" + "1" * 64
H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64


def test_verdict_packet_round_trip_is_exact_and_immutable():
    packet = from_args(
        episode_id="episode-1",
        episode_event_hash=H1,
        outcome="success",
        verifier_kind="software_test",
        verifier_version="pytest-8.4",
        verifier_policy_hash=H2,
        evidence_hash=H3,
        failure_class=None,
    )
    assert OUTCOMES == frozenset({"success", "failure", "partial", "inconclusive"})
    assert "physical" in VERIFIER_KINDS
    assert to_payload(packet)["episode_id"] == "episode-1"
    with pytest.raises(FrozenInstanceError):
        packet.outcome = "failure"
```

**Step 2: Run the focused test and verify RED**

Run:

```powershell
python -m pytest tests/gep/test_verdict_packet.py -q
```

Expected: FAIL during collection because `gep.verdict_packet` does not exist.

**Step 3: Implement the frozen schema and exact validators**

Implement:

```python
@dataclass(frozen=True)
class VerdictPacket:
    episode_id: str
    episode_event_hash: str
    outcome: VerdictOutcome
    verifier_kind: VerifierKind
    verifier_version: str
    verifier_policy_hash: str
    evidence_hash: str
    environment_fingerprint_hash: str | None = None
    failure_class: str | None = None
```

Use full-match validators for `sha256:[0-9a-f]{64}` and safe taxonomy tokens
`[a-z0-9][a-z0-9_.-]{0,63}`. Reject booleans/non-strings, whitespace-only IDs or
versions, unsupported enum values, and uppercase/bare hashes. S4-3 does not infer
an outcome from `failure_class`; it validates the token only. `to_payload()` must
return a detached dictionary containing every dataclass field.

**Step 4: Add fail-closed type and unknown-field tests**

Cover every field with parametrized invalid values. Verify direct dataclass
construction and `from_args()` apply the same validation. Verify `to_payload()`
rejects non-packets and no free-form reason/evidence field exists.

**Step 5: Run GREEN and the existing ExperiencePacket tests**

Run:

```powershell
python -m pytest tests/gep/test_verdict_packet.py tests/gep/test_experience_packet.py -q
```

Expected: all selected tests PASS.

**Step 6: Commit the schema slice**

```powershell
git add gep/verdict_packet.py tests/gep/test_verdict_packet.py
git commit -m "feat(s4): add strict verdict packet schema"
```

### Task 2: Extend the common envelope without changing episode hashes

**Files:**
- Modify: `gep/flywheel_event.py`
- Modify: `tests/gep/test_flywheel_event.py`

**Step 1: Add failing verdict-envelope tests**

Add a `valid_verdict_mapping()` fixture with:

```python
{
    "schema_version": "compass.flywheel.event.v1",
    "event_kind": "verdict",
    "source_event_id": "verdict-source-1",
    "episode_id": "episode-1",
    "parent_event_id": "episode-source-1",
    "agent_id": 8,
    "occurred_at": "2026-08-01T01:00:00Z",
    "payload_schema": "compass.verdict_packet.v0",
    "payload": verdict_payload,
    "payload_hash": hash_payload_for_kind("verdict", verdict_payload),
}
```

Require exact kind/schema pairing, VerdictPacket normalization, episode-ID
matching, canonical UTF-8 JSON, deterministic event hash, and unknown-key
rejection.

**Step 2: Pin the S4-2 compatibility hash before implementation**

Add one golden episode fixture and assert its canonical envelope bytes and
`event_hash` equal the values produced by the current S4-2 implementation. Do
not regenerate the expected value after changing code.

Run:

```powershell
python -m pytest tests/gep/test_flywheel_event.py -q
```

Expected: existing episode tests PASS and new verdict tests FAIL.

**Step 3: Add payload dispatch to `FlywheelEvent`**

Retain:

```python
SCHEMA_VERSION = "compass.flywheel.event.v1"
EVENT_KIND_EPISODE = "episode"
PAYLOAD_SCHEMA = "compass.experience_packet.v0"  # compatibility alias
```

Add `EVENT_KIND_VERDICT` and `VERDICT_PAYLOAD_SCHEMA`. Replace the episode-only
normalizer with an exact dispatch table keyed by
`(event_kind, payload_schema)`. Experience packets continue through the existing
normalizer; verdict packets go through `VerdictPacket` and `to_payload()`.

Keep the envelope field set and canonical JSON function unchanged. Require a
non-null `parent_event_id` for verdict envelopes, but leave parent existence and
trust checks to journal admission.

**Step 4: Verify wrong-pair and compatibility behavior**

Test that:

- `episode` plus verdict schema is rejected;
- `verdict` plus experience schema is rejected;
- unknown kinds/schemas/keys are rejected;
- verdict payload `episode_id` must match the envelope;
- verdict payload hash mismatch is rejected;
- the pinned S4-2 episode bytes and hash are unchanged.

Run:

```powershell
python -m pytest tests/gep/test_flywheel_event.py tests/gep/test_verdict_packet.py -q
```

Expected: all selected tests PASS.

**Step 5: Commit the protocol slice**

```powershell
git add gep/flywheel_event.py tests/gep/test_flywheel_event.py
git commit -m "feat(s4): admit verdict event envelopes"
```

### Task 3: Evolve the one-event SQLite table transactionally

**Files:**
- Modify: `gep/flywheel_log.py`
- Modify: `tests/gep/test_flywheel_log.py`

**Step 1: Write a failing fresh-v2 schema test**

Require `flywheel_events` to expose these stored columns:

```text
source_event_id, event_kind, episode_id, parent_event_id, agent_id,
event_hash, envelope_json, accepted_at
```

Require unique source/event hashes, one episode event per episode, at most one
verdict per verifier and episode, event-kind/episode indexes, and immutable
update/delete triggers.

Run:

```powershell
python -m pytest tests/gep/test_flywheel_log.py -q
```

Expected: the new schema assertion FAILS against the S4-2 table.

**Step 2: Write the legacy migration fixture before migration code**

Build a database with the exact S4-2 table, triggers, one canonical episode row,
and `PRAGMA user_version = 0`. Record its canonical `envelope_json`, event hash,
source ID, episode ID, and accepted timestamp.

The test opens that database with the new `FlywheelEventLog` and requires:

- one accepted event after migration;
- byte-for-byte identical envelope JSON;
- identical event hash and accepted timestamp;
- `event_kind == "episode"` in stored columns;
- `PRAGMA user_version == 2`;
- successful close/reopen.

Add a corrupt legacy fixture whose stored bytes or hash disagree; opening it must
raise and leave the original schema/row intact after rollback.

**Step 3: Implement `_ensure_schema()` and fail-closed detection**

Within the constructor's existing `BEGIN IMMEDIATE` transaction:

1. If no table exists, create v2 directly.
2. If the exact legacy columns exist, validate every row using canonical event
   parsing, then migrate.
3. If exact v2 columns exist, validate schema version/indexes and continue.
4. Any unknown or partial schema raises without mutation.

Use a temporary legacy table name only inside the transaction. Drop/recreate the
old immutability triggers deliberately, copy rows with the new indexed columns,
compare counts and bytes, install v2 triggers/indexes, set `user_version = 2`,
then remove the temporary table. Never rewrite canonical envelope bytes.

**Step 4: Make append storage generic while preserving episode behavior**

Insert `event_kind`, `parent_event_id`, and `agent_id` from the normalized event.
Change the old episode-ID collision query to apply only to `event_kind='episode'`.
Keep `AppendReceipt`, quarantine redaction, source idempotency, restart behavior,
and all S4-2 public methods backward compatible.

**Step 5: Run migration and complete existing log tests**

Run:

```powershell
python -m pytest tests/gep/test_flywheel_log.py -q
```

Expected: all log tests PASS, including migration rollback and original episode
idempotency tests.

**Step 6: Commit the journal migration slice**

```powershell
git add gep/flywheel_log.py tests/gep/test_flywheel_log.py
git commit -m "feat(s4): evolve flywheel journal for linked events"
```

### Task 4: Enforce independent verifier and parent-hash admission

**Files:**
- Modify: `gep/flywheel_log.py`
- Modify: `tests/gep/test_flywheel_log.py`
- Create: `tests/gep/test_verdict_flow.py`

**Step 1: Write the valid one-shot flow test**

Construct the log with action agent `7` and verifier `8`:

```python
log = FlywheelEventLog(
    path,
    registered_agent_ids={7, 8},
    registered_verifier_ids={8},
)
```

Append an episode from agent 7, then a verdict from agent 8 whose
`parent_event_id` and `episode_event_hash` bind to that accepted episode. Require
two durable events, complete read-back, and correct duplicate behavior after
reopen.

Run:

```powershell
python -m pytest tests/gep/test_verdict_flow.py -q
```

Expected: FAIL because the constructor and verdict admission do not yet exist.

**Step 2: Add verifier-role configuration without a new registry**

Add a backward-compatible optional `registered_verifier_ids=()` constructor
argument. Validate positive non-bool integers and require the verifier set to be
a subset of registered agents. The caller remains the identity authority.

**Step 3: Add verdict lineage admission before insert**

For `event_kind == "verdict"`, enforce in this order:

1. verifier identity is registered for that role;
2. parent source event exists;
3. parent kind is `episode`;
4. parent and child episode IDs match;
5. payload `episode_event_hash` matches parent `event_hash`;
6. verifier ID differs from parent action `agent_id`;
7. no verdict from this verifier already exists for the episode.

Use stable reason codes:

```text
unregistered_verifier
orphan_parent
invalid_parent_kind
parent_episode_mismatch
episode_event_hash_mismatch
self_verdict
verifier_episode_conflict
```

All failures produce safe quarantine receipts; none append an accepted row.

**Step 4: Add the full rejection matrix**

Write one focused test for each reason code plus unknown keys, altered evidence
hash, duplicate exact event, same source with changed content, and restart.
Include a secret string in each unsafe raw mapping and assert it never appears in
the database file, accepted table, or quarantine projection.

**Step 5: Run GREEN and regression tests**

Run:

```powershell
python -m pytest tests/gep/test_verdict_flow.py tests/gep/test_flywheel_log.py -q
```

Expected: all selected tests PASS.

**Step 6: Commit the trust-boundary slice**

```powershell
git add gep/flywheel_log.py tests/gep/test_flywheel_log.py tests/gep/test_verdict_flow.py
git commit -m "feat(s4): enforce independent verdict admission"
```

### Task 5: Derive verified and conflicting episode state purely

**Files:**
- Modify: `gep/flywheel_log.py`
- Modify: `tests/gep/test_flywheel_log.py`
- Modify: `tests/gep/test_verdict_flow.py`

**Step 1: Write failing reducer-state tests**

Extend `EpisodeState` expectations to cover:

```python
EpisodeState(
    episode_id="episode-1",
    state="verified",
    source_event_id="episode-source-1",
    event_hash=episode_hash,
    verified_outcome="success",
    verdict_event_hashes=(verdict_hash,),
)
```

Add cases for:

- episode only -> `awaiting_verdict`;
- only inconclusive verdicts -> `awaiting_verdict`;
- one success -> `verified/success`;
- several independent successes -> `verified/success`;
- success plus inconclusive -> `verified/success`;
- success plus failure -> `verdict_conflict`, no verified outcome;
- every permutation returns the same state and sorted verdict hashes;
- orphan or wrong-parent event passed directly to the reducer raises.

Run:

```powershell
python -m pytest tests/gep/test_flywheel_log.py tests/gep/test_verdict_flow.py -q
```

Expected: new reducer tests FAIL.

**Step 2: Extend the immutable derived-state type**

Retain the original four fields and add defaults:

```python
verified_outcome: VerdictOutcome | None = None
verdict_event_hashes: tuple[str, ...] = ()
```

Expand `state` to `awaiting_verdict | verified | verdict_conflict`.

**Step 3: Implement an order-independent two-pass reducer**

First collect exactly one episode event per episode. Then validate/group verdicts
by parent episode. Exclude `inconclusive` from the conclusive outcome set. Derive
state from the set, sort verdict hashes, and return a mapping sorted by episode
ID. Do not mutate events, payloads, iterables, or the journal.

**Step 4: Run RED/GREEN regression and commit**

Run:

```powershell
python -m pytest tests/gep/test_flywheel_log.py tests/gep/test_verdict_flow.py -q
```

Expected: all selected tests PASS.

Commit:

```powershell
git add gep/flywheel_log.py tests/gep/test_flywheel_log.py tests/gep/test_verdict_flow.py
git commit -m "feat(s4): derive verdict-backed episode state"
```

### Task 6: Prove packaging and Python-version compatibility

**Files:**
- Modify if required: `pyproject.toml`
- Modify: `.github/workflows/ci.yml`
- Create: `tests/gep/test_verdict_wheel_smoke.py`

**Step 1: Write the installed-wheel smoke test**

Build the wheel, install it into a temporary virtual environment, and run a
small script importing:

```python
from gep.verdict_packet import VerdictPacket
from gep.flywheel_event import EVENT_KIND_VERDICT
from gep.flywheel_log import CompassS4AgentHarness, FlywheelEventLog
```

The script must append one episode and one software-test verdict, reopen the
database, and print the derived verified outcome. It must not import chat,
Feishu, robot SDK, daemon, recall, capsule, or `proof/poi_*` modules.

**Step 2: Run the smoke test and fix only demonstrated packaging gaps**

Run:

```powershell
python -m pytest tests/gep/test_verdict_wheel_smoke.py -q
```

Expected before any packaging fix: either PASS because `gep` already includes
the module, or a specific FAIL that justifies the minimal `pyproject.toml`
change. Do not edit packaging speculatively.

**Step 3: Ensure the existing CI matrix executes all GEP tests**

Verify the matrix still includes Python 3.9, 3.10, and 3.13 and that its GEP
command discovers the new files. Change the workflow only if the new tests are
not already covered.

**Step 4: Run local packaging and GEP verification**

Run:

```powershell
python -m pytest tests/gep -q
python -m ruff check gep tests/gep
python -m build
```

Expected: all GEP tests PASS, Ruff reports no errors, and sdist/wheel build with
exit code 0.

**Step 5: Commit the compatibility slice**

Stage only files that actually changed:

```powershell
git add tests/gep/test_verdict_wheel_smoke.py pyproject.toml .github/workflows/ci.yml
git commit -m "test(s4): prove verdict wheel compatibility"
```

If `pyproject.toml` or the workflow did not need changes, omit them from `git add`.

### Task 7: Independent review and final evidence gate

**Files:**
- Review: `gep/verdict_packet.py`
- Review: `gep/flywheel_event.py`
- Review: `gep/flywheel_log.py`
- Review: `tests/gep/`
- Review: `docs/plans/2026-08-01-s4-verdict-attestation-design.md`

**Step 1: Run the complete fresh verification set**

Run from the isolated worktree:

```powershell
python -m pytest tests/gep -q
python -m ruff check gep tests/gep
python -m build
git diff --check origin/main...HEAD
git status --short --branch
```

Expected: zero failed tests, zero Ruff errors, build exit 0, no whitespace
errors, and only intentional branch commits.

**Step 2: Run the declared Python-floor matrix**

Use the repository's existing CI/tox/matrix mechanism or available interpreters
to run `tests/gep` on Python 3.9, 3.10, and 3.13. Record exact interpreter
versions and pass counts. If a declared interpreter is unavailable locally, the
PR CI result is required before claiming compatibility.

**Step 3: Request independent code review**

The reviewer must check:

- action/verifier separation cannot be bypassed through public APIs;
- no raw rejected evidence reaches SQLite;
- S4-2 episode bytes and hashes are unchanged;
- migration is atomic and fail-closed;
- reducer behavior is deterministic under permutation;
- no PoI, recall, route, capsule, model-training, robot-control, or Feishu side
  effect was introduced;
- every design acceptance item has a test or an explicit remaining gate.

Fix all critical/high findings with a failing regression test first. Re-run the
complete verification set after every review fix.

**Step 4: Create the final implementation commit only if needed**

```powershell
git add <specific-reviewed-files>
git commit -m "fix(s4): close verdict review findings"
```

Do not push, merge, or claim SOTA/RSI closure as part of this task. The next
promotion decision is S4-4 and requires held-out replay evidence.
