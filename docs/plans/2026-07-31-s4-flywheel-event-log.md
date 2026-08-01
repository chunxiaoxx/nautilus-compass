# Compass S4 Flywheel Event Log Implementation Plan

> **For Codex:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Admit strict ExperiencePacket episode events into an append-only, idempotent SQLite log with safe quarantine receipts and a deterministic derived-state reducer.

**Architecture:** `gep.flywheel_event` owns canonical serialization, hashes, and fail-closed envelope validation. `gep.flywheel_log` owns transactional append, duplicate/conflict/quarantine receipts, restart-safe reads, the thin `CompassS4AgentHarness`, and a pure episode-state reducer. SQLite is an immutable event log, not a mutable workflow engine.

**Tech Stack:** Python 3.10+ standard library (`dataclasses`, `datetime`, `hashlib`, `json`, `sqlite3`), pytest, Ruff.

---

### Task 1: Specify and implement the strict FlywheelEvent envelope

**Files:**
- Create: `tests/gep/test_flywheel_event.py`
- Create: `gep/flywheel_event.py`

**Step 1: Write the failing envelope tests**

Cover:

- a valid `episode` mapping round-trips through canonical normalized JSON;
- `payload_hash` is SHA-256 over canonical ExperiencePacket payload bytes;
- `event_hash` is deterministic and derived rather than accepted from input;
- unknown envelope and payload keys fail closed;
- wrong schema/event kind/payload schema fail closed;
- empty IDs, bool/non-positive `agent_id`, non-UTC timestamps, malformed hashes,
  payload/envelope episode mismatch, NaN, and hash mismatch are rejected;
- input mappings and nested payloads are copied so later caller mutation cannot
  alter the event.

Use a helper resembling:

```python
def valid_mapping(**overrides):
    payload = {"episode_id": "episode-1", "task": "verify a fix"}
    event = {
        "schema_version": "compass.flywheel.event.v1",
        "event_kind": "episode",
        "source_event_id": "source-1",
        "episode_id": "episode-1",
        "parent_event_id": None,
        "agent_id": 7,
        "occurred_at": "2026-07-31T12:00:00Z",
        "payload_schema": "compass.experience_packet.v0",
        "payload": payload,
        "payload_hash": hash_payload(payload),
    }
    event.update(overrides)
    return event
```

**Step 2: Run tests to verify RED**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_event.py
```

Expected: collection fails because `gep.flywheel_event` does not exist.

**Step 3: Implement the minimal envelope**

Add:

```python
SCHEMA_VERSION = "compass.flywheel.event.v1"
PAYLOAD_SCHEMA = "compass.experience_packet.v0"
EVENT_KIND_EPISODE = "episode"

class FlywheelEventError(ValueError):
    def __init__(self, reason_code: str, message: str): ...

@dataclass(frozen=True)
class FlywheelEvent:
    schema_version: str
    event_kind: str
    source_event_id: str
    episode_id: str
    parent_event_id: str | None
    agent_id: int
    occurred_at: str
    payload_schema: str
    payload: Mapping[str, Any]
    payload_hash: str

    @property
    def event_hash(self) -> str: ...

    def to_mapping(self) -> dict[str, Any]: ...
```

Add `hash_payload`, `canonical_payload_bytes`, `canonical_event_bytes`, and
`event_from_mapping`. Use `ExperiencePacket(**payload)` plus `to_frontmatter` to
normalize and strictly reject unknown payload fields. Require payload
`episode_id` to be present and equal the envelope value. Use `MappingProxyType`
or an immutable copied representation internally.

**Step 4: Run tests to verify GREEN**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_event.py
```

Expected: all envelope tests pass.

**Step 5: Commit**

```text
git add gep/flywheel_event.py tests/gep/test_flywheel_event.py
git commit -m "feat(s4): add strict flywheel episode envelope"
```

### Task 2: Specify and implement append-only SQLite admission

**Files:**
- Create: `tests/gep/test_flywheel_log.py`
- Create: `gep/flywheel_log.py`

**Step 1: Write failing log tests**

Cover:

- first valid event returns `accepted` and inserts one row;
- 100 replays return one `accepted`, then 99 `duplicate`, and one row total;
- reopening the database preserves canonical envelope bytes and event hash;
- same source ID with changed content returns `conflict` and cannot overwrite;
- same episode ID under a different source returns `conflict`;
- unregistered agent returns `quarantined` with reason `unregistered_agent`;
- invalid schema and payload hash mismatch create safe quarantine receipts;
- quarantine rows contain no raw payload, task, link, password, or unknown key;
- a SQLite write failure raises rather than returning acceptance.

**Step 2: Run tests to verify RED**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_log.py
```

Expected: collection fails because `gep.flywheel_log` does not exist.

**Step 3: Implement receipts and tables**

Add:

```python
@dataclass(frozen=True)
class AppendReceipt:
    status: Literal["accepted", "duplicate", "conflict", "quarantined"]
    source_event_id: str | None
    episode_id: str | None
    event_hash: str | None
    reason_code: str | None = None

class FlywheelEventLog:
    def __init__(self, path, registered_agent_ids): ...
    def append(self, raw_event: Mapping[str, Any]) -> AppendReceipt: ...
    def get(self, source_event_id: str) -> FlywheelEvent | None: ...
    def list_events(self) -> tuple[FlywheelEvent, ...]: ...
    def count_events(self) -> int: ...
    def list_quarantine(self) -> tuple[dict[str, Any], ...]: ...
    def close(self) -> None: ...
```

Create `flywheel_events` with unique `source_event_id` and `episode_id`, storing
canonical envelope JSON and derived event hash. Create `flywheel_quarantine`
with only reason, safe source/episode IDs, fingerprint, and timestamp. Use
explicit transactions and never update accepted rows.

**Step 4: Run tests to verify GREEN**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_log.py
```

Expected: all log tests pass.

**Step 5: Commit**

```text
git add gep/flywheel_log.py tests/gep/test_flywheel_log.py
git commit -m "feat(s4): persist idempotent flywheel event log"
```

### Task 3: Add the thin harness and pure reducer

**Files:**
- Modify: `gep/flywheel_log.py`
- Modify: `tests/gep/test_flywheel_log.py`

**Step 1: Write failing harness and reducer tests**

Cover:

- `CompassS4AgentHarness.record(mapping)` delegates to the log and returns its
  immutable receipt;
- a one-shot fixture records and reads one episode without chat or runtime
  framework imports;
- `reduce_episode_states(events)` returns `awaiting_verdict` with episode,
  source, and event hash lineage;
- reducer output is deterministic and does not mutate inputs;
- empty input returns an empty mapping.

**Step 2: Run focused tests to verify RED**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_log.py -k "harness or reducer"
```

Expected: failures because harness/reducer names do not exist.

**Step 3: Implement minimal harness and reducer**

Add:

```python
@dataclass(frozen=True)
class EpisodeState:
    episode_id: str
    state: Literal["awaiting_verdict"]
    source_event_id: str
    event_hash: str

class CompassS4AgentHarness:
    def __init__(self, event_log: FlywheelEventLog): ...
    def record(self, raw_event: Mapping[str, Any]) -> AppendReceipt: ...

def reduce_episode_states(events: Iterable[FlywheelEvent]) -> dict[str, EpisodeState]: ...
```

Do not add scheduling, callbacks, network I/O, or policy actions.

**Step 4: Run tests to verify GREEN**

Run:

```text
python -m pytest -q tests/gep/test_flywheel_log.py
```

Expected: all log, harness, and reducer tests pass.

**Step 5: Commit**

```text
git add gep/flywheel_log.py tests/gep/test_flywheel_log.py
git commit -m "feat(s4): add deterministic harness and episode reducer"
```

### Task 4: Verify scope, compatibility, and quality

**Files:**
- Verify: `gep/experience_packet.py`
- Verify: `gep/flywheel_event.py`
- Verify: `gep/flywheel_log.py`
- Verify: `tests/gep/test_flywheel_event.py`
- Verify: `tests/gep/test_flywheel_log.py`

**Step 1: Run focused and full GEP tests**

```text
python -m pytest -q tests/gep/test_flywheel_event.py tests/gep/test_flywheel_log.py
python -m pytest -q tests/gep
```

Expected: all pass.

**Step 2: Run static checks**

```text
uvx --offline ruff check gep/flywheel_event.py gep/flywheel_log.py tests/gep/test_flywheel_event.py tests/gep/test_flywheel_log.py
git diff --check origin/main...HEAD
```

Expected: both pass.

**Step 3: Review non-goals**

Confirm the diff does not touch daemon, scheduler, `ingest_obs`, PoI, recall,
capsule generation, governance, Feishu, FDE, robot execution, or model training.

**Step 4: Run a fresh-process restart replay**

Create a temporary database, record one event in one Python process, reopen it in
a second process, and assert the same canonical envelope and event hash are read.

Expected: one accepted event, no duplicate bytes, deterministic reducer state.

**Step 5: Prepare PR**

```text
git status --short --branch
git log --oneline origin/main..HEAD
```

Expected: only the design, plan, event/log modules, and focused tests differ from
main.
