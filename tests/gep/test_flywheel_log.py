import ast
import re
import sqlite3
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

import gep.flywheel_log as flywheel_log_module
from gep.flywheel_event import canonical_event_bytes, event_from_mapping, hash_payload
from gep.flywheel_log import AppendReceipt, FlywheelEventLog


class UnknownFingerprintValue:
    pass


class ExplosiveReprValue:
    def __repr__(self):
        raise RuntimeError("repr must not run")


def valid_mapping(**overrides):
    payload = overrides.pop(
        "payload",
        {"episode_id": "episode-1", "task": "verify a fix"},
    )
    payload_hash = overrides.pop("payload_hash", hash_payload(payload))
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
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


def table_columns(path, table):
    with sqlite3.connect(path) as connection:
        return tuple(row[1] for row in connection.execute(f"PRAGMA table_info({table})"))


@pytest.fixture
def log_and_path(tmp_path):
    path = tmp_path / "flywheel.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    yield event_log, path
    event_log.close()


def test_append_receipt_is_frozen_and_has_the_exact_public_fields():
    receipt = AppendReceipt(
        status="accepted",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash="sha256:" + "0" * 64,
        reason_code=None,
    )

    assert tuple(field.name for field in fields(AppendReceipt)) == (
        "status",
        "source_event_id",
        "episode_id",
        "event_hash",
        "reason_code",
    )
    with pytest.raises(FrozenInstanceError):
        receipt.status = "duplicate"


@pytest.mark.parametrize(
    "registered_agent_ids",
    [(True,), (False,), (0,), (-1,), (1.5,), ("7",), (7, True)],
)
def test_registered_agent_ids_must_be_positive_non_bool_integers(
    tmp_path, registered_agent_ids
):
    path = tmp_path / "invalid-registry.sqlite3"

    with pytest.raises(ValueError, match="positive non-bool integers"):
        FlywheelEventLog(path, registered_agent_ids)

    assert not path.exists()


def test_first_valid_append_is_committed_and_readable(log_and_path):
    event_log, path = log_and_path
    raw = valid_mapping()
    expected = event_from_mapping(raw)

    receipt = event_log.append(raw)

    assert receipt == AppendReceipt(
        status="accepted",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash=expected.event_hash,
        reason_code=None,
    )
    assert event_log.get("source-1") == expected
    assert event_log.get("missing-source") is None
    assert event_log.list_events() == (expected,)
    assert event_log.count_events() == 1
    assert event_log.list_quarantine() == ()

    assert table_columns(path, "flywheel_events") == (
        "source_event_id",
        "episode_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT source_event_id, episode_id, event_hash,
                   typeof(envelope_json), envelope_json, accepted_at
            FROM flywheel_events
            """
        ).fetchone()
        tables = {
            item[0]
            for item in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
            if not item[0].startswith("sqlite_")
        }

    assert row[:4] == ("source-1", "episode-1", expected.event_hash, "blob")
    assert row[4] == canonical_event_bytes(expected)
    assert row[5].endswith("Z")
    assert tables == {"flywheel_events", "flywheel_quarantine"}


def test_accepted_rows_are_immutable_at_the_database_boundary(log_and_path):
    event_log, path = log_and_path
    event_log.append(valid_mapping())

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute(
                "UPDATE flywheel_events SET event_hash = ? WHERE source_event_id = ?",
                ("sha256:" + "0" * 64, "source-1"),
            )

    assert event_log.get("source-1") == event_from_mapping(valid_mapping())


def test_replaying_the_same_event_100_times_is_idempotent(log_and_path):
    event_log, _ = log_and_path
    raw = valid_mapping()

    receipts = [event_log.append(raw) for _ in range(100)]

    assert receipts[0].status == "accepted"
    assert [receipt.status for receipt in receipts[1:]] == ["duplicate"] * 99
    assert all(receipt.event_hash == receipts[0].event_hash for receipt in receipts)
    assert all(receipt.reason_code is None for receipt in receipts)
    assert event_log.count_events() == 1
    assert event_log.list_quarantine() == ()


def test_reopen_preserves_canonical_envelope_bytes_and_event_hash(tmp_path):
    path = tmp_path / "restart.sqlite3"
    raw = valid_mapping(
        payload={
            "episode_id": "episode-1",
            "task": "验证重启恢复",
            "tool_chain": ["inspect", "verify"],
        }
    )
    expected = event_from_mapping(raw)
    first_log = FlywheelEventLog(path, registered_agent_ids={7})
    first_log.append(raw)
    with sqlite3.connect(path) as connection:
        before = connection.execute(
            "SELECT envelope_json, event_hash FROM flywheel_events"
        ).fetchone()
    first_log.close()

    reopened = FlywheelEventLog(path, registered_agent_ids={7})
    try:
        restored = reopened.get("source-1")
        with sqlite3.connect(path) as connection:
            after = connection.execute(
                "SELECT envelope_json, event_hash FROM flywheel_events"
            ).fetchone()

        assert restored == expected
        assert canonical_event_bytes(restored) == canonical_event_bytes(expected)
        assert before == after == (canonical_event_bytes(expected), expected.event_hash)
        assert reopened.list_events() == (expected,)
        assert reopened.count_events() == 1
    finally:
        reopened.close()


def test_same_source_with_changed_content_conflicts_without_overwrite(log_and_path):
    event_log, path = log_and_path
    original = valid_mapping()
    changed = valid_mapping(
        payload={"episode_id": "episode-1", "task": "changed content"}
    )
    original_event = event_from_mapping(original)
    changed_event = event_from_mapping(changed)
    event_log.append(original)

    receipt = event_log.append(changed)

    assert receipt == AppendReceipt(
        status="conflict",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash=changed_event.event_hash,
        reason_code="source_event_conflict",
    )
    assert event_log.count_events() == 1
    assert event_log.get("source-1") == original_event
    assert event_log.list_quarantine()[0]["reason_code"] == "source_event_conflict"
    with sqlite3.connect(path) as connection:
        stored = connection.execute(
            "SELECT envelope_json, event_hash FROM flywheel_events"
        ).fetchone()
    assert stored == (canonical_event_bytes(original_event), original_event.event_hash)


def test_same_episode_under_another_source_conflicts_and_is_quarantined(log_and_path):
    event_log, _ = log_and_path
    event_log.append(valid_mapping())
    competing = valid_mapping(source_event_id="source-2")
    competing_event = event_from_mapping(competing)

    receipt = event_log.append(competing)

    assert receipt == AppendReceipt(
        status="conflict",
        source_event_id="source-2",
        episode_id="episode-1",
        event_hash=competing_event.event_hash,
        reason_code="episode_id_conflict",
    )
    assert event_log.count_events() == 1
    assert event_log.get("source-2") is None
    assert event_log.list_quarantine()[0]["reason_code"] == "episode_id_conflict"


def test_unregistered_agent_is_quarantined_without_an_event_row(log_and_path):
    event_log, _ = log_and_path
    raw = valid_mapping(agent_id=8)
    expected_hash = event_from_mapping(raw).event_hash

    receipt = event_log.append(raw)

    assert receipt == AppendReceipt(
        status="quarantined",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash=expected_hash,
        reason_code="unregistered_agent",
    )
    assert event_log.count_events() == 0
    assert event_log.list_quarantine()[0]["reason_code"] == "unregistered_agent"


def test_flywheel_event_errors_supply_quarantine_reason_codes(log_and_path):
    event_log, _ = log_and_path
    invalid_schema = valid_mapping()
    invalid_schema["unknown_envelope_field"] = "reject-me"
    bad_hash = valid_mapping(payload_hash="sha256:" + "0" * 64)

    schema_receipt = event_log.append(invalid_schema)
    hash_receipt = event_log.append(bad_hash)

    assert schema_receipt == AppendReceipt(
        status="quarantined",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash=None,
        reason_code="invalid_schema",
    )
    assert hash_receipt == AppendReceipt(
        status="quarantined",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash=None,
        reason_code="payload_hash_mismatch",
    )
    assert event_log.count_events() == 0
    assert {row["reason_code"] for row in event_log.list_quarantine()} == {
        "invalid_schema",
        "payload_hash_mismatch",
    }


def test_quarantine_fingerprints_preserve_heterogeneous_mapping_key_types(tmp_path):
    path = tmp_path / "typed-fingerprint.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    first = valid_mapping()
    first["unknown_input"] = {1: "second", "1": "first"}
    second = valid_mapping()
    second["unknown_input"] = {1: "second", "1": "second"}

    event_log.append(first)
    event_log.append(second)

    rows = event_log.list_quarantine()
    event_log.close()

    assert len(rows) == 2
    assert {row["reason_code"] for row in rows} == {"invalid_schema"}
    assert len({row["fingerprint"] for row in rows}) == 2


def test_unknown_class_instances_have_stable_quarantine_fingerprint(tmp_path):
    path = tmp_path / "opaque-fingerprint.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    first = valid_mapping()
    first["unknown_input"] = UnknownFingerprintValue()
    second = valid_mapping()
    second["unknown_input"] = UnknownFingerprintValue()

    try:
        first_receipt = event_log.append(first)
        second_receipt = event_log.append(second)
        rows = event_log.list_quarantine()
    finally:
        event_log.close()

    assert first_receipt.status == second_receipt.status == "quarantined"
    assert second_receipt == first_receipt
    assert len(rows) == 1
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", rows[0]["fingerprint"])


def test_unknown_object_with_failing_repr_is_quarantined(tmp_path):
    path = tmp_path / "explosive-repr.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    raw = valid_mapping()
    raw["unknown_input"] = ExplosiveReprValue()

    try:
        receipt = event_log.append(raw)
    finally:
        event_log.close()

    assert receipt.status == "quarantined"
    assert receipt.reason_code == "invalid_schema"


def test_quarantine_schema_and_rows_never_persist_raw_sensitive_input(tmp_path):
    path = tmp_path / "safe-quarantine.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    secret = "SENSITIVE-PASSWORD-DO-NOT-PERSIST"
    url = "https://private.example.invalid/token"
    raw = valid_mapping(
        source_event_id=url,
        payload={"episode_id": "episode-safe", "task": secret},
        episode_id="episode-safe",
    )
    raw["unknown_input"] = {"password": secret, "url": url}

    first = event_log.append(raw)
    second = event_log.append(raw)
    rows = event_log.list_quarantine()
    event_log.close()

    assert first.status == second.status == "quarantined"
    assert first.reason_code == second.reason_code == "invalid_schema"
    assert first.source_event_id is None
    assert first.episode_id == "episode-safe"
    assert len(rows) == 1
    assert tuple(rows[0]) == (
        "source_event_id",
        "episode_id",
        "reason_code",
        "fingerprint",
        "quarantined_at",
    )
    assert rows[0]["source_event_id"] is None
    assert rows[0]["episode_id"] == "episode-safe"
    assert rows[0]["reason_code"] == "invalid_schema"
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", rows[0]["fingerprint"])
    assert rows[0]["quarantined_at"].endswith("Z")
    assert table_columns(path, "flywheel_quarantine") == (
        "source_event_id",
        "episode_id",
        "reason_code",
        "fingerprint",
        "quarantined_at",
    )

    database_bytes = path.read_bytes()
    for forbidden in (secret, url, "unknown_input", "password", "task"):
        assert forbidden.encode() not in database_bytes


def test_sqlite_write_failure_raises_and_rolls_back_instead_of_accepting(log_and_path):
    event_log, path = log_and_path
    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TRIGGER force_event_write_failure
            BEFORE INSERT ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'forced write failure');
            END
            """
        )

    with pytest.raises(sqlite3.IntegrityError, match="forced write failure"):
        event_log.append(valid_mapping())

    assert event_log.count_events() == 0
    assert event_log.list_quarantine() == ()


def test_harness_record_delegates_the_original_mapping_and_returns_frozen_receipt():
    expected = AppendReceipt(
        status="accepted",
        source_event_id="source-1",
        episode_id="episode-1",
        event_hash="sha256:" + "0" * 64,
        reason_code=None,
    )

    class RecordingLog:
        def __init__(self):
            self.recorded = None

        def append(self, raw_event):
            self.recorded = raw_event
            return expected

    raw = valid_mapping()
    event_log = RecordingLog()
    harness = flywheel_log_module.CompassS4AgentHarness(event_log)

    receipt = harness.record(raw)

    assert event_log.recorded is raw
    assert receipt is expected
    with pytest.raises(FrozenInstanceError):
        receipt.status = "duplicate"


@pytest.fixture
def one_shot_harness(tmp_path):
    event_log = FlywheelEventLog(
        tmp_path / "one-shot.sqlite3",
        registered_agent_ids={7},
    )
    try:
        yield flywheel_log_module.CompassS4AgentHarness(event_log), event_log
    finally:
        event_log.close()


def test_one_shot_harness_records_and_reads_episode_without_chat_runtime_imports(
    one_shot_harness,
):
    harness, event_log = one_shot_harness
    raw = valid_mapping()
    expected = event_from_mapping(raw)

    receipt = harness.record(raw)

    assert receipt.status == "accepted"
    assert event_log.get("source-1") == expected

    source = Path(flywheel_log_module.__file__).read_text(encoding="utf-8")
    imported_roots = set()
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
    assert imported_roots.isdisjoint(
        {"anthropic", "claude", "codex", "langchain", "langgraph", "openai"}
    )


def test_reducer_returns_frozen_awaiting_verdict_states_with_lineage():
    first = event_from_mapping(valid_mapping())
    second_raw = valid_mapping(
        source_event_id="source-2",
        episode_id="episode-2",
        payload={"episode_id": "episode-2", "task": "verify another fix"},
    )
    second = event_from_mapping(second_raw)

    states = flywheel_log_module.reduce_episode_states((second, first))

    assert tuple(states) == ("episode-1", "episode-2")
    assert states["episode-1"] == flywheel_log_module.EpisodeState(
        episode_id="episode-1",
        state="awaiting_verdict",
        source_event_id="source-1",
        event_hash=first.event_hash,
    )
    assert states["episode-2"].source_event_id == "source-2"
    assert states["episode-2"].event_hash == second.event_hash
    with pytest.raises(FrozenInstanceError):
        states["episode-1"].state = "changed"


def test_reducer_is_deterministic_and_does_not_modify_its_input():
    first = event_from_mapping(valid_mapping())
    second = event_from_mapping(
        valid_mapping(
            source_event_id="source-2",
            episode_id="episode-2",
            payload={"episode_id": "episode-2", "task": "second task"},
        )
    )
    events = [second, first]
    before = tuple(events)

    first_result = flywheel_log_module.reduce_episode_states(events)
    second_result = flywheel_log_module.reduce_episode_states(reversed(events))

    assert first_result == second_result
    assert tuple(first_result) == tuple(second_result) == ("episode-1", "episode-2")
    assert tuple(events) == before


def test_reducer_returns_empty_mapping_for_empty_input():
    assert flywheel_log_module.reduce_episode_states(()) == {}


def test_reducer_rejects_duplicate_episode_ids_without_silent_overwrite():
    first = event_from_mapping(valid_mapping())
    competing = event_from_mapping(valid_mapping(source_event_id="source-2"))

    with pytest.raises(ValueError, match=r"duplicate episode_id: episode-1"):
        flywheel_log_module.reduce_episode_states((first, competing))
    with pytest.raises(ValueError, match=r"duplicate episode_id: episode-1"):
        flywheel_log_module.reduce_episode_states((competing, first))
