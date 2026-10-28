"""Pure, canonical executor-authenticated evidence for the R1a synthetic task."""

from __future__ import annotations

import base64
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.keys import ED25519_V1

EVIDENCE_CONTRACT_VERSION = "m1-r1a-executor-execution-evidence-v1"
EVIDENCE_VECTOR_SET_VERSION = "m1-r1a-executor-execution-evidence-vectors-v1"
EVIDENCE_VECTOR_SHA256 = (
    "e44643cc5cdce10c018b9f3f92837fa27dda51f63a169d5cdae8df3e8349eca5"
)
EXECUTION_RESULT_STATES_V1 = ("completed", "review_required")

_FIELDS = frozenset(
    {
        "artifact_hash",
        "attempt_id",
        "bound_capsule_hash",
        "evidence_version",
        "executor_id",
        "executor_key_id",
        "executor_release",
        "executor_signature",
        "fixture_hash",
        "input_ref_hash",
        "operation_id",
        "produced_at",
        "result_state",
        "signature_algorithm",
        "tool_policy_hash",
    }
)
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_SIGNATURE_RE = re.compile(r"sig_[A-Za-z0-9_-]{86}\Z")


@dataclass(frozen=True, slots=True)
class ExecutorExecutionEvidenceV1:
    """One executor-signed result binding every R1a execution input."""

    evidence_version: str
    operation_id: str
    attempt_id: str
    input_ref_hash: str
    executor_id: str
    executor_release: str
    executor_key_id: str
    bound_capsule_hash: str
    fixture_hash: str
    tool_policy_hash: str
    artifact_hash: str
    result_state: str
    produced_at: datetime
    signature_algorithm: str
    executor_signature: str

    def __post_init__(self) -> None:
        if self.evidence_version != EVIDENCE_CONTRACT_VERSION:
            _violate("invalid_evidence_version")
        _require_identifier(self.operation_id, "operation_id", "op_")
        _require_identifier(self.attempt_id, "attempt_id", "att_")
        _require_identifier(self.executor_id, "executor_id", "exec_")
        _require_identifier(self.executor_release, "executor_release", "rel_")
        _require_identifier(self.executor_key_id, "executor_key_id", "key_")
        for field_name in (
            "input_ref_hash",
            "bound_capsule_hash",
            "fixture_hash",
            "tool_policy_hash",
            "artifact_hash",
        ):
            _require_sha256(getattr(self, field_name), field_name)
        if self.result_state not in EXECUTION_RESULT_STATES_V1:
            _violate("invalid_result_state")
        _require_utc(self.produced_at, "produced_at")
        if self.signature_algorithm != ED25519_V1:
            _violate("invalid_signature_algorithm")
        _require_ed25519_signature(self.executor_signature)

    @property
    def canonical_signing_bytes(self) -> bytes:
        """Return canonical bytes excluding only ``executor_signature``."""
        return _canonical_json_bytes(self._canonical_data(include_signature=False))

    @property
    def canonical_bytes(self) -> bytes:
        """Return canonical bytes for the complete signed evidence value."""
        return _canonical_json_bytes(self._canonical_data(include_signature=True))

    def _canonical_data(self, *, include_signature: bool) -> dict[str, object]:
        data: dict[str, object] = {
            "artifact_hash": self.artifact_hash,
            "attempt_id": self.attempt_id,
            "bound_capsule_hash": self.bound_capsule_hash,
            "evidence_version": self.evidence_version,
            "executor_id": self.executor_id,
            "executor_key_id": self.executor_key_id,
            "executor_release": self.executor_release,
            "fixture_hash": self.fixture_hash,
            "input_ref_hash": self.input_ref_hash,
            "operation_id": self.operation_id,
            "produced_at": _utc_text(self.produced_at),
            "result_state": self.result_state,
            "signature_algorithm": self.signature_algorithm,
            "tool_policy_hash": self.tool_policy_hash,
        }
        if include_signature:
            data["executor_signature"] = self.executor_signature
        return data


def parse_executor_execution_evidence_bytes(data: bytes) -> ExecutorExecutionEvidenceV1:
    """Parse exact UTF-8 JSON while rejecting duplicates and unknown fields."""
    document = _parse_json_object(data)
    if frozenset(document) != _FIELDS:
        _violate("unexpected_evidence_fields")
    produced_at = _parse_utc(document["produced_at"])
    return ExecutorExecutionEvidenceV1(
        evidence_version=document["evidence_version"],
        operation_id=document["operation_id"],
        attempt_id=document["attempt_id"],
        input_ref_hash=document["input_ref_hash"],
        executor_id=document["executor_id"],
        executor_release=document["executor_release"],
        executor_key_id=document["executor_key_id"],
        bound_capsule_hash=document["bound_capsule_hash"],
        fixture_hash=document["fixture_hash"],
        tool_policy_hash=document["tool_policy_hash"],
        artifact_hash=document["artifact_hash"],
        result_state=document["result_state"],
        produced_at=produced_at,
        signature_algorithm=document["signature_algorithm"],
        executor_signature=document["executor_signature"],
    )


def _parse_json_object(data: bytes) -> Mapping[str, Any]:
    if not isinstance(data, bytes):
        _violate("invalid_evidence_bytes")

    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _violate("duplicate_evidence_field")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (UnicodeDecodeError, json.JSONDecodeError):
        _violate("invalid_evidence_json")
    if not isinstance(value, Mapping):
        _violate("invalid_evidence_json")
    return value


def _parse_utc(value: object) -> datetime:
    if not isinstance(value, str):
        _violate("invalid_produced_at")
    try:
        parsed = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ").replace(
            tzinfo=timezone.utc
        )
    except ValueError:
        _violate("invalid_produced_at")
    if _utc_text(parsed) != value:
        _violate("invalid_produced_at")
    return parsed


def _require_identifier(value: object, field_name: str, prefix: str) -> None:
    expression = re.compile(rf"{re.escape(prefix)}[a-z0-9][a-z0-9_-]{{1,60}}\Z")
    if not isinstance(value, str) or expression.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_sha256(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_utc(value: object, field_name: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None:
        _violate(f"invalid_{field_name}")
    if value.utcoffset() != timedelta(0):
        _violate(f"invalid_{field_name}")


def _require_ed25519_signature(value: object) -> None:
    if not isinstance(value, str) or _SIGNATURE_RE.fullmatch(value) is None:
        _violate("invalid_executor_signature")
    encoded = value.removeprefix("sig_")
    try:
        raw = base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4))
    except (ValueError, UnicodeEncodeError):
        _violate("invalid_executor_signature")
    canonical = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    if len(raw) != 64 or canonical != encoded:
        _violate("invalid_executor_signature")


def _utc_text(value: datetime) -> str:
    _require_utc(value, "produced_at")
    return (
        value.astimezone(timezone.utc)
        .isoformat(timespec="microseconds")
        .replace("+00:00", "Z")
    )


def _canonical_json_bytes(value: Mapping[str, object]) -> bytes:
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _violate(code: str) -> None:
    raise ProtocolViolation(code)
