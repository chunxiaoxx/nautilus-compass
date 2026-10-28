from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from services.fde_phase3_continuations import (
    ContinuationConsumedError,
    ContinuationExpiredError,
    ContinuationScopeError,
    EligibleQuestionContinuation,
    HmacContinuationService,
    InMemoryContinuationStore,
)


NOW = datetime(2026, 7, 24, 9, tzinfo=timezone.utc)


def _eligibility(**overrides: object) -> EligibleQuestionContinuation:
    values: dict[str, object] = {
        "expert_scope_handle": "mentor_expert_001",
        "question_binding_ref": "question_binding_001",
        "question_state": "eligible_for_interaction",
        "expires_at": NOW + timedelta(hours=2),
    }
    values.update(overrides)
    return EligibleQuestionContinuation(**values)


def _service() -> HmacContinuationService:
    return HmacContinuationService(
        secret=b"continuation-test-secret-material-32bytes",
        store=InMemoryContinuationStore(),
    )


def test_eligible_question_gets_one_opaque_idempotent_mentor_action() -> None:
    service = _service()

    action = service.issue(eligible_question=_eligibility(), now=NOW)
    duplicate_delivery = service.issue(eligible_question=_eligibility(), now=NOW)

    assert action.continuation_reference == duplicate_delivery.continuation_reference
    assert action.to_mentor_payload() == {
        "action": "open_interaction_evidence",
        "continuation_reference": action.continuation_reference,
        "expires_at": "2026-07-24T11:00:00+00:00",
        "recovery_action": "request_continuation_reissue",
    }
    serialized = str(action.to_mentor_payload())
    assert "record_id" not in serialized
    assert "question_binding_001" not in serialized


def test_issue_requires_eligible_question_state() -> None:
    service = _service()

    with pytest.raises(ValueError, match="eligible_for_interaction"):
        service.issue(
            eligible_question=_eligibility(question_state="precheck_pending"),
            now=NOW,
        )


def test_consumption_is_bound_to_expert_scope_and_idempotency_key() -> None:
    service = _service()
    action = service.issue(eligible_question=_eligibility(), now=NOW)

    with pytest.raises(ContinuationScopeError):
        service.consume(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_other",
            request_key="interaction_request_001",
            now=NOW,
        )

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
    assert duplicate.question_binding_ref == "question_binding_001"
    with pytest.raises(ContinuationConsumedError):
        service.consume(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_001",
            request_key="interaction_request_002",
            now=NOW,
        )


def test_inspect_allows_only_the_own_active_continuation() -> None:
    service = _service()
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
    service.consume(
        continuation_reference=action.continuation_reference,
        expert_scope_handle="mentor_expert_001",
        request_key="interaction_request_001",
        now=NOW,
    )
    with pytest.raises(ContinuationConsumedError):
        service.inspect(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_001",
            now=NOW,
        )


def test_expired_continuation_never_consumes() -> None:
    service = _service()
    action = service.issue(
        eligible_question=_eligibility(expires_at=NOW + timedelta(minutes=1)),
        now=NOW,
    )

    with pytest.raises(ContinuationExpiredError):
        service.consume(
            continuation_reference=action.continuation_reference,
            expert_scope_handle="mentor_expert_001",
            request_key="interaction_request_001",
            now=NOW + timedelta(minutes=1),
        )
