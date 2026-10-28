"""Opaque, Mentor-scoped continuations for Phase 3 interaction evidence.

Continuation state is technical session state, not a parallel business ledger.
Production must inject a durable ``ContinuationStore`` distinct from Bitable;
the in-memory implementation exists only for unit tests and local rehearsal.
"""

from __future__ import annotations

from base64 import urlsafe_b64encode
from dataclasses import dataclass, replace
from datetime import datetime
from enum import Enum
import hashlib
import hmac
import re
import secrets
from threading import RLock
from typing import Protocol, runtime_checkable


_EXPERT_SCOPE_PATTERN = re.compile(r"mentor_expert_[A-Za-z0-9_-]{1,80}\Z")
_QUESTION_BINDING_PATTERN = re.compile(r"question_binding_[A-Za-z0-9_-]{1,80}\Z")
_CONTINUATION_REFERENCE_PATTERN = re.compile(r"mentor_continue_[A-Za-z0-9_-]{20,128}\Z")
_REQUEST_KEY_PATTERN = re.compile(r"interaction_request_[A-Za-z0-9_-]{1,80}\Z")
_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")


class ContinuationState(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class ContinuationError(ValueError):
    """Base class for opaque continuation failures."""


class ContinuationScopeError(PermissionError):
    """Raised when a continuation is used from a different expert scope."""


class ContinuationExpiredError(PermissionError):
    """Raised when an expired continuation is used."""


class ContinuationConsumedError(PermissionError):
    """Raised when a different request tries to reuse a consumed continuation."""


class ContinuationNotFoundError(PermissionError):
    """Raised when a continuation reference cannot be resolved."""


@dataclass(frozen=True)
class EligibleQuestionContinuation:
    """An opaque projection of an eligible question, without Bitable identity."""

    expert_scope_handle: str
    question_binding_ref: str
    question_state: str
    expires_at: datetime

    def __post_init__(self) -> None:
        _require_pattern(
            self.expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        _require_pattern(
            self.question_binding_ref,
            _QUESTION_BINDING_PATTERN,
            "question_binding_ref",
        )
        if self.question_state != "eligible_for_interaction":
            raise ValueError("question_state must be eligible_for_interaction")
        _require_aware_datetime(self.expires_at, "expires_at")


@dataclass(frozen=True)
class ContinuationRecord:
    """Durable technical state; all references are opaque and non-content."""

    handle_hash: str
    handle_nonce: str
    expert_scope_handle: str
    question_binding_ref: str
    expires_at: datetime
    state: ContinuationState = ContinuationState.ACTIVE
    consumed_request_key: str | None = None

    def __post_init__(self) -> None:
        _require_pattern(self.handle_hash, _SHA256_PATTERN, "handle_hash")
        _require_compact_identifier(self.handle_nonce, "handle_nonce")
        _require_pattern(
            self.expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        _require_pattern(
            self.question_binding_ref,
            _QUESTION_BINDING_PATTERN,
            "question_binding_ref",
        )
        _require_aware_datetime(self.expires_at, "expires_at")
        if not isinstance(self.state, ContinuationState):
            raise ValueError("state must be a ContinuationState")
        if self.consumed_request_key is not None:
            _require_pattern(
                self.consumed_request_key,
                _REQUEST_KEY_PATTERN,
                "consumed_request_key",
            )
        if self.state is ContinuationState.CONSUMED and self.consumed_request_key is None:
            raise ValueError("consumed continuation requires a request key")
        if self.state is not ContinuationState.CONSUMED and self.consumed_request_key is not None:
            raise ValueError("only consumed continuation may retain a request key")


@dataclass(frozen=True)
class MentorContinuationAction:
    """The safe payload the Mentor renders as a task-card action."""

    continuation_reference: str
    expires_at: datetime
    action: str = "open_interaction_evidence"
    recovery_action: str = "request_continuation_reissue"

    def __post_init__(self) -> None:
        _require_pattern(
            self.continuation_reference,
            _CONTINUATION_REFERENCE_PATTERN,
            "continuation_reference",
        )
        _require_aware_datetime(self.expires_at, "expires_at")
        if self.action != "open_interaction_evidence":
            raise ValueError("action must be open_interaction_evidence")
        if self.recovery_action != "request_continuation_reissue":
            raise ValueError("recovery_action must be request_continuation_reissue")

    def to_mentor_payload(self) -> dict[str, str]:
        return {
            "action": self.action,
            "continuation_reference": self.continuation_reference,
            "expires_at": self.expires_at.isoformat(),
            "recovery_action": self.recovery_action,
        }


@dataclass(frozen=True)
class ContinuationConsumption:
    """Internal, opaque result of a successful single-use continuation claim."""

    question_binding_ref: str
    request_key: str
    duplicate: bool


@dataclass(frozen=True)
class _StoredConsumption:
    record: ContinuationRecord
    duplicate: bool


@runtime_checkable
class ContinuationStore(Protocol):
    """Durable, atomic storage contract outside the Bitable business ledger."""

    def acquire(self, candidate: ContinuationRecord, *, now: datetime) -> ContinuationRecord: ...

    def inspect(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        now: datetime,
    ) -> ContinuationRecord: ...

    def consume(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        request_key: str,
        now: datetime,
    ) -> _StoredConsumption: ...


class InMemoryContinuationStore:
    """Test-only store. Runtime wiring must inject a durable implementation."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._records_by_hash: dict[str, ContinuationRecord] = {}
        self._hash_by_binding: dict[tuple[str, str], str] = {}

    def acquire(self, candidate: ContinuationRecord, *, now: datetime) -> ContinuationRecord:
        _require_aware_datetime(now, "now")
        with self._lock:
            binding = (candidate.expert_scope_handle, candidate.question_binding_ref)
            existing_hash = self._hash_by_binding.get(binding)
            if existing_hash is not None:
                existing = self._records_by_hash[existing_hash]
                existing = self._expire_if_needed(existing, now)
                if existing.state is ContinuationState.ACTIVE:
                    return existing
                if existing.state is ContinuationState.CONSUMED:
                    return existing
                del self._records_by_hash[existing_hash]
            self._records_by_hash[candidate.handle_hash] = candidate
            self._hash_by_binding[binding] = candidate.handle_hash
            return candidate

    def inspect(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        now: datetime,
    ) -> ContinuationRecord:
        _require_pattern(handle_hash, _SHA256_PATTERN, "handle_hash")
        _require_pattern(
            expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        _require_aware_datetime(now, "now")
        with self._lock:
            record = self._records_by_hash.get(handle_hash)
            if record is None:
                raise ContinuationNotFoundError("continuation cannot be resolved")
            if record.expert_scope_handle != expert_scope_handle:
                raise ContinuationScopeError("continuation does not belong to this expert")
            record = self._expire_if_needed(record, now)
            if record.state is ContinuationState.EXPIRED:
                raise ContinuationExpiredError("continuation is expired")
            if record.state is ContinuationState.CONSUMED:
                raise ContinuationConsumedError("continuation is already consumed")
            return record

    def consume(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        request_key: str,
        now: datetime,
    ) -> _StoredConsumption:
        _require_pattern(handle_hash, _SHA256_PATTERN, "handle_hash")
        _require_pattern(
            expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        _require_pattern(request_key, _REQUEST_KEY_PATTERN, "request_key")
        _require_aware_datetime(now, "now")
        with self._lock:
            record = self._records_by_hash.get(handle_hash)
            if record is None:
                raise ContinuationNotFoundError("continuation cannot be resolved")
            if record.expert_scope_handle != expert_scope_handle:
                raise ContinuationScopeError("continuation does not belong to this expert")
            record = self._expire_if_needed(record, now)
            if record.state is ContinuationState.EXPIRED:
                raise ContinuationExpiredError("continuation is expired")
            if record.state is ContinuationState.CONSUMED:
                if record.consumed_request_key == request_key:
                    return _StoredConsumption(record=record, duplicate=True)
                raise ContinuationConsumedError("continuation is already consumed")
            consumed = replace(
                record,
                state=ContinuationState.CONSUMED,
                consumed_request_key=request_key,
            )
            self._records_by_hash[handle_hash] = consumed
            return _StoredConsumption(record=consumed, duplicate=False)

    def _expire_if_needed(
        self,
        record: ContinuationRecord,
        now: datetime,
    ) -> ContinuationRecord:
        if record.state is ContinuationState.ACTIVE and now >= record.expires_at:
            record = replace(record, state=ContinuationState.EXPIRED)
            self._records_by_hash[record.handle_hash] = record
        return record


@dataclass(frozen=True)
class HmacContinuationService:
    """Issues deterministic opaque actions while retaining only a handle hash."""

    secret: bytes
    store: ContinuationStore

    def __post_init__(self) -> None:
        if not isinstance(self.secret, bytes) or len(self.secret) < 32:
            raise ValueError("continuation secret must contain at least 32 bytes")
        if not isinstance(self.store, ContinuationStore):
            raise ValueError("store must implement ContinuationStore")

    def issue(
        self,
        *,
        eligible_question: EligibleQuestionContinuation,
        now: datetime,
    ) -> MentorContinuationAction:
        if not isinstance(eligible_question, EligibleQuestionContinuation):
            raise ValueError("eligible_question must be an EligibleQuestionContinuation")
        _require_aware_datetime(now, "now")
        if now >= eligible_question.expires_at:
            raise ContinuationExpiredError("continuation expiry must be in the future")
        nonce = secrets.token_urlsafe(32)
        reference = self._reference_for_nonce(nonce)
        candidate = ContinuationRecord(
            handle_hash=_hash_reference(reference),
            handle_nonce=nonce,
            expert_scope_handle=eligible_question.expert_scope_handle,
            question_binding_ref=eligible_question.question_binding_ref,
            expires_at=eligible_question.expires_at,
        )
        record = self.store.acquire(candidate, now=now)
        if record.state is ContinuationState.CONSUMED:
            raise ContinuationConsumedError("continuation is already consumed")
        if record.state is ContinuationState.EXPIRED:
            raise ContinuationExpiredError("continuation is expired")
        reference = self._reference_for_nonce(record.handle_nonce)
        if not hmac.compare_digest(record.handle_hash, _hash_reference(reference)):
            raise ContinuationError("continuation storage integrity check failed")
        return MentorContinuationAction(
            continuation_reference=reference,
            expires_at=record.expires_at,
        )

    def consume(
        self,
        *,
        continuation_reference: str,
        expert_scope_handle: str,
        request_key: str,
        now: datetime,
    ) -> ContinuationConsumption:
        _require_pattern(
            continuation_reference,
            _CONTINUATION_REFERENCE_PATTERN,
            "continuation_reference",
        )
        result = self.store.consume(
            handle_hash=_hash_reference(continuation_reference),
            expert_scope_handle=expert_scope_handle,
            request_key=request_key,
            now=now,
        )
        return ContinuationConsumption(
            question_binding_ref=result.record.question_binding_ref,
            request_key=request_key,
            duplicate=result.duplicate,
        )

    def inspect(
        self,
        *,
        continuation_reference: str,
        expert_scope_handle: str,
        now: datetime,
    ) -> ContinuationRecord:
        _require_pattern(
            continuation_reference,
            _CONTINUATION_REFERENCE_PATTERN,
            "continuation_reference",
        )
        _require_pattern(
            expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        _require_aware_datetime(now, "now")
        record = self.store.inspect(
            handle_hash=_hash_reference(continuation_reference),
            expert_scope_handle=expert_scope_handle,
            now=now,
        )
        expected_reference = self._reference_for_nonce(record.handle_nonce)
        if not hmac.compare_digest(expected_reference, continuation_reference):
            raise ContinuationError("continuation storage integrity check failed")
        return record

    def _reference_for_nonce(self, nonce: str) -> str:
        _require_compact_identifier(nonce, "handle_nonce")
        digest = hmac.new(self.secret, nonce.encode("utf-8"), hashlib.sha256).digest()
        return "mentor_continue_" + urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _hash_reference(continuation_reference: str) -> str:
    return "sha256:" + hashlib.sha256(continuation_reference.encode("utf-8")).hexdigest()


def _require_aware_datetime(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")


def _require_compact_identifier(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{label} must be a non-empty compact string")


def _require_pattern(value: str, pattern: re.Pattern[str], label: str) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} has an invalid opaque format")
