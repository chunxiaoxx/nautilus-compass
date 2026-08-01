"""Strict, canonical event envelope for the Compass S4 flywheel."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, fields
from datetime import datetime
from types import MappingProxyType
from typing import Any

from gep.experience_packet import ExperiencePacket, to_frontmatter
from gep.verdict_packet import VerdictPacket, to_payload as verdict_to_payload


SCHEMA_VERSION = "compass.flywheel.event.v1"
EVENT_KIND_EPISODE = "episode"
EVENT_KIND_VERDICT = "verdict"
PAYLOAD_SCHEMA = "compass.experience_packet.v0"
VERDICT_PAYLOAD_SCHEMA = "compass.verdict_packet.v0"

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_UTC_RFC3339_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z"
)
_EXPERIENCE_PAYLOAD_KEYS = frozenset(
    field.name for field in fields(ExperiencePacket)
)
_VERDICT_PAYLOAD_KEYS = frozenset(field.name for field in fields(VerdictPacket))
_PAYLOAD_SCHEMA_BY_KIND = {
    EVENT_KIND_EPISODE: PAYLOAD_SCHEMA,
    EVENT_KIND_VERDICT: VERDICT_PAYLOAD_SCHEMA,
}


class FlywheelEventError(ValueError):
    """A fail-closed envelope validation error with a stable reason code."""

    def __init__(self, reason_code: str, message: str | None = None) -> None:
        self.reason_code = reason_code
        super().__init__(message or reason_code)


@dataclass(frozen=True)
class FlywheelEvent:
    """One normalized and immutable flywheel event."""

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

    def __post_init__(self) -> None:
        _validate_constants(self)
        _validate_id(self.source_event_id, "source_event_id")
        _validate_id(self.episode_id, "episode_id")
        if self.event_kind == EVENT_KIND_VERDICT and self.parent_event_id is None:
            raise FlywheelEventError(
                "invalid_id",
                "parent_event_id must be present for verdict events",
            )
        if self.parent_event_id is not None:
            _validate_id(self.parent_event_id, "parent_event_id")
        _validate_agent_id(self.agent_id)
        _validate_occurred_at(self.occurred_at)
        _validate_payload_hash(self.payload_hash)

        normalized_payload = _normalize_payload(
            self.event_kind,
            self.payload_schema,
            self.payload,
        )
        if normalized_payload.get("episode_id") != self.episode_id:
            raise FlywheelEventError(
                "episode_id_mismatch",
                "payload episode_id must be present and match the envelope episode_id",
            )

        expected_hash = _hash_bytes(_canonical_json_bytes(normalized_payload, "invalid_payload"))
        if self.payload_hash != expected_hash:
            raise FlywheelEventError(
                "payload_hash_mismatch",
                "payload_hash does not match the canonical normalized payload",
            )

        object.__setattr__(self, "payload", _freeze_json(normalized_payload))

    @property
    def event_hash(self) -> str:
        """Return the SHA-256 hash of the canonical normalized envelope."""

        return _hash_bytes(canonical_event_bytes(self))

    def to_mapping(self) -> dict[str, Any]:
        """Return a detached, JSON-ready envelope mapping."""

        return to_mapping(self)


_ENVELOPE_KEYS = tuple(field.name for field in fields(FlywheelEvent))
_ENVELOPE_KEY_SET = frozenset(_ENVELOPE_KEYS)


def canonical_payload_bytes(payload: Mapping[str, Any]) -> bytes:
    """Serialize a strict, normalized ExperiencePacket payload canonically."""

    normalized = _normalize_experience_payload(payload)
    return _canonical_json_bytes(normalized, "invalid_payload")


def hash_payload(payload: Mapping[str, Any]) -> str:
    """Hash a strict ExperiencePacket payload in canonical normalized form."""

    return _hash_bytes(canonical_payload_bytes(payload))


def hash_payload_for_kind(event_kind: str, payload: Mapping[str, Any]) -> str:
    """Hash a payload using the normalizer registered for an event kind."""

    try:
        payload_schema = _PAYLOAD_SCHEMA_BY_KIND[event_kind]
    except (KeyError, TypeError) as exc:
        raise FlywheelEventError("invalid_schema", "unsupported event_kind") from exc
    normalized = _normalize_payload(event_kind, payload_schema, payload)
    return _hash_bytes(_canonical_json_bytes(normalized, "invalid_payload"))


def canonical_event_bytes(event: FlywheelEvent | Mapping[str, Any]) -> bytes:
    """Serialize an event or raw envelope in canonical normalized form."""

    normalized_event = event if isinstance(event, FlywheelEvent) else event_from_mapping(event)
    return _canonical_json_bytes(to_mapping(normalized_event), "invalid_schema")


def event_from_mapping(raw_event: Mapping[str, Any]) -> FlywheelEvent:
    """Validate and detach an exact v1 flywheel envelope mapping."""

    if not isinstance(raw_event, Mapping):
        raise FlywheelEventError("invalid_schema", "event must be a mapping")

    try:
        supplied_keys = frozenset(raw_event)
    except (TypeError, ValueError) as exc:
        raise FlywheelEventError("invalid_schema", "event keys are invalid") from exc

    if supplied_keys != _ENVELOPE_KEY_SET:
        missing = sorted(_ENVELOPE_KEY_SET - supplied_keys)
        unknown = sorted((supplied_keys - _ENVELOPE_KEY_SET), key=repr)
        details = []
        if missing:
            details.append(f"missing keys: {', '.join(missing)}")
        if unknown:
            details.append(f"unknown keys: {', '.join(map(str, unknown))}")
        raise FlywheelEventError("invalid_schema", "; ".join(details))

    try:
        values = {key: raw_event[key] for key in _ENVELOPE_KEYS}
    except (KeyError, TypeError, ValueError) as exc:
        raise FlywheelEventError("invalid_schema", "event mapping could not be read") from exc
    return FlywheelEvent(**values)


def to_mapping(event: FlywheelEvent) -> dict[str, Any]:
    """Return a detached mapping containing exactly the normalized envelope keys."""

    if not isinstance(event, FlywheelEvent):
        raise TypeError("event must be a FlywheelEvent")
    return {
        "schema_version": event.schema_version,
        "event_kind": event.event_kind,
        "source_event_id": event.source_event_id,
        "episode_id": event.episode_id,
        "parent_event_id": event.parent_event_id,
        "agent_id": event.agent_id,
        "occurred_at": event.occurred_at,
        "payload_schema": event.payload_schema,
        "payload": _thaw_json(event.payload),
        "payload_hash": event.payload_hash,
    }


def _validate_constants(event: FlywheelEvent) -> None:
    if event.schema_version != SCHEMA_VERSION:
        raise FlywheelEventError("invalid_schema", "unsupported schema_version")
    _payload_normalizer(event.event_kind, event.payload_schema)


def _validate_id(value: Any, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise FlywheelEventError("invalid_id", f"{field_name} must be a non-empty string")


def _validate_agent_id(agent_id: Any) -> None:
    if isinstance(agent_id, bool) or not isinstance(agent_id, int) or agent_id <= 0:
        raise FlywheelEventError("invalid_agent_id", "agent_id must be a positive integer")


def _validate_occurred_at(occurred_at: Any) -> None:
    if not isinstance(occurred_at, str) or _UTC_RFC3339_PATTERN.fullmatch(occurred_at) is None:
        raise FlywheelEventError(
            "invalid_occurred_at",
            "occurred_at must be an RFC3339 UTC timestamp ending in Z",
        )
    try:
        datetime.fromisoformat(f"{occurred_at[:-1]}+00:00")
    except ValueError as exc:
        raise FlywheelEventError(
            "invalid_occurred_at",
            "occurred_at must be a valid RFC3339 UTC timestamp",
        ) from exc


def _validate_payload_hash(payload_hash: Any) -> None:
    if not isinstance(payload_hash, str) or _HASH_PATTERN.fullmatch(payload_hash) is None:
        raise FlywheelEventError(
            "invalid_payload_hash",
            "payload_hash must be sha256 followed by 64 lowercase hexadecimal characters",
        )


def _normalize_payload(
    event_kind: Any,
    payload_schema: Any,
    payload: Any,
) -> dict[str, Any]:
    normalizer = _payload_normalizer(event_kind, payload_schema)
    return normalizer(payload)


def _payload_normalizer(event_kind: Any, payload_schema: Any) -> Any:
    try:
        return _PAYLOAD_NORMALIZERS[(event_kind, payload_schema)]
    except (KeyError, TypeError) as exc:
        raise FlywheelEventError(
            "invalid_schema",
            "unsupported event_kind and payload_schema pair",
        ) from exc


def _copy_exact_payload(payload: Any, allowed_keys: frozenset[str]) -> dict[str, Any]:
    if not isinstance(payload, Mapping):
        raise FlywheelEventError("invalid_payload", "payload must be a mapping")

    try:
        supplied_keys = frozenset(payload)
    except (TypeError, ValueError) as exc:
        raise FlywheelEventError("invalid_payload", "payload keys are invalid") from exc

    unknown_keys = supplied_keys - allowed_keys
    if unknown_keys:
        names = ", ".join(map(str, sorted(unknown_keys, key=repr)))
        raise FlywheelEventError("invalid_schema", f"unknown payload keys: {names}")

    try:
        return copy.deepcopy(dict(payload))
    except (TypeError, ValueError) as exc:
        raise FlywheelEventError("invalid_payload", "payload could not be copied") from exc


def _normalize_experience_payload(payload: Any) -> dict[str, Any]:
    copied_payload = _copy_exact_payload(payload, _EXPERIENCE_PAYLOAD_KEYS)
    try:
        packet = ExperiencePacket(**copied_payload)
        normalized = to_frontmatter(packet)
    except (TypeError, ValueError) as exc:
        raise FlywheelEventError("invalid_payload", "payload is not a valid ExperiencePacket") from exc

    encoded = _canonical_json_bytes(normalized, "invalid_payload")
    return json.loads(encoded)


def _normalize_verdict_payload(payload: Any) -> dict[str, Any]:
    copied_payload = _copy_exact_payload(payload, _VERDICT_PAYLOAD_KEYS)
    try:
        packet = VerdictPacket(**copied_payload)
        normalized = verdict_to_payload(packet)
    except (TypeError, ValueError) as exc:
        raise FlywheelEventError(
            "invalid_payload",
            "payload is not a valid VerdictPacket",
        ) from exc

    encoded = _canonical_json_bytes(normalized, "invalid_payload")
    return json.loads(encoded)


_PAYLOAD_NORMALIZERS = MappingProxyType(
    {
        (EVENT_KIND_EPISODE, PAYLOAD_SCHEMA): _normalize_experience_payload,
        (EVENT_KIND_VERDICT, VERDICT_PAYLOAD_SCHEMA): _normalize_verdict_payload,
    }
)


def _canonical_json_bytes(value: Any, reason_code: str) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise FlywheelEventError(reason_code, "value is not canonical JSON") from exc


def _hash_bytes(value: bytes) -> str:
    return f"sha256:{hashlib.sha256(value).hexdigest()}"


def _freeze_json(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_json(item) for item in value)
    return value


def _thaw_json(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_json(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_json(item) for item in value]
    return value


__all__ = [
    "EVENT_KIND_EPISODE",
    "EVENT_KIND_VERDICT",
    "PAYLOAD_SCHEMA",
    "SCHEMA_VERSION",
    "VERDICT_PAYLOAD_SCHEMA",
    "FlywheelEvent",
    "FlywheelEventError",
    "canonical_event_bytes",
    "canonical_payload_bytes",
    "event_from_mapping",
    "hash_payload",
    "hash_payload_for_kind",
    "to_mapping",
]
