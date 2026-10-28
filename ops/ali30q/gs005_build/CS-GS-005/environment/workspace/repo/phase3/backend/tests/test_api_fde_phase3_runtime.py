from __future__ import annotations

from collections.abc import Mapping

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api.fde_phase3_runtime import (
    EventVerification,
    InteractionSubmissionResult,
    MentorInteractionPage,
    Phase3RuntimeDependencies,
    configure_phase3_runtime,
    router,
)
from services.fde_phase3_continuations import (
    ContinuationConsumedError,
    ContinuationExpiredError,
    ContinuationScopeError,
)
from services.fde_phase3_event_orchestrator import EventHandlingResult
from services.fde_phase3_feishu_runtime_contract import MentorProjection


class FakeEventVerifier:
    def __init__(self, *, authenticated: bool = True) -> None:
        self.authenticated = authenticated
        self.calls: list[dict[str, object]] = []

    def verify(
        self,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> EventVerification:
        self.calls.append(dict(payload))
        challenge = payload.get("challenge")
        if isinstance(challenge, str):
            return EventVerification(authenticated=self.authenticated, challenge=challenge)
        return EventVerification(authenticated=self.authenticated)


class FakeEventHandler:
    def __init__(self, outcomes: list[str] | None = None) -> None:
        self.outcomes = list(outcomes or ["written_and_read_back"])
        self.events = []

    def handle(self, authenticated):
        self.events.append(authenticated)
        return EventHandlingResult(outcome=self.outcomes.pop(0))


class FakeMentorSessionVerifier:
    def authenticate(self, headers: Mapping[str, str]) -> str | None:
        if headers.get("x-mentor-session") == "valid":
            return "mentor_expert_001"
        return None


class FakeMentorStatusResolver:
    def __init__(self, projection: MentorProjection | None) -> None:
        self.projection = projection
        self.calls: list[tuple[str, str]] = []

    def resolve(self, *, expert_scope_handle: str, task_handle: str) -> MentorProjection | None:
        self.calls.append((expert_scope_handle, task_handle))
        return self.projection


class FakeMentorContinuationWorkflow:
    def __init__(self) -> None:
        self.open_calls: list[tuple[str, str]] = []
        self.submissions: list[tuple[str, str, object, str]] = []
        self.open_error: Exception | None = None
        self.submit_error: Exception | None = None
        self.result = InteractionSubmissionResult(outcome="submitted")
        self.page = MentorInteractionPage()

    def open(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
    ) -> MentorInteractionPage:
        self.open_calls.append((expert_scope_handle, continuation_reference))
        if self.open_error is not None:
            raise self.open_error
        return self.page

    def submit(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
        evidence: object,
        request_key: str,
    ) -> InteractionSubmissionResult:
        self.submissions.append(
            (expert_scope_handle, continuation_reference, evidence, request_key)
        )
        if self.submit_error is not None:
            raise self.submit_error
        return self.result


class RaisingEventVerifier:
    def verify(
        self,
        *,
        headers: Mapping[str, str],
        payload: Mapping[str, object],
    ) -> EventVerification:
        raise RuntimeError("internal verifier detail must not reach the caller")


@pytest.fixture
def runtime_client():
    verifier = FakeEventVerifier()
    handler = FakeEventHandler()
    resolver = FakeMentorStatusResolver(
        MentorProjection(
            expert_scope_handle="mentor_expert_001",
            task_handle="mentor_task_001",
            p0_disposition="buyer_ready",
            next_action="await_buyer_mapping",
            reason_codes=(),
            repair_guidance="请等待后续流程通知。",
            knowledge_pack_version="mentor-p3-v1",
            lessons=(),
        )
    )
    workflow = FakeMentorContinuationWorkflow()
    configure_phase3_runtime(
        Phase3RuntimeDependencies(
            event_verifier=verifier,
            event_handler=handler,
            mentor_session_verifier=FakeMentorSessionVerifier(),
            mentor_status_resolver=resolver,
            mentor_continuation_workflow=workflow,
        )
    )
    app = FastAPI()
    app.include_router(router)
    try:
        yield TestClient(app), verifier, handler, resolver, workflow
    finally:
        configure_phase3_runtime(None)


def event_body(**overrides: object) -> dict[str, object]:
    event: dict[str, object] = {
        "route": "submission_created",
        "record_id": "rec_submission_001",
        "record_version": 3,
        "source_event_id": "evt_feishu_001",
    }
    event.update(overrides)
    return {"event": event}


CONTINUATION_REFERENCE = "mentor_continue_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456"


def interaction_body(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "tool_name": "豆包办公任务",
        "turn_count": 6,
        "round_feedback": [
            {
                "ordinal": ordinal,
                "rating": "like",
                "issue_label": "correct",
                "reason": f"第{ordinal}轮回答包含了可核对的业务依据。",
            }
            for ordinal in range(1, 7)
        ],
        "dialogue_image_refs": ["file_token_001"],
        "trajectory_link": "https://example.invalid/trajectory/001",
        "log_id": "log_001",
        "attested_by_expert": True,
    }
    payload.update(overrides)
    return payload


def test_event_endpoint_returns_feishu_challenge_without_dispatch(runtime_client) -> None:
    client, _, handler, _, _ = runtime_client

    response = client.post("/api/platform/fde/phase3/events", json={"challenge": "nonce-123"})

    assert response.status_code == 200
    assert response.json() == {"challenge": "nonce-123"}
    assert handler.events == []


def test_event_endpoint_rejects_invalid_event_authentication() -> None:
    verifier = FakeEventVerifier(authenticated=False)
    handler = FakeEventHandler()
    configure_phase3_runtime(
        Phase3RuntimeDependencies(
            event_verifier=verifier,
            event_handler=handler,
            mentor_session_verifier=FakeMentorSessionVerifier(),
            mentor_status_resolver=FakeMentorStatusResolver(None),
        )
    )
    app = FastAPI()
    app.include_router(router)
    try:
        response = TestClient(app).post("/api/platform/fde/phase3/events", json=event_body())
    finally:
        configure_phase3_runtime(None)

    assert response.status_code == 401
    assert response.json() == {"detail": "event authentication failed"}
    assert handler.events == []


def test_event_endpoint_fails_closed_when_the_verifier_errors() -> None:
    configure_phase3_runtime(
        Phase3RuntimeDependencies(
            event_verifier=RaisingEventVerifier(),
            event_handler=FakeEventHandler(),
            mentor_session_verifier=FakeMentorSessionVerifier(),
            mentor_status_resolver=FakeMentorStatusResolver(None),
        )
    )
    app = FastAPI()
    app.include_router(router)
    try:
        response = TestClient(app, raise_server_exceptions=False).post(
            "/api/platform/fde/phase3/events",
            json=event_body(),
        )
    finally:
        configure_phase3_runtime(None)

    assert response.status_code == 503
    assert response.json() == {"detail": "event verifier is unavailable"}
    assert "internal verifier detail" not in response.text


def test_event_endpoint_dispatches_only_metadata_and_hides_record_identity(runtime_client) -> None:
    client, _, handler, _, _ = runtime_client

    response = client.post("/api/platform/fde/phase3/events", json=event_body())

    assert response.status_code == 202
    assert response.json() == {"status": "accepted"}
    assert len(handler.events) == 1
    assert handler.events[0].event.record_id == "rec_submission_001"
    assert "rec_submission_001" not in response.text


def test_event_endpoint_acknowledges_duplicate_without_leaking_event_data(runtime_client) -> None:
    client, _, handler, _, _ = runtime_client
    handler.outcomes = ["already_processed"]

    response = client.post("/api/platform/fde/phase3/events", json=event_body())

    assert response.status_code == 200
    assert response.json() == {"status": "already_processed"}
    assert "rec_submission_001" not in response.text


def test_event_endpoint_rejects_unapproved_route_without_echoing_body(runtime_client) -> None:
    client, _, handler, _, _ = runtime_client

    response = client.post(
        "/api/platform/fde/phase3/events",
        json=event_body(route="developer_chat", record_id="rec_should_not_echo"),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid event metadata"}
    assert "rec_should_not_echo" not in response.text
    assert handler.events == []


def test_mentor_status_requires_authenticated_scope_and_opaque_task_handle(runtime_client) -> None:
    client, _, _, resolver, _ = runtime_client

    unauthorized = client.get("/api/platform/fde/phase3/mentor/status?task_handle=mentor_task_001")
    authorized = client.get(
        "/api/platform/fde/phase3/mentor/status?task_handle=mentor_task_001",
        headers={"x-mentor-session": "valid"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json()["status"]["label"] == "题目检查中"
    assert authorized.json()["primary_action"]["code"] == "wait_for_question_review"
    assert "task_handle" not in authorized.text
    assert "reason_codes" not in authorized.text
    assert "record_id" not in authorized.text
    assert resolver.calls == [("mentor_expert_001", "mentor_task_001")]


def test_mentor_status_refuses_cross_scope_projection(runtime_client) -> None:
    client, _, _, resolver, _ = runtime_client
    resolver.projection = MentorProjection(
        expert_scope_handle="mentor_expert_other",
        task_handle="mentor_task_001",
        p0_disposition="buyer_ready",
        next_action="await_buyer_mapping",
        reason_codes=(),
        repair_guidance="请等待后续流程通知。",
        knowledge_pack_version="mentor-p3-v1",
        lessons=(),
    )

    response = client.get(
        "/api/platform/fde/phase3/mentor/status?task_handle=mentor_task_001",
        headers={"x-mentor-session": "valid"},
    )

    assert response.status_code == 403
    assert response.json() == {"detail": "mentor scope mismatch"}


def test_mentor_can_open_its_opaque_interaction_continuation(runtime_client) -> None:
    client, _, _, _, workflow = runtime_client

    response = client.get(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}",
        headers={"x-mentor-session": "valid"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "action": "submit_interaction_evidence",
        "allowed_tool": "豆包办公任务",
        "minimum_turn_count": 6,
        "required_fields": [
            "round_feedback",
            "dialogue_image_refs",
            "trajectory_link",
            "log_id",
            "attested_by_expert",
        ],
    }
    assert workflow.open_calls == [("mentor_expert_001", CONTINUATION_REFERENCE)]
    assert "record_id" not in response.text


@pytest.mark.parametrize(
    "error",
    [
        ContinuationScopeError("other expert"),
        ContinuationExpiredError("expired"),
        ContinuationConsumedError("consumed"),
    ],
)
def test_mentor_continuation_errors_are_generic_and_do_not_leak_state(runtime_client, error) -> None:
    client, _, _, _, workflow = runtime_client
    workflow.open_error = error

    response = client.get(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}",
        headers={"x-mentor-session": "valid"},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "continuation unavailable"}
    assert str(error) not in response.text


def test_interaction_submission_uses_only_public_fields_and_is_idempotent(runtime_client) -> None:
    client, _, _, _, workflow = runtime_client

    first = client.post(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}/interaction",
        headers={"x-mentor-session": "valid"},
        json=interaction_body(),
    )
    workflow.result = InteractionSubmissionResult(outcome="already_submitted")
    duplicate = client.post(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}/interaction",
        headers={"x-mentor-session": "valid"},
        json=interaction_body(),
    )

    assert first.status_code == 202
    assert first.json() == {"status": "submitted"}
    assert duplicate.status_code == 200
    assert duplicate.json() == {"status": "already_submitted"}
    assert len(workflow.submissions) == 2
    _, _, evidence, request_key = workflow.submissions[0]
    assert evidence.tool_name == "豆包办公任务"
    assert evidence.turn_count == 6
    assert len(evidence.round_feedback) == 6
    assert evidence.dialogue_image_refs == ("file_token_001",)
    assert request_key.startswith("interaction_request_")
    assert "rec_" not in request_key
    assert "record_id" not in first.text


def test_interaction_submission_rejects_client_supplied_internal_identity(runtime_client) -> None:
    client, _, _, _, workflow = runtime_client

    response = client.post(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}/interaction",
        headers={"x-mentor-session": "valid"},
        json=interaction_body(question_record_id="rec_question_001"),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid interaction submission"}
    assert workflow.submissions == []
    assert "rec_question_001" not in response.text


@pytest.mark.parametrize(
    "overrides",
    [
        {"tool_name": "other_tool"},
        {"turn_count": 5},
        {"attested_by_expert": False},
    ],
)
def test_interaction_submission_enforces_phase3_tool_turn_and_attestation(
    runtime_client,
    overrides,
) -> None:
    client, _, _, _, workflow = runtime_client

    response = client.post(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}/interaction",
        headers={"x-mentor-session": "valid"},
        json=interaction_body(**overrides),
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "invalid interaction submission"}
    assert workflow.submissions == []


def test_mentor_continuation_requires_authenticated_session(runtime_client) -> None:
    client, _, _, _, workflow = runtime_client

    response = client.get(
        f"/api/platform/fde/phase3/mentor/continuations/{CONTINUATION_REFERENCE}",
    )

    assert response.status_code == 401
    assert workflow.open_calls == []


def test_mentor_interface_contract_is_authenticated_and_versioned(runtime_client) -> None:
    client, _, _, _, _ = runtime_client

    unauthorized = client.get("/api/platform/fde/phase3/mentor/interface-contract")
    authorized = client.get(
        "/api/platform/fde/phase3/mentor/interface-contract",
        headers={"x-mentor-session": "valid"},
    )

    assert unauthorized.status_code == 401
    assert authorized.status_code == 200
    assert authorized.json()["contract_version"] == "platform-t1-interface-v1"
    assert len(authorized.json()["states"]) == 13
    assert len(authorized.json()["exception_categories"]) == 7
    assert len(authorized.json()["error_microguides"]) == 13
    assert "record_id" not in authorized.text
    assert "reason_code" not in authorized.text
