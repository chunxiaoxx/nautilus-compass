"""Durable, non-content runtime state for the Phase 3 Feishu workflow.

This module holds only opaque continuation/session handles and idempotency
markers. Bitable remains the authority for task, review, lineage, and export
state; these Redis records exist only to make authenticated delivery safe
across workers and restarts. Redis errors intentionally propagate so callers
fail closed instead of using process-local memory.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from typing import Any, Protocol

from services.fde_phase3_continuations import (
    ContinuationConsumedError,
    ContinuationExpiredError,
    ContinuationNotFoundError,
    ContinuationRecord,
    ContinuationScopeError,
    ContinuationState,
)


class RedisStateClient(Protocol):
    """Narrow Redis surface needed for atomic Phase 3 technical state."""

    def get(self, key: str) -> str | bytes | None: ...

    def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool | None: ...

    def eval(self, script: str, numkeys: int, *args: str) -> str | bytes: ...


@dataclass(frozen=True)
class _ContinuationConsumeResult:
    """Private structural result compatible with ``ContinuationStore``."""

    record: ContinuationRecord
    duplicate: bool


class RedisContinuationStore:
    """Atomic continuation store backed by the existing Redis runtime.

    Keys contain only SHA-256 digests of already-opaque handles. A retained
    consumed marker lets a network retry resume the same request while
    rejecting an unrelated second submission.
    """

    _ACQUIRE_SCRIPT = """
local bound_record_key = redis.call('GET', KEYS[2])
if bound_record_key then
  local existing_json = redis.call('GET', bound_record_key)
  if existing_json then
    local existing = cjson.decode(existing_json)
    if existing.state == 'active' and tonumber(ARGV[2]) < tonumber(existing.expires_at_epoch) then
      return cjson.encode({status='existing', record=existing})
    end
    if existing.state == 'consumed' then
      return cjson.encode({status='existing', record=existing})
    end
    if existing.state ~= 'active' and existing.state ~= 'expired' then
      return cjson.encode({status='invalid'})
    end
  end
  redis.call('DEL', bound_record_key)
  redis.call('DEL', KEYS[2])
end
redis.call('SET', KEYS[1], ARGV[1], 'EX', tonumber(ARGV[3]))
redis.call('SET', KEYS[2], KEYS[1], 'EX', tonumber(ARGV[3]))
return cjson.encode({status='created', record=cjson.decode(ARGV[1])})
""".strip()

    _CONSUME_SCRIPT = """
local record_json = redis.call('GET', KEYS[1])
if not record_json then
  return cjson.encode({status='not_found'})
end
local record = cjson.decode(record_json)
if record.expert_scope_handle ~= ARGV[1] then
  return cjson.encode({status='scope'})
end
if record.state == 'active' and tonumber(ARGV[3]) >= tonumber(record.expires_at_epoch) then
  record.state = 'expired'
  redis.call('SET', KEYS[1], cjson.encode(record), 'EX', tonumber(ARGV[4]))
  return cjson.encode({status='expired', record=record})
end
if record.state == 'consumed' then
  if record.consumed_request_key == ARGV[2] then
    return cjson.encode({status='duplicate', record=record})
  end
  return cjson.encode({status='consumed', record=record})
end
if record.state == 'expired' then
  return cjson.encode({status='expired', record=record})
end
record.state = 'consumed'
record.consumed_request_key = ARGV[2]
redis.call('SET', KEYS[1], cjson.encode(record), 'EX', tonumber(ARGV[4]))
return cjson.encode({status='claimed', record=record})
""".strip()

    _INSPECT_SCRIPT = """
local record_json = redis.call('GET', KEYS[1])
if not record_json then
  return cjson.encode({status='not_found'})
end
local record = cjson.decode(record_json)
if record.expert_scope_handle ~= ARGV[1] then
  return cjson.encode({status='scope'})
end
if record.state == 'active' and tonumber(ARGV[2]) >= tonumber(record.expires_at_epoch) then
  record.state = 'expired'
  redis.call('SET', KEYS[1], cjson.encode(record), 'EX', tonumber(ARGV[3]))
  return cjson.encode({status='expired', record=record})
end
if record.state == 'consumed' then
  return cjson.encode({status='consumed', record=record})
end
if record.state == 'expired' then
  return cjson.encode({status='expired', record=record})
end
if record.state == 'active' then
  return cjson.encode({status='active', record=record})
end
return cjson.encode({status='invalid'})
""".strip()

    def __init__(
        self,
        redis_client: RedisStateClient,
        *,
        namespace: str = "fde_phase3",
        retained_state_seconds: int = 86_400,
    ) -> None:
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("namespace is required")
        if isinstance(retained_state_seconds, bool) or retained_state_seconds < 1:
            raise ValueError("retained_state_seconds must be positive")
        self._redis = redis_client
        self._namespace = namespace.strip()
        self._retained_state_seconds = retained_state_seconds

    def acquire(self, candidate: ContinuationRecord, *, now: datetime) -> ContinuationRecord:
        if not isinstance(candidate, ContinuationRecord):
            raise ValueError("candidate must be a ContinuationRecord")
        _require_aware_datetime(now, "now")
        payload = self._serialize_record(candidate)
        result = self._eval_result(
            self._ACQUIRE_SCRIPT,
            2,
            self._record_key(candidate.handle_hash),
            self._binding_key(
                candidate.expert_scope_handle,
                candidate.question_binding_ref,
            ),
            payload,
            str(_epoch_millis(now)),
            str(self._retention_ttl(candidate.expires_at, now)),
        )
        if result.get("status") not in {"created", "existing"}:
            raise RuntimeError("continuation state store returned an invalid acquisition result")
        return self._record_from_result(result)

    def consume(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        request_key: str,
        now: datetime,
    ) -> _ContinuationConsumeResult:
        _require_aware_datetime(now, "now")
        result = self._eval_result(
            self._CONSUME_SCRIPT,
            1,
            self._record_key(handle_hash),
            expert_scope_handle,
            request_key,
            str(_epoch_millis(now)),
            str(self._retained_state_seconds),
        )
        status = result.get("status")
        if status == "not_found":
            raise ContinuationNotFoundError("continuation cannot be resolved")
        if status == "scope":
            raise ContinuationScopeError("continuation does not belong to this expert")
        if status == "expired":
            raise ContinuationExpiredError("continuation is expired")
        if status == "consumed":
            raise ContinuationConsumedError("continuation is already consumed")
        if status not in {"claimed", "duplicate"}:
            raise RuntimeError("continuation state store returned an invalid consumption result")
        return _ContinuationConsumeResult(
            record=self._record_from_result(result),
            duplicate=status == "duplicate",
        )

    def inspect(
        self,
        *,
        handle_hash: str,
        expert_scope_handle: str,
        now: datetime,
    ) -> ContinuationRecord:
        _require_aware_datetime(now, "now")
        result = self._eval_result(
            self._INSPECT_SCRIPT,
            1,
            self._record_key(handle_hash),
            expert_scope_handle,
            str(_epoch_millis(now)),
            str(self._retained_state_seconds),
        )
        status = result.get("status")
        if status == "not_found":
            raise ContinuationNotFoundError("continuation cannot be resolved")
        if status == "scope":
            raise ContinuationScopeError("continuation does not belong to this expert")
        if status == "expired":
            raise ContinuationExpiredError("continuation is expired")
        if status == "consumed":
            raise ContinuationConsumedError("continuation is already consumed")
        if status != "active":
            raise RuntimeError("continuation state store returned an invalid inspection result")
        return self._record_from_result(result)

    def _record_key(self, handle_hash: str) -> str:
        return f"{self._namespace}:continuation:record:{_digest_key(handle_hash)}"

    def _binding_key(self, expert_scope_handle: str, question_binding_ref: str) -> str:
        material = "\x1f".join((expert_scope_handle, question_binding_ref))
        return f"{self._namespace}:continuation:binding:{_digest_key(material)}"

    def _retention_ttl(self, expires_at: datetime, now: datetime) -> int:
        return max(
            self._retained_state_seconds,
            int((expires_at - now).total_seconds()) + self._retained_state_seconds,
        )

    def _eval_result(self, script: str, numkeys: int, *args: str) -> dict[str, Any]:
        raw = self._redis.eval(script, numkeys, *args)
        decoded = _decode_json(raw)
        if not isinstance(decoded, dict):
            raise RuntimeError("continuation state store returned invalid JSON")
        return decoded

    @staticmethod
    def _serialize_record(record: ContinuationRecord) -> str:
        return json.dumps(
            {
                "handle_hash": record.handle_hash,
                "handle_nonce": record.handle_nonce,
                "expert_scope_handle": record.expert_scope_handle,
                "question_binding_ref": record.question_binding_ref,
                "expires_at_epoch": _epoch_millis(record.expires_at),
                "state": record.state.value,
                "consumed_request_key": record.consumed_request_key,
            },
            separators=(",", ":"),
            sort_keys=True,
        )

    @staticmethod
    def _record_from_result(result: dict[str, Any]) -> ContinuationRecord:
        raw = result.get("record")
        if not isinstance(raw, dict):
            raise RuntimeError("continuation state result omitted its record")
        epoch = raw.get("expires_at_epoch")
        if isinstance(epoch, bool) or not isinstance(epoch, int):
            raise RuntimeError("continuation state record has invalid expiry")
        try:
            state = ContinuationState(raw["state"])
            expires_at = datetime.fromtimestamp(epoch / 1000, tz=timezone.utc)
            return ContinuationRecord(
                handle_hash=raw["handle_hash"],
                handle_nonce=raw["handle_nonce"],
                expert_scope_handle=raw["expert_scope_handle"],
                question_binding_ref=raw["question_binding_ref"],
                expires_at=expires_at,
                state=state,
                consumed_request_key=raw.get("consumed_request_key"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("continuation state record is invalid") from exc


class RedisEventIdempotencyStore:
    """Redis reservation store for one Bitable-led event at a time."""

    _RELEASE_SCRIPT = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
  redis.call('DEL', KEYS[1])
end
return '1'
""".strip()

    def __init__(
        self,
        redis_client: RedisStateClient,
        *,
        namespace: str = "fde_phase3",
        reservation_seconds: int = 900,
        completed_seconds: int = 604_800,
    ) -> None:
        if not isinstance(namespace, str) or not namespace.strip():
            raise ValueError("namespace is required")
        for label, value in (
            ("reservation_seconds", reservation_seconds),
            ("completed_seconds", completed_seconds),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise ValueError(f"{label} must be a positive integer")
        self._redis = redis_client
        self._namespace = namespace.strip()
        self._reservation_seconds = reservation_seconds
        self._completed_seconds = completed_seconds

    def acquire(self, key: str) -> str:
        redis_key = self._key(key)
        reserved = self._redis.set(
            redis_key,
            "reserved",
            nx=True,
            ex=self._reservation_seconds,
        )
        if reserved:
            return "acquired"
        current = _decode_text(self._redis.get(redis_key))
        if current == "completed":
            return "completed"
        if current == "reserved":
            return "in_progress"
        raise RuntimeError("event idempotency state is unavailable")

    def complete(self, key: str) -> None:
        self._redis.set(
            self._key(key),
            "completed",
            ex=self._completed_seconds,
        )

    def release_before_write(self, key: str) -> None:
        self._redis.eval(self._RELEASE_SCRIPT, 1, self._key(key), "reserved")

    def _key(self, key: str) -> str:
        if not isinstance(key, str) or not key.strip():
            raise ValueError("idempotency key is required")
        return f"{self._namespace}:event:{_digest_key(key)}"


def _epoch_millis(value: datetime) -> int:
    _require_aware_datetime(value, "datetime")
    return int(value.timestamp() * 1000)


def _digest_key(value: str) -> str:
    if not isinstance(value, str) or not value:
        raise ValueError("opaque state key is required")
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _decode_json(value: str | bytes) -> object:
    text = _decode_text(value)
    if text is None:
        raise RuntimeError("Redis returned no state result")
    try:
        return json.loads(text)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Redis returned invalid state JSON") from exc


def _decode_text(value: str | bytes | None) -> str | None:
    if value is None:
        return None
    if isinstance(value, bytes):
        return value.decode("utf-8")
    if isinstance(value, str):
        return value
    raise RuntimeError("Redis returned an unsupported state value")


def _require_aware_datetime(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be timezone-aware")
