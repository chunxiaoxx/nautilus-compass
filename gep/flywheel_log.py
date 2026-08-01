"""SQLite persistence for validated Compass flywheel events."""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from os import PathLike
from pathlib import Path
from typing import Any, Callable, Literal, TypeVar

from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    FlywheelEvent,
    FlywheelEventError,
    canonical_event_bytes,
    event_from_mapping,
)


_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_T = TypeVar("_T")
_LEGACY_EVENT_SCHEMA = (
    ("source_event_id", "TEXT", 1, None, 0),
    ("episode_id", "TEXT", 1, None, 0),
    ("event_hash", "TEXT", 1, None, 0),
    ("envelope_json", "BLOB", 1, None, 0),
    ("accepted_at", "TEXT", 1, None, 0),
)
_V2_EVENT_SCHEMA = (
    ("source_event_id", "TEXT", 1, None, 0),
    ("event_kind", "TEXT", 1, None, 0),
    ("episode_id", "TEXT", 1, None, 0),
    ("parent_event_id", "TEXT", 0, None, 0),
    ("agent_id", "INTEGER", 1, None, 0),
    ("event_hash", "TEXT", 1, None, 0),
    ("envelope_json", "BLOB", 1, None, 0),
    ("accepted_at", "TEXT", 1, None, 0),
)
_QUARANTINE_SCHEMA = (
    ("source_event_id", "TEXT", 0, None, 0),
    ("episode_id", "TEXT", 0, None, 0),
    ("reason_code", "TEXT", 1, None, 0),
    ("fingerprint", "TEXT", 1, None, 0),
    ("quarantined_at", "TEXT", 1, None, 0),
)
_EVENT_TRIGGER_NAMES = frozenset(
    {
        "flywheel_events_immutable_update",
        "flywheel_events_immutable_delete",
    }
)
_QUARANTINE_TRIGGER_NAMES = frozenset(
    {
        "flywheel_quarantine_immutable_update",
        "flywheel_quarantine_immutable_delete",
    }
)
_TRIGGER_SQL_BY_NAME = {
    "flywheel_events_immutable_update": """
        CREATE TRIGGER flywheel_events_immutable_update
        BEFORE UPDATE ON flywheel_events
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
        END
    """,
    "flywheel_events_immutable_delete": """
        CREATE TRIGGER flywheel_events_immutable_delete
        BEFORE DELETE ON flywheel_events
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
        END
    """,
    "flywheel_quarantine_immutable_update": """
        CREATE TRIGGER flywheel_quarantine_immutable_update
        BEFORE UPDATE ON flywheel_quarantine
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
        END
    """,
    "flywheel_quarantine_immutable_delete": """
        CREATE TRIGGER flywheel_quarantine_immutable_delete
        BEFORE DELETE ON flywheel_quarantine
        BEGIN
            SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
        END
    """,
}
_V2_INDEX_SQL_BY_NAME = {
    "flywheel_events_episode_kind": """
        CREATE INDEX flywheel_events_episode_kind
            ON flywheel_events (episode_id, event_kind)
    """,
    "flywheel_events_one_episode": """
        CREATE UNIQUE INDEX flywheel_events_one_episode
            ON flywheel_events (episode_id)
            WHERE event_kind = 'episode'
    """,
    "flywheel_events_one_verdict_per_agent": """
        CREATE UNIQUE INDEX flywheel_events_one_verdict_per_agent
            ON flywheel_events (episode_id, agent_id)
            WHERE event_kind = 'verdict'
    """,
}
_QUARANTINE_INDEX_SQL_BY_NAME = {
    "flywheel_quarantine_dedup": """
        CREATE UNIQUE INDEX flywheel_quarantine_dedup
            ON flywheel_quarantine (reason_code, fingerprint)
    """
}


@dataclass(frozen=True)
class AppendReceipt:
    """The durable outcome of one append attempt."""

    status: str
    source_event_id: str | None
    episode_id: str | None
    event_hash: str | None
    reason_code: str | None


@dataclass(frozen=True)
class EpisodeState:
    """Derived state for one admitted episode event."""

    episode_id: str
    state: Literal["awaiting_verdict"]
    source_event_id: str
    event_hash: str


class FlywheelEventLog:
    """Persist validated flywheel events with fail-closed quarantine handling."""

    def __init__(
        self,
        path: str | PathLike[str],
        registered_agent_ids: Iterable[int],
    ) -> None:
        self._registered_agent_ids = _validate_registered_agent_ids(registered_agent_ids)
        self._connection = sqlite3.connect(Path(path))
        self._connection.row_factory = sqlite3.Row
        try:
            self._run_transaction(self._initialize_schema)
        except Exception:
            self._connection.close()
            raise

    def append(self, mapping: Mapping[str, Any]) -> AppendReceipt:
        """Append one event, or durably record its safe quarantine outcome."""

        try:
            event = event_from_mapping(mapping)
        except FlywheelEventError as error:
            source_event_id, episode_id = _safe_ids(mapping)
            fingerprint = _fingerprint(mapping)
            receipt = AppendReceipt(
                status="quarantined",
                source_event_id=source_event_id,
                episode_id=episode_id,
                event_hash=None,
                reason_code=error.reason_code,
            )
            self._run_transaction(
                lambda: self._insert_quarantine(
                    receipt,
                    fingerprint,
                )
            )
            return receipt

        event_bytes = canonical_event_bytes(event)
        if event.agent_id not in self._registered_agent_ids:
            receipt = self._quarantine_event(event, "unregistered_agent")
            self._run_transaction(lambda: self._insert_quarantine(receipt, event.event_hash))
            return receipt

        receipt = self._run_transaction(lambda: self._append_valid_event(event, event_bytes))
        return receipt

    def get(self, source_event_id: str) -> FlywheelEvent | None:
        """Return the accepted event for a source ID, if one exists."""

        row = self._connection.execute(
            "SELECT envelope_json FROM flywheel_events WHERE source_event_id = ?",
            (source_event_id,),
        ).fetchone()
        if row is None:
            return None
        return event_from_mapping(json.loads(row[0]))

    def list_events(self) -> tuple[FlywheelEvent, ...]:
        """Return accepted events in insertion order."""

        rows = self._connection.execute(
            "SELECT envelope_json FROM flywheel_events ORDER BY rowid"
        ).fetchall()
        return tuple(event_from_mapping(json.loads(row[0])) for row in rows)

    def count_events(self) -> int:
        """Return the number of accepted events."""

        row = self._connection.execute("SELECT COUNT(*) FROM flywheel_events").fetchone()
        return int(row[0])

    def list_quarantine(self) -> tuple[dict[str, Any], ...]:
        """Return safe quarantine metadata without raw event content."""

        return tuple(
            dict(row)
            for row in self._connection.execute(
                """
                SELECT source_event_id, episode_id, reason_code,
                       fingerprint, quarantined_at
                FROM flywheel_quarantine
                ORDER BY rowid
                """
            ).fetchall()
        )

    def close(self) -> None:
        """Close the SQLite connection."""

        self._connection.close()

    def _append_valid_event(
        self,
        event: FlywheelEvent,
        event_bytes: bytes,
    ) -> AppendReceipt:
        source_row = self._connection.execute(
            "SELECT event_hash, envelope_json FROM flywheel_events WHERE source_event_id = ?",
            (event.source_event_id,),
        ).fetchone()
        if source_row is not None:
            if source_row[0] == event.event_hash and bytes(source_row[1]) == event_bytes:
                return AppendReceipt(
                    status="duplicate",
                    source_event_id=event.source_event_id,
                    episode_id=event.episode_id,
                    event_hash=event.event_hash,
                    reason_code=None,
                )
            receipt = self._quarantine_event(event, "source_event_conflict")
            self._insert_quarantine(receipt, event.event_hash)
            return receipt

        if event.event_kind == EVENT_KIND_EPISODE:
            episode_row = self._connection.execute(
                """
                SELECT source_event_id
                FROM flywheel_events
                WHERE episode_id = ? AND event_kind = 'episode'
                """,
                (event.episode_id,),
            ).fetchone()
            if episode_row is not None:
                receipt = self._quarantine_event(event, "episode_id_conflict")
                self._insert_quarantine(receipt, event.event_hash)
                return receipt

        self._connection.execute(
            """
            INSERT INTO flywheel_events
                (source_event_id, event_kind, episode_id, parent_event_id,
                 agent_id, event_hash, envelope_json, accepted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.source_event_id,
                event.event_kind,
                event.episode_id,
                event.parent_event_id,
                event.agent_id,
                event.event_hash,
                sqlite3.Binary(event_bytes),
                _timestamp(),
            ),
        )
        return AppendReceipt(
            status="accepted",
            source_event_id=event.source_event_id,
            episode_id=event.episode_id,
            event_hash=event.event_hash,
            reason_code=None,
        )

    def _quarantine_event(self, event: FlywheelEvent, reason_code: str) -> AppendReceipt:
        return AppendReceipt(
            status="quarantined" if reason_code == "unregistered_agent" else "conflict",
            source_event_id=event.source_event_id,
            episode_id=event.episode_id,
            event_hash=event.event_hash,
            reason_code=reason_code,
        )

    def _insert_quarantine(self, receipt: AppendReceipt, fingerprint: str) -> None:
        self._connection.execute(
            """
            INSERT OR IGNORE INTO flywheel_quarantine
                (source_event_id, episode_id, reason_code, fingerprint, quarantined_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                receipt.source_event_id,
                receipt.episode_id,
                receipt.reason_code,
                fingerprint,
                _timestamp(),
            ),
        )

    def _initialize_schema(self) -> None:
        event_exists = self._table_exists("flywheel_events")
        quarantine_exists = self._table_exists("flywheel_quarantine")
        if not event_exists and not quarantine_exists:
            self._create_v2_schema()
            self._connection.execute("PRAGMA user_version = 2")
            return
        if not event_exists or not quarantine_exists:
            raise ValueError("unknown or partial flywheel schema")

        event_schema = self._table_schema("flywheel_events")
        if event_schema == _LEGACY_EVENT_SCHEMA:
            self._validate_legacy_schema()
            self._migrate_legacy_schema()
            return
        if event_schema == _V2_EVENT_SCHEMA:
            self._validate_v2_schema()
            return
        raise ValueError("unknown or partial flywheel_events schema")

    def _create_v2_schema(self) -> None:
        self._create_event_schema()
        self._create_quarantine_schema()

    def _create_event_schema(self) -> None:
        statements = (
            """
            CREATE TABLE flywheel_events (
                source_event_id TEXT NOT NULL UNIQUE,
                event_kind TEXT NOT NULL,
                episode_id TEXT NOT NULL,
                parent_event_id TEXT,
                agent_id INTEGER NOT NULL,
                event_hash TEXT NOT NULL UNIQUE,
                envelope_json BLOB NOT NULL,
                accepted_at TEXT NOT NULL
            )
            """,
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
            END;
            """,
            """
            CREATE TRIGGER flywheel_events_immutable_delete
            BEFORE DELETE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END;
            """,
        )
        for statement in statements:
            self._connection.execute(statement)

    def _create_quarantine_schema(self) -> None:
        statements = (
            """
            CREATE TABLE flywheel_quarantine (
                source_event_id TEXT,
                episode_id TEXT,
                reason_code TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                quarantined_at TEXT NOT NULL
            )
            """,
            """
            CREATE UNIQUE INDEX flywheel_quarantine_dedup
                ON flywheel_quarantine (reason_code, fingerprint)
            """,
            """
            CREATE TRIGGER flywheel_quarantine_immutable_update
            BEFORE UPDATE ON flywheel_quarantine
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
            END;
            """,
            """
            CREATE TRIGGER flywheel_quarantine_immutable_delete
            BEFORE DELETE ON flywheel_quarantine
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_quarantine rows are immutable');
            END;
            """,
        )
        for statement in statements:
            self._connection.execute(statement)

    def _migrate_legacy_schema(self) -> None:
        legacy_rows = self._connection.execute(
            """
            SELECT source_event_id, episode_id, event_hash,
                   envelope_json, accepted_at
            FROM flywheel_events
            ORDER BY rowid
            """
        ).fetchall()
        migrated_rows = tuple(
            _validated_legacy_row(row, position)
            for position, row in enumerate(legacy_rows, start=1)
        )

        for trigger_name in sorted(_EVENT_TRIGGER_NAMES):
            self._connection.execute(f"DROP TRIGGER {trigger_name}")
        self._connection.execute(
            "ALTER TABLE flywheel_events RENAME TO flywheel_events_legacy"
        )
        self._create_event_schema()
        self._connection.executemany(
            """
            INSERT INTO flywheel_events
                (source_event_id, event_kind, episode_id, parent_event_id,
                 agent_id, event_hash, envelope_json, accepted_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            migrated_rows,
        )
        copied_rows = tuple(
            tuple(row)
            for row in self._connection.execute(
                "SELECT * FROM flywheel_events ORDER BY rowid"
            ).fetchall()
        )
        if len(copied_rows) != len(legacy_rows) or copied_rows != migrated_rows:
            raise ValueError("legacy flywheel_events migration row mismatch")

        self._connection.execute("DROP TABLE flywheel_events_legacy")
        self._connection.execute("PRAGMA user_version = 2")
        self._validate_v2_schema()

    def _validate_legacy_schema(self) -> None:
        if self._user_version() != 0:
            raise ValueError("legacy flywheel schema has an unexpected user_version")
        self._validate_quarantine_schema()
        self._validate_trigger_names("flywheel_events", _EVENT_TRIGGER_NAMES)
        expected_indexes = {
            "sqlite_autoindex_flywheel_events_1": (1, 0, ("source_event_id",)),
            "sqlite_autoindex_flywheel_events_2": (1, 0, ("episode_id",)),
        }
        if self._index_specs("flywheel_events") != expected_indexes:
            raise ValueError("legacy flywheel_events indexes do not match S4-2")

    def _validate_v2_schema(self) -> None:
        if self._user_version() != 2:
            raise ValueError("v2 flywheel schema requires user_version 2")
        if self._table_schema("flywheel_events") != _V2_EVENT_SCHEMA:
            raise ValueError("unknown or partial v2 flywheel_events schema")
        self._validate_quarantine_schema()
        self._validate_trigger_names("flywheel_events", _EVENT_TRIGGER_NAMES)
        expected_indexes = {
            "sqlite_autoindex_flywheel_events_1": (1, 0, ("source_event_id",)),
            "sqlite_autoindex_flywheel_events_2": (1, 0, ("event_hash",)),
            "flywheel_events_episode_kind": (0, 0, ("episode_id", "event_kind")),
            "flywheel_events_one_episode": (1, 1, ("episode_id",)),
            "flywheel_events_one_verdict_per_agent": (
                1,
                1,
                ("episode_id", "agent_id"),
            ),
        }
        if self._index_specs("flywheel_events") != expected_indexes:
            raise ValueError("v2 flywheel_events indexes are incomplete")
        self._validate_named_sql(_V2_INDEX_SQL_BY_NAME)

    def _validate_quarantine_schema(self) -> None:
        if self._table_schema("flywheel_quarantine") != _QUARANTINE_SCHEMA:
            raise ValueError("unknown or partial flywheel_quarantine schema")
        self._validate_trigger_names(
            "flywheel_quarantine",
            _QUARANTINE_TRIGGER_NAMES,
        )
        expected_indexes = {
            "flywheel_quarantine_dedup": (
                1,
                0,
                ("reason_code", "fingerprint"),
            )
        }
        if self._index_specs("flywheel_quarantine") != expected_indexes:
            raise ValueError("flywheel_quarantine indexes are incomplete")
        self._validate_named_sql(_QUARANTINE_INDEX_SQL_BY_NAME)

    def _validate_trigger_names(
        self,
        table_name: str,
        expected_names: frozenset[str],
    ) -> None:
        definitions = {
            row[0]: row[1]
            for row in self._connection.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE type = 'trigger' AND tbl_name = ?
                """,
                (table_name,),
            )
        }
        if frozenset(definitions) != expected_names:
            raise ValueError(f"{table_name} immutable triggers are incomplete")
        expected_sql = {
            name: _TRIGGER_SQL_BY_NAME[name]
            for name in expected_names
        }
        if _normalized_schema_sql_map(definitions) != _normalized_schema_sql_map(
            expected_sql
        ):
            raise ValueError(f"{table_name} immutable trigger schema is invalid")

    def _validate_named_sql(self, expected: Mapping[str, str]) -> None:
        definitions = {
            row[0]: row[1]
            for row in self._connection.execute(
                """
                SELECT name, sql
                FROM sqlite_master
                WHERE name IN ({})
                """.format(", ".join("?" for _ in expected)),
                tuple(expected),
            )
        }
        if _normalized_schema_sql_map(definitions) != _normalized_schema_sql_map(
            expected
        ):
            raise ValueError("named flywheel index schema is invalid")

    def _table_exists(self, table_name: str) -> bool:
        return (
            self._connection.execute(
                """
                SELECT 1 FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table_name,),
            ).fetchone()
            is not None
        )

    def _table_schema(self, table_name: str) -> tuple[tuple[Any, ...], ...]:
        return tuple(
            tuple(row[1:])
            for row in self._connection.execute(f"PRAGMA table_info({table_name})")
        )

    def _index_specs(
        self,
        table_name: str,
    ) -> dict[str, tuple[int, int, tuple[str, ...]]]:
        specs = {}
        for row in self._connection.execute(f"PRAGMA index_list({table_name})"):
            name = row[1]
            columns = tuple(
                item[2]
                for item in self._connection.execute(f"PRAGMA index_info({name})")
            )
            specs[name] = (row[2], row[4], columns)
        return specs

    def _user_version(self) -> int:
        return int(self._connection.execute("PRAGMA user_version").fetchone()[0])

    def _run_transaction(self, operation: Callable[[], _T]) -> _T:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            result = operation()
            self._connection.commit()
            return result
        except Exception:
            self._connection.rollback()
            raise


def _normalized_schema_sql_map(
    definitions: Mapping[str, str | None],
) -> dict[str, str | None]:
    normalized = {}
    for name, statement in definitions.items():
        if statement is None:
            normalized[name] = None
            continue
        compact = re.sub(r"\s+", "", statement).lower()
        normalized[name] = compact.replace("ifnotexists", "").rstrip(";")
    return normalized


def _validated_legacy_row(
    row: sqlite3.Row,
    position: int,
) -> tuple[Any, ...]:
    try:
        envelope_bytes = bytes(row["envelope_json"])
        raw_event = json.loads(envelope_bytes)
        event = event_from_mapping(raw_event)
    except (FlywheelEventError, TypeError, ValueError, UnicodeError) as exc:
        raise ValueError(
            f"legacy flywheel_events row {position} has an invalid envelope"
        ) from exc

    if canonical_event_bytes(event) != envelope_bytes:
        raise ValueError(
            f"legacy flywheel_events row {position} is not canonical"
        )
    if event.event_kind != EVENT_KIND_EPISODE:
        raise ValueError(
            f"legacy flywheel_events row {position} is not an episode"
        )
    if row["event_hash"] != event.event_hash:
        raise ValueError(
            f"legacy flywheel_events row {position} has an event_hash mismatch"
        )
    if row["source_event_id"] != event.source_event_id:
        raise ValueError(
            f"legacy flywheel_events row {position} has a source_event_id mismatch"
        )
    if row["episode_id"] != event.episode_id:
        raise ValueError(
            f"legacy flywheel_events row {position} has an episode_id mismatch"
        )
    return (
        event.source_event_id,
        event.event_kind,
        event.episode_id,
        event.parent_event_id,
        event.agent_id,
        event.event_hash,
        envelope_bytes,
        row["accepted_at"],
    )


class CompassS4AgentHarness:
    """Thin adapter from a structured runtime event to the durable log."""

    def __init__(self, event_log: FlywheelEventLog) -> None:
        self._event_log = event_log

    def record(self, raw_event: Mapping[str, Any]) -> AppendReceipt:
        """Delegate one structured event to the configured append-only log."""

        return self._event_log.append(raw_event)


def reduce_episode_states(events: Iterable[FlywheelEvent]) -> dict[str, EpisodeState]:
    """Derive deterministic awaiting-verdict states without mutating events."""

    states: dict[str, EpisodeState] = {}
    for event in events:
        if event.episode_id in states:
            raise ValueError(f"duplicate episode_id: {event.episode_id}")
        states[event.episode_id] = EpisodeState(
            episode_id=event.episode_id,
            state="awaiting_verdict",
            source_event_id=event.source_event_id,
            event_hash=event.event_hash,
        )
    return dict(sorted(states.items()))


def _validate_registered_agent_ids(registered_agent_ids: Iterable[int]) -> frozenset[int]:
    try:
        ids = tuple(registered_agent_ids)
    except TypeError as exc:
        raise ValueError("registered_agent_ids must contain positive non-bool integers") from exc
    if any(isinstance(agent_id, bool) or not isinstance(agent_id, int) or agent_id <= 0 for agent_id in ids):
        raise ValueError("registered_agent_ids must contain positive non-bool integers")
    return frozenset(ids)


def _safe_ids(mapping: Any) -> tuple[str | None, str | None]:
    if not isinstance(mapping, Mapping):
        return None, None
    return _safe_id(mapping.get("source_event_id")), _safe_id(mapping.get("episode_id"))


def _safe_id(value: Any) -> str | None:
    if not isinstance(value, str) or _SAFE_ID_PATTERN.fullmatch(value) is None:
        return None
    return value


def _fingerprint(value: Any) -> str:
    normalized = _fingerprint_value(value)
    encoded = _fingerprint_json(normalized)
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def _fingerprint_value(value: Any) -> Any:
    if type(value) is dict:
        entries = [
            [_fingerprint_value(key), _fingerprint_value(item)]
            for key, item in value.items()
        ]
        entries.sort(key=_fingerprint_json)
        return {"type": "mapping", "entries": entries}
    if type(value) is list:
        return {"type": "list", "items": [_fingerprint_value(item) for item in value]}
    if type(value) is tuple:
        return {"type": "tuple", "items": [_fingerprint_value(item) for item in value]}
    if value is None:
        return {"type": "none"}
    if type(value) is bool:
        return {"type": "bool", "value": value}
    if type(value) is int:
        return {"type": "int", "value": str(value)}
    if type(value) is str:
        return {"type": "str", "value": value}
    if type(value) is float:
        return {"type": "float", "value": float.hex(value)}
    if type(value) is bytes:
        return {"type": "bytes", "value": value.hex()}
    if type(value) is bytearray:
        return {"type": "bytearray", "value": bytes(value).hex()}
    if type(value) is set:
        items = [_fingerprint_value(item) for item in value]
        items.sort(key=_fingerprint_json)
        return {"type": "set", "items": items}
    if type(value) is frozenset:
        items = [_fingerprint_value(item) for item in value]
        items.sort(key=_fingerprint_json)
        return {"type": "frozenset", "items": items}
    value_type = type(value)
    module = type.__getattribute__(value_type, "__module__")
    qualname = type.__getattribute__(value_type, "__qualname__")
    return {
        "type": "opaque",
        "class": f"{module}.{qualname}",
        "value": "<opaque>",
    }


def _fingerprint_json(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _timestamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds").replace("+00:00", "Z")


__all__ = [
    "AppendReceipt",
    "CompassS4AgentHarness",
    "EpisodeState",
    "FlywheelEventLog",
    "reduce_episode_states",
]
