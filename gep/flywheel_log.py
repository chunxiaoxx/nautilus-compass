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
from typing import Any, Callable, TypeVar

from gep.flywheel_event import (
    FlywheelEvent,
    FlywheelEventError,
    canonical_event_bytes,
    event_from_mapping,
)


_SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_T = TypeVar("_T")


@dataclass(frozen=True)
class AppendReceipt:
    """The durable outcome of one append attempt."""

    status: str
    source_event_id: str | None
    episode_id: str | None
    event_hash: str | None
    reason_code: str | None


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
            self._connection.execute("PRAGMA journal_mode = DELETE")
            self._run_transaction(self._create_schema)
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

        episode_row = self._connection.execute(
            "SELECT source_event_id FROM flywheel_events WHERE episode_id = ?",
            (event.episode_id,),
        ).fetchone()
        if episode_row is not None:
            receipt = self._quarantine_event(event, "episode_id_conflict")
            self._insert_quarantine(receipt, event.event_hash)
            return receipt

        self._connection.execute(
            """
            INSERT INTO flywheel_events
                (source_event_id, episode_id, event_hash, envelope_json, accepted_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                event.source_event_id,
                event.episode_id,
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

    def _create_schema(self) -> None:
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
                ON flywheel_quarantine (reason_code, fingerprint);
            """,

            """
            CREATE TRIGGER IF NOT EXISTS flywheel_events_immutable_update
            BEFORE UPDATE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END;
            """,

            """
            CREATE TRIGGER IF NOT EXISTS flywheel_events_immutable_delete
            BEFORE DELETE ON flywheel_events
            BEGIN
                SELECT RAISE(ABORT, 'flywheel_events rows are immutable');
            END;
            """,
        )
        for statement in statements:
            self._connection.execute(statement)

    def _run_transaction(self, operation: Callable[[], _T]) -> _T:
        self._connection.execute("BEGIN IMMEDIATE")
        try:
            result = operation()
            self._connection.commit()
            return result
        except Exception:
            self._connection.rollback()
            raise


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
    if isinstance(value, Mapping):
        entries = [
            [_fingerprint_value(key), _fingerprint_value(item)]
            for key, item in value.items()
        ]
        entries.sort(key=_fingerprint_json)
        return {"type": "mapping", "entries": entries}
    if isinstance(value, list):
        return {"type": "list", "items": [_fingerprint_value(item) for item in value]}
    if isinstance(value, tuple):
        return {"type": "tuple", "items": [_fingerprint_value(item) for item in value]}
    if value is None:
        return {"type": "none"}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": str(value)}
    if isinstance(value, str):
        return {"type": "str", "value": value}
    if isinstance(value, float):
        return {"type": "float", "value": repr(value)}
    if isinstance(value, bytes):
        return {"type": "bytes", "value": value.hex()}
    if isinstance(value, bytearray):
        return {"type": "bytearray", "value": bytes(value).hex()}
    if isinstance(value, set):
        items = [_fingerprint_value(item) for item in value]
        items.sort(key=_fingerprint_json)
        return {"type": "set", "items": items}
    if isinstance(value, frozenset):
        items = [_fingerprint_value(item) for item in value]
        items.sort(key=_fingerprint_json)
        return {"type": "frozenset", "items": items}
    return {
        "type": f"{type(value).__module__}.{type(value).__qualname__}",
        "repr": repr(value),
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


__all__ = ["AppendReceipt", "FlywheelEventLog"]
