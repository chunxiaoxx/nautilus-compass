"""Strict immutable verdict facts for the Compass S4 flywheel."""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, fields
from typing import Any, Literal


VerdictOutcome = Literal["success", "failure", "partial", "inconclusive"]
VerifierKind = Literal[
    "physical",
    "software_test",
    "human_review",
    "external_acceptance",
    "simulation",
]

OUTCOMES = frozenset({"success", "failure", "partial", "inconclusive"})
VERIFIER_KINDS = frozenset(
    {
        "physical",
        "software_test",
        "human_review",
        "external_acceptance",
        "simulation",
    }
)

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_FAILURE_CLASS_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,63}")


@dataclass(frozen=True)
class VerdictPacket:
    """One independently produced, hash-bound episode verdict."""

    episode_id: str
    episode_event_hash: str
    outcome: VerdictOutcome
    verifier_kind: VerifierKind
    verifier_version: str
    verifier_policy_hash: str
    evidence_hash: str
    environment_fingerprint_hash: str | None = None
    failure_class: str | None = None

    def __post_init__(self) -> None:
        _validate_non_blank_string("episode_id", self.episode_id)
        _validate_hash("episode_event_hash", self.episode_event_hash)
        _validate_enum("outcome", self.outcome, OUTCOMES)
        _validate_enum("verifier_kind", self.verifier_kind, VERIFIER_KINDS)
        _validate_non_blank_string("verifier_version", self.verifier_version)
        _validate_hash("verifier_policy_hash", self.verifier_policy_hash)
        _validate_hash("evidence_hash", self.evidence_hash)
        if self.environment_fingerprint_hash is not None:
            _validate_hash(
                "environment_fingerprint_hash",
                self.environment_fingerprint_hash,
            )
        _validate_failure_class(self.failure_class)


_FIELD_NAMES = tuple(field.name for field in fields(VerdictPacket))
_FIELD_NAME_SET = frozenset(_FIELD_NAMES)


def from_args(
    args: Mapping[str, Any] | object | None = None,
    **overrides: Any,
) -> VerdictPacket:
    """Build a packet from an exact mapping, namespace, or keyword arguments."""

    if args is None:
        source: Mapping[str, Any] = {}
    elif isinstance(args, Mapping):
        source = args
    else:
        try:
            source = vars(args)
        except TypeError as exc:
            raise TypeError("args must be a mapping, namespace-like object, or None") from exc

    _reject_unknown_fields(source)
    _reject_unknown_fields(overrides)

    values = {name: source[name] for name in _FIELD_NAMES if name in source}
    values.update(overrides)
    return VerdictPacket(**values)


def to_payload(packet: VerdictPacket) -> dict[str, Any]:
    """Return a detached JSON-ready mapping containing every packet field."""

    if not isinstance(packet, VerdictPacket):
        raise TypeError("packet must be a VerdictPacket")
    return {name: getattr(packet, name) for name in _FIELD_NAMES}


def _validate_non_blank_string(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if not value.strip():
        raise ValueError(f"{field_name} must not be blank")


def _validate_enum(field_name: str, value: Any, allowed_values: frozenset[str]) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if value not in allowed_values:
        raise ValueError(f"{field_name} is unsupported")


def _validate_hash(field_name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string")
    if _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{field_name} must be sha256 followed by 64 lowercase hex characters")


def _validate_failure_class(value: Any) -> None:
    if value is None:
        return
    if not isinstance(value, str):
        raise TypeError("failure_class must be a string or None")
    if _FAILURE_CLASS_PATTERN.fullmatch(value) is None:
        raise ValueError("failure_class must be a safe lowercase taxonomy token")


def _reject_unknown_fields(values: Mapping[str, Any]) -> None:
    try:
        unknown_fields = frozenset(values) - _FIELD_NAME_SET
    except (TypeError, ValueError) as exc:
        raise TypeError("Verdict Packet field names must be strings") from exc
    if unknown_fields:
        label = "field" if len(unknown_fields) == 1 else "fields"
        names = ", ".join(map(str, sorted(unknown_fields, key=repr)))
        raise TypeError(f"unknown Verdict Packet {label}: {names}")


__all__ = [
    "OUTCOMES",
    "VERIFIER_KINDS",
    "VerdictOutcome",
    "VerifierKind",
    "VerdictPacket",
    "from_args",
    "to_payload",
]
