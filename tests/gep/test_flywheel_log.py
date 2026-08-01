import ast
import re
import sqlite3
from dataclasses import FrozenInstanceError, fields
from pathlib import Path

import pytest

import gep.flywheel_log as flywheel_log_module
from gep.flywheel_event import (
    canonical_event_bytes,
    event_from_mapping,
    hash_payload,
    hash_payload_for_kind,
)
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


def valid_verdict_mapping(**overrides):
    payload = overrides.pop(
        "payload",
        {
            "episode_id": "episode-1",
            "episode_event_hash": "sha256:" + "1" * 64,
            "outcome": "success",
            "verifier_kind": "software_test",
            "verifier_version": "pytest-8.4",
            "verifier_policy_hash": "sha256:" + "2" * 64,
            "evidence_hash": "sha256:" + "3" * 64,
            "environment_fingerprint_hash": "sha256:" + "4" * 64,
            "failure_class": None,
        },
    )
    payload_hash = overrides.pop(
        "payload_hash",
        hash_payload_for_kind("verdict", payload),
    )
    event = {
        "schema_version": "compass.flywheel.event.v1",
        "event_kind": "verdict",
        "source_event_id": "verdict-source-1",
        "episode_id": "episode-1",
        "parent_event_id": "source-1",
        "agent_id": 8,
        "occurred_at": "2026-08-01T01:00:00Z",
        "payload_schema": "compass.verdict_packet.v0",
        "payload": payload,
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


LEGACY_ACCEPTED_AT = "2026-07-31T12:00:01.123456Z"


def create_legacy_database(path, raw_event=None):
    raw_event = valid_mapping() if raw_event is None else raw_event
    event = event_from_mapping(raw_event)
    envelope_bytes = canonical_event_bytes(event)
    statements = (
        """
        CREATE TABLE IF NOT EXISTS flywheel_events (
            source_event_id TEXT NOT NULL UNIQUE,
            episode_id TEXT NOT NULL UNIQUE,
            event_hash TEXT NOT NULL,
            envelope_json BLOB NOT NULL,
            accepted_at TEXT NOT NULL
        )
        """,
        """
        CREATE TABLE IF NOT EXISTS flywheel_quarantine (
            source_event_id TEXT,
            episode_id TEXT,
            reason_code TEXT NOT NULL,
            fingerprint TEXT NOT NULL,
            quarantined_at TEXT NOT NULL
        )
        """,
        """
        CREATE UNIQUE INDEX IF NOT EXISTS flywheel_quarantine_dedup
            ON flywheel_quarantine (reason_code, fingerprint)
        """,
        """
        CREATE TRIGGER IF NOT EXISTS flywheel_events_immutable_update
        BEFORE UPDATE ON flywheel_events
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS flywheel_events_immutable_delete
        BEFORE DELETE ON flywheel_events
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS flywheel_quarantine_immutable_update
        BEFORE UPDATE ON flywheel_quarantine
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
        END
        """,
        """
        CREATE TRIGGER IF NOT EXISTS flywheel_quarantine_immutable_delete
        BEFORE DELETE ON flywheel_quarantine
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
        END
        """,
    )
    with sqlite3.connect(path) as connection:
        for statement in statements:
            connection.execute(statement)
        connection.execute(
            """
            INSERT INTO flywheel_events
                (source_event_id, episode_id, event_hash, envelope_json, accepted_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.source_event_id,
                event.episode_id,
                event.event_hash,
                sqlite3.Binary(envelope_bytes),
                LEGACY_ACCEPTED_AT,
            ),
        )
        connection.execute(
            """
            INSERT INTO flywheel_quarantine
                (source_event_id, episode_id, reason_code, fingerprint, quarantined_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "legacy-rejected-source",
                "legacy-rejected-episode",
                "invalid_schema",
                "sha256:" + "9" * 64,
                "2026-07-31T12:00:02.654321Z",
            ),
        )
        connection.execute("PRAGMA user_version = 0")
    return event, envelope_bytes


def database_snapshot(path):
    with sqlite3.connect(path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            )
        }
        return {
            "version": connection.execute("PRAGMA user_version").fetchone()[0],
            "columns": tuple(
                row[1]
                for row in connection.execute("PRAGMA table_info(flywheel_events)")
            ),
            "events": tuple(
                connection.execute(
                    "SELECT * FROM flywheel_events ORDER BY rowid"
                ).fetchall()
            )
            if "flywheel_events" in tables
            else (),
            "quarantine": tuple(
                connection.execute(
                    "SELECT * FROM flywheel_quarantine ORDER BY rowid"
                ).fetchall()
            )
            if "flywheel_quarantine" in tables
            else (),
            "schema": tuple(
                connection.execute(
                    """
                    SELECT type, name, tbl_name, sql
                    FROM sqlite_master
                    WHERE name NOT LIKE 'sqlite_%'
                    ORDER BY type, name
                    """
                ).fetchall()
            ),
        }


def create_v2_database(path):
    episode = event_from_mapping(valid_mapping())
    verdict = event_from_mapping(valid_verdict_mapping())
    event_log = FlywheelEventLog(path, registered_agent_ids={7, 8})
    try:
        assert event_log.append(episode.to_mapping()).status == "accepted"
        assert event_log.append(verdict.to_mapping()).status == "accepted"
    finally:
        event_log.close()
    return episode, verdict


def tamper_v2_event_row(path, corruption):
    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER flywheel_events_immutable_update")
        if corruption == "invalid_envelope":
            connection.execute(
                "UPDATE flywheel_events SET envelope_json = ? WHERE source_event_id = ?",
                (sqlite3.Binary(b"{not-json"), "source-1"),
            )
        elif corruption == "noncanonical_envelope":
            canonical = connection.execute(
                "SELECT envelope_json FROM flywheel_events WHERE source_event_id = ?",
                ("source-1",),
            ).fetchone()[0]
            noncanonical = canonical.replace(b'","', b'", "', 1)
            connection.execute(
                "UPDATE flywheel_events SET envelope_json = ? WHERE source_event_id = ?",
                (sqlite3.Binary(noncanonical), "source-1"),
            )
        elif corruption == "event_hash":
            connection.execute(
                "UPDATE flywheel_events SET event_hash = ? WHERE source_event_id = ?",
                ("sha256:" + "0" * 64, "source-1"),
            )
        elif corruption == "source_event_id":
            connection.execute(
                "UPDATE flywheel_events SET source_event_id = ? WHERE source_event_id = ?",
                ("tampered-source", "source-1"),
            )
        elif corruption == "event_kind":
            connection.execute(
                "UPDATE flywheel_events SET event_kind = ? WHERE source_event_id = ?",
                ("verdict", "source-1"),
            )
        elif corruption == "episode_id":
            connection.execute(
                "UPDATE flywheel_events SET episode_id = ? WHERE source_event_id = ?",
                ("tampered-episode", "source-1"),
            )
        elif corruption == "parent_event_id":
            connection.execute(
                """
                UPDATE flywheel_events
                SET parent_event_id = ?
                WHERE source_event_id = ?
                """,
                ("tampered-parent", "verdict-source-1"),
            )
        elif corruption == "agent_id":
            connection.execute(
                "UPDATE flywheel_events SET agent_id = ? WHERE source_event_id = ?",
                (99, "source-1"),
            )
        else:
            raise AssertionError(f"unsupported corruption: {corruption}")
        connection.execute(
            """
            CREATE TRIGGER flywheel_events_immutable_update
            BEFORE UPDATE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END
            """
        )


def replace_v2_table_with_tampered_ddl(path, table_name, tamper):
    if table_name == "flywheel_events":
        regular_columns = (
            "source_event_id, event_kind, episode_id, parent_event_id, "
            "agent_id, event_hash, envelope_json, accepted_at"
        )
        generated_expression = "event_kind"
        base_ddl = """
            CREATE TABLE flywheel_events (
                source_event_id TEXT NOT NULL UNIQUE,
                event_kind TEXT NOT NULL,
                episode_id TEXT NOT NULL,
                parent_event_id TEXT,
                agent_id INTEGER NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                envelope_json BLOB NOT NULL,
                accepted_at TEXT NOT NULL{suffix}
            )
        """
        drop_objects = (
            "DROP TRIGGER flywheel_events_immutable_update",
            "DROP TRIGGER flywheel_events_immutable_delete",
            "DROP INDEX flywheel_events_episode_kind",
            "DROP INDEX flywheel_events_one_episode",
            "DROP INDEX flywheel_events_one_verdict_per_agent",
        )
        create_objects = (
            """
            CREATE INDEX flywheel_events_episode_kind
                ON flywheel_events (episode_id, event_kind)
            """,
            """
            CREATE UNIQUE INDEX flywheel_events_one_episode
                ON flywheel_events (episode_id)
                WHERE event_kind = 'episode'
            """,
            """
            CREATE UNIQUE INDEX flywheel_events_one_verdict_per_agent
                ON flywheel_events (episode_id, agent_id)
                WHERE event_kind = 'verdict'
            """,
            """
            CREATE TRIGGER flywheel_events_immutable_update
            BEFORE UPDATE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END
            """,
            """
            CREATE TRIGGER flywheel_events_immutable_delete
            BEFORE DELETE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END
            """,
        )
    else:
        regular_columns = (
            "source_event_id, episode_id, reason_code, fingerprint, quarantined_at"
        )
        generated_expression = "reason_code"
        base_ddl = """
            CREATE TABLE flywheel_quarantine (
                source_event_id TEXT,
                episode_id TEXT,
                reason_code TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                quarantined_at TEXT NOT NULL{suffix}
            )
        """
        drop_objects = (
            "DROP TRIGGER flywheel_quarantine_immutable_update",
            "DROP TRIGGER flywheel_quarantine_immutable_delete",
            "DROP INDEX flywheel_quarantine_dedup",
        )
        create_objects = (
            """
            CREATE UNIQUE INDEX flywheel_quarantine_dedup
                ON flywheel_quarantine (reason_code, fingerprint)
            """,
            """
            CREATE TRIGGER flywheel_quarantine_immutable_update
            BEFORE UPDATE ON flywheel_quarantine
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
            END
            """,
            """
            CREATE TRIGGER flywheel_quarantine_immutable_delete
            BEFORE DELETE ON flywheel_quarantine
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
            END
            """,
        )

    suffix = (
        ", CHECK (length(source_event_id) > 0)"
        if tamper == "extra_check"
        else (
            ", tamper_marker TEXT GENERATED ALWAYS AS "
            f"({generated_expression}) VIRTUAL"
        )
    )
    backup_name = f"{table_name}_backup"
    with sqlite3.connect(path) as connection:
        for statement in drop_objects:
            connection.execute(statement)
        connection.execute(f"ALTER TABLE {table_name} RENAME TO {backup_name}")
        connection.execute(base_ddl.format(suffix=suffix))
        connection.execute(
            f"""
            INSERT INTO {table_name} ({regular_columns})
            SELECT {regular_columns} FROM {backup_name}
            """
        )
        connection.execute(f"DROP TABLE {backup_name}")
        for statement in create_objects:
            connection.execute(statement)


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
        "event_kind",
        "episode_id",
        "parent_event_id",
        "agent_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    with sqlite3.connect(path) as connection:
        row = connection.execute(
            """
            SELECT source_event_id, event_kind, episode_id, parent_event_id,
                   agent_id, event_hash,
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

    assert row[:7] == (
        "source-1",
        "episode",
        "episode-1",
        None,
        7,
        expected.event_hash,
        "blob",
    )
    assert row[7] == canonical_event_bytes(expected)
    assert row[8].endswith("Z")
    assert tables == {"flywheel_events", "flywheel_quarantine"}


def test_fresh_database_has_exact_v2_schema_indexes_triggers_and_version(tmp_path):
    path = tmp_path / "fresh-v2.sqlite3"
    episode = event_from_mapping(valid_mapping())
    event_log = FlywheelEventLog(path, registered_agent_ids={7, 8})
    event_log.close()

    with sqlite3.connect(path) as connection:
        version = connection.execute("PRAGMA user_version").fetchone()[0]
        indexes = {
            row[1]: (row[2], row[4])
            for row in connection.execute("PRAGMA index_list(flywheel_events)")
        }
        index_columns = {
            name: tuple(
                row[2]
                for row in connection.execute(f"PRAGMA index_info({name})")
            )
            for name in indexes
            if not name.startswith("sqlite_autoindex")
        }
        trigger_names = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'trigger'"
            )
        }
        connection.execute(
            """
            INSERT INTO flywheel_events
                (source_event_id, event_kind, episode_id, parent_event_id,
                 agent_id, event_hash, envelope_json, accepted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                episode.source_event_id,
                episode.event_kind,
                episode.episode_id,
                episode.parent_event_id,
                episode.agent_id,
                episode.event_hash,
                sqlite3.Binary(canonical_event_bytes(episode)),
                LEGACY_ACCEPTED_AT,
            ),
        )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="UNIQUE constraint failed: flywheel_events.source_event_id",
        ):
            connection.execute(
                """
                INSERT INTO flywheel_events
                    (source_event_id, event_kind, episode_id, parent_event_id,
                     agent_id, event_hash, envelope_json, accepted_at)
                VALUES (?, 'verdict', ?, ?, ?, ?, ?, ?)
                """,
                (
                    episode.source_event_id,
                    "unique-source-check",
                    episode.source_event_id,
                    8,
                    "sha256:" + "a" * 64,
                    sqlite3.Binary(b"{}"),
                    LEGACY_ACCEPTED_AT,
                ),
            )
        with pytest.raises(
            sqlite3.IntegrityError,
            match="UNIQUE constraint failed: flywheel_events.event_hash",
        ):
            connection.execute(
                """
                INSERT INTO flywheel_events
                    (source_event_id, event_kind, episode_id, parent_event_id,
                     agent_id, event_hash, envelope_json, accepted_at)
                VALUES (?, 'verdict', ?, ?, ?, ?, ?, ?)
                """,
                (
                    "unique-hash-source",
                    "unique-hash-check",
                    episode.source_event_id,
                    9,
                    episode.event_hash,
                    sqlite3.Binary(b"{}"),
                    LEGACY_ACCEPTED_AT,
                ),
            )

    assert version == 2
    assert table_columns(path, "flywheel_events") == (
        "source_event_id",
        "event_kind",
        "episode_id",
        "parent_event_id",
        "agent_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    assert indexes["flywheel_events_episode_kind"] == (0, 0)
    assert indexes["flywheel_events_one_episode"] == (1, 1)
    assert indexes["flywheel_events_one_verdict_per_agent"] == (1, 1)
    assert index_columns == {
        "flywheel_events_episode_kind": ("episode_id", "event_kind"),
        "flywheel_events_one_episode": ("episode_id",),
        "flywheel_events_one_verdict_per_agent": ("episode_id", "agent_id"),
    }
    assert trigger_names == {
        "flywheel_events_immutable_update",
        "flywheel_events_immutable_delete",
        "flywheel_quarantine_immutable_update",
        "flywheel_quarantine_immutable_delete",
    }

    reopened = FlywheelEventLog(path, registered_agent_ids={7, 8})
    try:
        assert reopened.get(episode.source_event_id) == episode
        assert reopened.count_events() == 1
    finally:
        reopened.close()


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


def test_quarantine_rows_are_immutable_at_the_database_boundary(log_and_path):
    event_log, path = log_and_path
    event_log.append(valid_mapping(agent_id=8))
    original_rows = event_log.list_quarantine()

    assert len(original_rows) == 1

    for statement in (
        "UPDATE flywheel_quarantine SET reason_code = 'tampered'",
        "DELETE FROM flywheel_quarantine",
    ):
        with sqlite3.connect(path) as connection:
            with pytest.raises(sqlite3.IntegrityError, match="immutable"):
                connection.execute(statement)

    rows = event_log.list_quarantine()
    assert len(rows) == 1
    assert rows == original_rows


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


def test_untouched_v2_episode_and_verdict_rows_reopen_without_mutation(tmp_path):
    path = tmp_path / "valid-v2-restart.sqlite3"
    episode, verdict = create_v2_database(path)
    before_snapshot = database_snapshot(path)
    before_bytes = path.read_bytes()

    reopened = FlywheelEventLog(path, registered_agent_ids={7, 8})
    try:
        assert reopened.list_events() == (episode, verdict)
        assert reopened.count_events() == 2
    finally:
        reopened.close()

    assert database_snapshot(path) == before_snapshot
    assert path.read_bytes() == before_bytes


@pytest.mark.parametrize(
    "corruption",
    (
        "invalid_envelope",
        "noncanonical_envelope",
        "event_hash",
        "source_event_id",
        "event_kind",
        "episode_id",
        "parent_event_id",
        "agent_id",
    ),
)
def test_tampered_v2_event_row_fails_reopen_without_mutation(corruption, tmp_path):
    path = tmp_path / f"tampered-v2-row-{corruption}.sqlite3"
    create_v2_database(path)
    tamper_v2_event_row(path, corruption)
    before_snapshot = database_snapshot(path)
    before_bytes = path.read_bytes()

    with pytest.raises(ValueError, match="v2 flywheel_events row"):
        FlywheelEventLog(path, registered_agent_ids={7, 8})

    assert database_snapshot(path) == before_snapshot
    assert path.read_bytes() == before_bytes


def test_exact_s4_2_legacy_database_migrates_transactionally_without_rewriting(tmp_path):
    path = tmp_path / "legacy.sqlite3"
    expected, envelope_bytes = create_legacy_database(path)
    before = database_snapshot(path)

    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    try:
        restored = event_log.get(expected.source_event_id)
        after = database_snapshot(path)

        assert restored == expected
        assert event_log.list_events() == (expected,)
        assert event_log.count_events() == 1
        assert event_log.list_quarantine() == (
            {
                "source_event_id": "legacy-rejected-source",
                "episode_id": "legacy-rejected-episode",
                "reason_code": "invalid_schema",
                "fingerprint": "sha256:" + "9" * 64,
                "quarantined_at": "2026-07-31T12:00:02.654321Z",
            },
        )
    finally:
        event_log.close()

    assert before["version"] == 0
    assert before["columns"] == (
        "source_event_id",
        "episode_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    assert after["version"] == 2
    assert after["columns"] == (
        "source_event_id",
        "event_kind",
        "episode_id",
        "parent_event_id",
        "agent_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    assert after["events"] == (
        (
            expected.source_event_id,
            "episode",
            expected.episode_id,
            None,
            expected.agent_id,
            expected.event_hash,
            envelope_bytes,
            LEGACY_ACCEPTED_AT,
        ),
    )
    assert after["quarantine"] == before["quarantine"]
    assert {item[1] for item in after["schema"] if item[0] == "trigger"} == {
        "flywheel_events_immutable_update",
        "flywheel_events_immutable_delete",
        "flywheel_quarantine_immutable_update",
        "flywheel_quarantine_immutable_delete",
    }

    reopened = FlywheelEventLog(path, registered_agent_ids={7})
    try:
        restored = reopened.get(expected.source_event_id)
        assert restored == expected
        assert restored.source_event_id == expected.source_event_id
        assert restored.episode_id == expected.episode_id
        assert restored.event_hash == expected.event_hash
        assert canonical_event_bytes(restored) == envelope_bytes
        assert reopened.count_events() == 1
        with sqlite3.connect(path) as connection:
            persisted = connection.execute(
                """
                SELECT source_event_id, episode_id, event_hash,
                       envelope_json, accepted_at
                FROM flywheel_events
                """
            ).fetchone()
            version = connection.execute("PRAGMA user_version").fetchone()[0]
        assert persisted == (
            expected.source_event_id,
            expected.episode_id,
            expected.event_hash,
            envelope_bytes,
            LEGACY_ACCEPTED_AT,
        )
        assert version == 2
    finally:
        reopened.close()

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM flywheel_events")


@pytest.mark.parametrize(
    "corruption",
    (
        "invalid_bytes",
        "noncanonical_bytes",
        "stored_hash_mismatch",
        "stored_source_mismatch",
        "stored_episode_mismatch",
        "non_episode_envelope",
    ),
)
def test_corrupt_legacy_migration_rolls_back_every_schema_and_value(corruption, tmp_path):
    path = tmp_path / f"legacy-{corruption}.sqlite3"
    create_legacy_database(path)

    with sqlite3.connect(path) as connection:
        connection.execute("DROP TRIGGER flywheel_events_immutable_update")
        if corruption == "invalid_bytes":
            connection.execute(
                "UPDATE flywheel_events SET envelope_json = ?",
                (sqlite3.Binary(b"{not-json"),),
            )
        elif corruption == "noncanonical_bytes":
            event = event_from_mapping(valid_mapping())
            noncanonical = canonical_event_bytes(event).replace(b'","', b'", "', 1)
            connection.execute(
                "UPDATE flywheel_events SET envelope_json = ?",
                (sqlite3.Binary(noncanonical),),
            )
        elif corruption == "stored_hash_mismatch":
            connection.execute(
                "UPDATE flywheel_events SET event_hash = ?",
                ("sha256:" + "0" * 64,),
            )
        elif corruption == "stored_source_mismatch":
            connection.execute(
                "UPDATE flywheel_events SET source_event_id = 'stored-source'"
            )
        elif corruption == "stored_episode_mismatch":
            connection.execute(
                "UPDATE flywheel_events SET episode_id = 'stored-episode'"
            )
        else:
            verdict = event_from_mapping(valid_verdict_mapping())
            connection.execute(
                """
                UPDATE flywheel_events
                SET source_event_id = ?, episode_id = ?, event_hash = ?, envelope_json = ?
                """,
                (
                    verdict.source_event_id,
                    verdict.episode_id,
                    verdict.event_hash,
                    sqlite3.Binary(canonical_event_bytes(verdict)),
                ),
            )
        connection.execute(
            """
            CREATE TRIGGER flywheel_events_immutable_update
            BEFORE UPDATE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END
            """
        )

    before = database_snapshot(path)

    with pytest.raises((ValueError, sqlite3.DatabaseError)):
        FlywheelEventLog(path, registered_agent_ids={7, 8})

    after = database_snapshot(path)
    assert after == before
    assert after["version"] == 0
    assert after["columns"] == (
        "source_event_id",
        "episode_id",
        "event_hash",
        "envelope_json",
        "accepted_at",
    )
    assert {item[1] for item in after["schema"] if item[0] == "trigger"} == {
        "flywheel_events_immutable_update",
        "flywheel_events_immutable_delete",
        "flywheel_quarantine_immutable_update",
        "flywheel_quarantine_immutable_delete",
    }

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError, match="immutable"):
            connection.execute("DELETE FROM flywheel_events")


def test_unknown_partial_schema_raises_without_mutation(tmp_path):
    path = tmp_path / "partial.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute(
            "CREATE TABLE flywheel_events (source_event_id TEXT NOT NULL UNIQUE)"
        )
        connection.execute("PRAGMA user_version = 1")
    before = database_snapshot(path)

    with pytest.raises(ValueError, match="schema"):
        FlywheelEventLog(path, registered_agent_ids={7})

    assert database_snapshot(path) == before


@pytest.mark.parametrize("tampered_object", ("partial_index", "trigger"))
def test_same_shape_but_tampered_v2_schema_raises_without_mutation(
    tampered_object,
    tmp_path,
):
    path = tmp_path / f"tampered-{tampered_object}.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    event_log.close()

    with sqlite3.connect(path) as connection:
        if tampered_object == "partial_index":
            connection.execute("DROP INDEX flywheel_events_one_episode")
            connection.execute(
                """
                CREATE UNIQUE INDEX flywheel_events_one_episode
                    ON flywheel_events (episode_id)
                    WHERE event_kind = 'verdict'
                """
            )
        else:
            connection.execute("DROP TRIGGER flywheel_events_immutable_update")
            connection.execute(
                """
                CREATE TRIGGER flywheel_events_immutable_update
                BEFORE UPDATE ON flywheel_events
                BEGIN
                    SELECT 1;
                END
                """
            )
    before = database_snapshot(path)

    with pytest.raises(ValueError, match="schema|trigger|index"):
        FlywheelEventLog(path, registered_agent_ids={7})

    assert database_snapshot(path) == before


@pytest.mark.parametrize(
    ("table_name", "tamper"),
    (
        ("flywheel_events", "extra_check"),
        ("flywheel_events", "generated_column"),
        ("flywheel_quarantine", "extra_check"),
        ("flywheel_quarantine", "generated_column"),
    ),
)
def test_noncanonical_table_ddl_or_hidden_column_fails_without_mutation(
    table_name,
    tamper,
    tmp_path,
):
    path = tmp_path / f"tampered-ddl-{table_name}-{tamper}.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7})
    event_log.close()
    replace_v2_table_with_tampered_ddl(path, table_name, tamper)
    before_snapshot = database_snapshot(path)
    before_bytes = path.read_bytes()

    with pytest.raises(ValueError, match="schema"):
        FlywheelEventLog(path, registered_agent_ids={7})

    assert database_snapshot(path) == before_snapshot
    assert path.read_bytes() == before_bytes


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


def test_episode_and_linked_verdict_append_to_one_generic_journal(tmp_path):
    path = tmp_path / "linked-events.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7, 8})
    episode_raw = valid_mapping()
    verdict_raw = valid_verdict_mapping()
    episode = event_from_mapping(episode_raw)
    verdict = event_from_mapping(verdict_raw)

    try:
        episode_receipt = event_log.append(episode_raw)
        verdict_receipt = event_log.append(verdict_raw)

        assert episode_receipt.status == verdict_receipt.status == "accepted"
        assert event_log.get("source-1") == episode
        assert event_log.get("verdict-source-1") == verdict
        assert event_log.list_events() == (episode, verdict)
        assert event_log.count_events() == 2
        assert event_log.list_quarantine() == ()
    finally:
        event_log.close()

    with sqlite3.connect(path) as connection:
        rows = connection.execute(
            """
            SELECT source_event_id, event_kind, episode_id, parent_event_id,
                   agent_id, event_hash, envelope_json
            FROM flywheel_events
            ORDER BY rowid
            """
        ).fetchall()

    assert rows == [
        (
            episode.source_event_id,
            episode.event_kind,
            episode.episode_id,
            episode.parent_event_id,
            episode.agent_id,
            episode.event_hash,
            canonical_event_bytes(episode),
        ),
        (
            verdict.source_event_id,
            verdict.event_kind,
            verdict.episode_id,
            verdict.parent_event_id,
            verdict.agent_id,
            verdict.event_hash,
            canonical_event_bytes(verdict),
        ),
    ]


def test_verdict_before_episode_does_not_claim_the_episode_slot(tmp_path):
    path = tmp_path / "verdict-first.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7, 8})
    try:
        verdict_receipt = event_log.append(valid_verdict_mapping())
        episode_receipt = event_log.append(valid_mapping())

        assert verdict_receipt.status == "accepted"
        assert episode_receipt.status == "accepted"
        assert event_log.count_events() == 2
        assert event_log.list_quarantine() == ()
    finally:
        event_log.close()


def test_partial_unique_indexes_enforce_episode_and_verdict_cardinality(tmp_path):
    path = tmp_path / "partial-uniques.sqlite3"
    event_log = FlywheelEventLog(path, registered_agent_ids={7, 8, 9})
    episode = event_from_mapping(valid_mapping())
    first_verdict = event_from_mapping(valid_verdict_mapping())
    second_verdict = event_from_mapping(
        valid_verdict_mapping(
            source_event_id="verdict-source-2",
            agent_id=9,
        )
    )
    event_log.append(episode.to_mapping())
    event_log.append(first_verdict.to_mapping())
    event_log.append(second_verdict.to_mapping())
    event_log.close()

    with sqlite3.connect(path) as connection:
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO flywheel_events
                    (source_event_id, event_kind, episode_id, parent_event_id,
                     agent_id, event_hash, envelope_json, accepted_at)
                VALUES (?, 'episode', ?, NULL, ?, ?, ?, ?)
                """,
                (
                    "source-duplicate-episode",
                    episode.episode_id,
                    10,
                    "sha256:" + "a" * 64,
                    sqlite3.Binary(b"{}"),
                    LEGACY_ACCEPTED_AT,
                ),
            )
        with pytest.raises(sqlite3.IntegrityError):
            connection.execute(
                """
                INSERT INTO flywheel_events
                    (source_event_id, event_kind, episode_id, parent_event_id,
                     agent_id, event_hash, envelope_json, accepted_at)
                VALUES (?, 'verdict', ?, ?, ?, ?, ?, ?)
                """,
                (
                    "verdict-source-duplicate-agent",
                    first_verdict.episode_id,
                    first_verdict.parent_event_id,
                    first_verdict.agent_id,
                    "sha256:" + "b" * 64,
                    sqlite3.Binary(b"{}"),
                    LEGACY_ACCEPTED_AT,
                ),
            )

    reopened = FlywheelEventLog(path, registered_agent_ids={7, 8, 9})
    try:
        assert reopened.count_events() == 3
    finally:
        reopened.close()


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
