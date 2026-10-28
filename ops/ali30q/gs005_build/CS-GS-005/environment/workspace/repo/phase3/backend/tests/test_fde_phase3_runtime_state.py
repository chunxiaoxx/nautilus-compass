from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from services.fde_phase3_continuations import (
    ContinuationConsumedError,
    ContinuationExpiredError,
    ContinuationScopeError,
    EligibleQuestionContinuation,
    HmacContinuationService,
)
from services.fde_phase3_runtime_state import (
    RedisContinuationStore,
    RedisEventIdempotencyStore,
)


NOW = datetime(2026, 7, 24, 9, tzinfo=timezone.utc)


class FakeRedis:
    """Small deterministic Redis substitute for Phase 3 atomic-state tests."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.expirations: dict[str, int] = {}

    def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool = False,
        ex: int | None = None,
    ) -> bool:
        if nx and key in self.values:
            return False
        self.values[key] = value
        if ex is not None:
            self.expirations[key] = ex
        return True

    def get(self, key: str) -> str | None:
        return self.values.get(key)

    def eval(self, script: str, numkeys: int, *args: str) -> str:
        if script == RedisContinuationStore._ACQUIRE_SCRIPT:
            assert numkeys == 2
            record_key, binding_key, candidate_json, now_epoch, ttl_seconds = args
            candidate = json.loads(candidate_json)
            existing_record_key = self.values.get(binding_key)
            if existing_record_key is not None:
                existing_json = self.values.get(existing_record_key)
                if existing_json is not None:
                    existing = json.loads(existing_json)
                    if (
                        existing["state"] == "active"
                        and int(now_epoch) < int(existing["expires_at_epoch"])
                    ):
                        return json.dumps({"status": "existing", "record": existing})
                    if existing["state"] == "consumed":
                        return json.dumps({"status": "existing", "record": existing})
                    if existing["state"] not in {"active", "expired"}:
                        return json.dumps({"status": "invalid"})
                self.values.pop(existing_record_key, None)
                self.values.pop(binding_key, None)
            self.values[record_key] = candidate_json
            self.values[binding_key] = record_key
            self.expirations[record_key] = int(ttl_seconds)
            self.expirations[binding_key] = int(ttl_seconds)
            return json.dumps({"status": "created", "record": candidate})

        if script == RedisContinuationStore._CONSUME_SCRIPT:
            assert numkeys == 1
            record_key, expert_scope_handle, request_key, now_epoch, ttl_seconds = args
            record_json = self.values.get(record_key)
            if record_json is None:
                return json.dumps({"status": "not_found"})
            record = json.loads(record_json)
            if record["expert_scope_handle"] != expert_scope_handle:
                return json.dumps({"status": "scope"})
            if record["state"] == "active" and int(now_epoch) >= int(record["expires_at_epoch"]):
                record["state"] = "expired"
                self.values[record_key] = json.dumps(record, sort_keys=True)
                self.expirations[record_key] = int(ttl_seconds)
                return json.dumps({"status": "expired", "record": record})
            if record["state"] == "consumed":
                if record["consumed_request_key"] == request_key:
                    return json.dumps({"status": "duplicate", "record": record})
                return json.dumps({"status": "consumed", "record": record})
            if record["state"] == "expired":
                return json.dumps({"status": "expired", "record": record})
            record["state"] = "consumed"
            record["consumed_request_key"] = request_key
            self.values[record_key] = json.dumps(record, sort_keys=True)
            self.expirations[record_key] = int(ttl_seconds)
            return json.dumps({"status": "claimed", "record": record})

        if script == RedisContinuationStore._INSPECT_SCRIPT:
            assert numkeys == 1
            record_key, expert_scope_handle, now_epoch, ttl_seconds = args
            record_json = self.values.get(record_key)
            if record_json is None:
                return json.dumps({"status": "not_found"})
            record = json.loads(record_json)
            if record["expert_scope_handle"] != expert_scope_handle:
                return json.dumps({"status": "scope"})
            if record["state"] == "active" and int(now_epoch) >= int(record["expires_at_epoch"]):
                record["state"] = "expired"
                self.values[record_key] = json.dumps(record, sort_keys=True)
                self.expirations[record_key] = int(ttl_seconds)
                return json.dumps({"status": "expired", "record": record})
            if record["state"] == "consumed":
                return json.dumps({"status": "consumed", "record": record})
            if record["state"] == "expired":
                return json.dumps({"status": "expired", "record": record})
            return json.dumps({"status": "active", "record": record})

        if script == RedisEventIdempotencyStore._RELEASE_SCRIPT:
            assert numkeys == 1
            key, expected = args
            if self.values.get(key) == expected:
                self.values.pop(key, None)
                self.expirations.pop(key, None)
            return "1"

        raise AssertionError("unknown Lua script")


def _eligibility(**overrides: object) -> EligibleQuestionContinuation:
    values: dict[str, object] = {
        "expert_scope_handle": "mentor_expert_001",
        "question_binding_ref": "question_binding_001",
        "question_state": "eligible_for_interaction",
        "expires_at": NOW + timedelta(hours=2),
    }
    values.update(overrides)
    return EligibleQuestionContinuation(**values)


def _continuation_service(redis: FakeRedis) -> HmacContinuationService:
    return HmacContinuationService(
        secret=b"continuation-test-secret-material-32bytes",
        store=RedisContinuationStore(redis),
    )


def test_redis_continuation_store_is_idempotent_and_scope_bound() -> None:
    redis = FakeRedis()
    service = _continuation_service(redis)

    action = service.issue(eligible_question=_eligibility(), now=NOW)
    duplicate_delivery = service.issue(eligible_question=_eligibility(), now=NOW)

    assert action.continuation_reference == duplicate_delivery.continuation_reference
    consumed = service.consume(
        continuation_reference=action.continuation_reference,
        expert_scope_handle="mentor_expert_001",
        request_key="interaction_request_001",
        now=NOW,
    )
    duplicate = service.consume(
        continuation_reference=action.continuation_reference,
        expert_scope_handle="mentor_expert_001",
        request_key="interaction_request_001",
        now=NOW,
    )

    assert consumed.duplicate is False
    assert duplicate.duplicate is True
    with pytest.raises(ContinuationScopeError):
        service.consume(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_other",
            request_key="interaction_request_001",
            now=NOW,
        )
    with pytest.raises(ContinuationConsumedError):
        service.consume(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_001",
            request_key="interaction_request_002",
            now=NOW,
        )


def test_redis_continuation_store_expires_and_permits_a_new_issuance() -> None:
    redis = FakeRedis()
    service = _continuation_service(redis)
    first = service.issue(
        eligible_question=_eligibility(expires_at=NOW + timedelta(minutes=1)),
        now=NOW,
    )

    with pytest.raises(ContinuationExpiredError):
        service.consume(
            continuation_reference=first.continuation_reference,
            expert_scope_handle="mentor_expert_001",
            request_key="interaction_request_001",
            now=NOW + timedelta(minutes=1),
        )

    reissued = service.issue(
        eligible_question=_eligibility(expires_at=NOW + timedelta(hours=2)),
        now=NOW + timedelta(minutes=1),
    )

    assert reissued.continuation_reference != first.continuation_reference


def test_redis_continuation_store_inspects_only_an_active_own_continuation() -> None:
    redis = FakeRedis()
    service = _continuation_service(redis)
    action = service.issue(eligible_question=_eligibility(), now=NOW)

    inspected = service.inspect(
        continuation_reference=action.continuation_reference,
        expert_scope_handle="mentor_expert_001",
        now=NOW,
    )

    assert inspected.question_binding_ref == "question_binding_001"
    with pytest.raises(ContinuationScopeError):
        service.inspect(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_other",
            now=NOW,
        )


def test_redis_event_idempotency_reserves_completes_and_releases_before_write() -> None:
    redis = FakeRedis()
    store = RedisEventIdempotencyStore(redis)

    assert store.acquire("phase3-event-001") == "acquired"
    assert store.acquire("phase3-event-001") == "in_progress"
    store.release_before_write("phase3-event-001")
    assert store.acquire("phase3-event-001") == "acquired"
    store.complete("phase3-event-001")
    assert store.acquire("phase3-event-001") == "completed"


def test_redis_state_never_falls_back_to_process_memory() -> None:
    class UnavailableRedis:
        def set(self, *args: object, **kwargs: object) -> bool:
            raise RuntimeError("redis unavailable")

        def get(self, *args: object, **kwargs: object) -> str | None:
            raise RuntimeError("redis unavailable")

        def eval(self, *args: object, **kwargs: object) -> str:
            raise RuntimeError("redis unavailable")

    with pytest.raises(RuntimeError, match="redis unavailable"):
        RedisEventIdempotencyStore(UnavailableRedis()).acquire("phase3-event-001")
