from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from api.fde_phase3_runtime import InteractionEvidenceSubmission, InteractionSubmissionResult
from services.fde_phase3_interaction_contract import RoundFeedback
from services.fde_phase3_continuations import (
    EligibleQuestionContinuation,
    HmacContinuationService,
    InMemoryContinuationStore,
)
from services.fde_phase3_mentor_continuation_workflow import (
    MentorInteractionBinding,
    MentorContinuationWorkflowService,
)


NOW = datetime(2026, 7, 24, 9, tzinfo=timezone.utc)


class FakeBindingResolver:
    def __init__(self, binding: MentorInteractionBinding | None) -> None:
        self.binding = binding
        self.references: list[str] = []

    def resolve(self, *, question_binding_ref: str) -> MentorInteractionBinding | None:
        self.references.append(question_binding_ref)
        return self.binding


class FakeInteractionSubmitter:
    def __init__(self) -> None:
        self.calls: list[tuple[MentorInteractionBinding, str]] = []
        self.next_outcomes = ["submitted", "already_submitted"]

    def submit(
        self,
        *,
        binding: MentorInteractionBinding,
        evidence: InteractionEvidenceSubmission,
        request_key: str,
    ) -> InteractionSubmissionResult:
        assert evidence.tool_name == "豆包办公任务"
        assert evidence.turn_count == 6
        self.calls.append((binding, request_key))
        return InteractionSubmissionResult(outcome=self.next_outcomes.pop(0))


def _continuation_service() -> HmacContinuationService:
    return HmacContinuationService(
        secret=b"continuation-test-secret-material-32bytes",
        store=InMemoryContinuationStore(),
    )


def _binding(**overrides: object) -> MentorInteractionBinding:
    values: dict[str, object] = {
        "question_binding_ref": "question_binding_001",
        "expert_scope_handle": "mentor_expert_001",
        "question_record_id": "rec_question_001",
        "expert_record_id": "rec_expert_001",
        "question_state": "eligible_for_interaction",
    }
    values.update(overrides)
    return MentorInteractionBinding(**values)


def _evidence() -> InteractionEvidenceSubmission:
    return InteractionEvidenceSubmission(
        tool_name="豆包办公任务",
        turn_count=6,
        round_feedback=tuple(
            RoundFeedback(
                ordinal=ordinal,
                rating="like",
                issue_label="correct",
                reason=f"第{ordinal}轮回答包含具体业务依据。",
            )
            for ordinal in range(1, 7)
        ),
        dialogue_image_refs=("file_token_001",),
        trajectory_link="https://example.invalid/trajectory/001",
        log_id="doubao-log-001",
        attested_by_expert=True,
    )


def _workflow(
    *,
    binding: MentorInteractionBinding | None = None,
) -> tuple[MentorContinuationWorkflowService, HmacContinuationService, FakeInteractionSubmitter]:
    continuations = _continuation_service()
    resolver = FakeBindingResolver(binding or _binding())
    submitter = FakeInteractionSubmitter()
    return (
        MentorContinuationWorkflowService(
            continuations=continuations,
            bindings=resolver,
            submitter=submitter,
            clock=lambda: NOW,
        ),
        continuations,
        submitter,
    )


def _action(continuations: HmacContinuationService) -> str:
    return continuations.issue(
        eligible_question=EligibleQuestionContinuation(
            expert_scope_handle="mentor_expert_001",
            question_binding_ref="question_binding_001",
            question_state="eligible_for_interaction",
            expires_at=NOW + timedelta(hours=2),
        ),
        now=NOW,
    ).continuation_reference


def test_workflow_opens_and_submits_through_one_opaque_continuation() -> None:
    workflow, continuations, submitter = _workflow()
    reference = _action(continuations)

    page = workflow.open(
        expert_scope_handle="mentor_expert_001",
        continuation_reference=reference,
    )
    first = workflow.submit(
        expert_scope_handle="mentor_expert_001",
        continuation_reference=reference,
        evidence=_evidence(),
        request_key="interaction_request_001",
    )
    duplicate = workflow.submit(
        expert_scope_handle="mentor_expert_001",
        continuation_reference=reference,
        evidence=_evidence(),
        request_key="interaction_request_001",
    )

    assert page is not None
    assert "rec_" not in str(page.to_payload())
    assert first.outcome == "submitted"
    assert duplicate.outcome == "already_submitted"
    assert [binding.question_record_id for binding, _ in submitter.calls] == [
        "rec_question_001",
        "rec_question_001",
    ]


def test_workflow_rejects_a_stale_question_before_consuming_the_continuation() -> None:
    workflow, continuations, submitter = _workflow(
        binding=_binding(question_state="question_repair_required"),
    )
    reference = _action(continuations)

    with pytest.raises(PermissionError, match="eligible"):
        workflow.submit(
            expert_scope_handle="mentor_expert_001",
            continuation_reference=reference,
            evidence=_evidence(),
            request_key="interaction_request_001",
        )

    assert submitter.calls == []
    assert continuations.inspect(
        continuation_reference=reference,
        expert_scope_handle="mentor_expert_001",
        now=NOW,
    ).question_binding_ref == "question_binding_001"


def test_workflow_rejects_a_binding_owned_by_another_expert() -> None:
    workflow, continuations, _ = _workflow(
        binding=_binding(expert_scope_handle="mentor_expert_other"),
    )
    reference = _action(continuations)

    with pytest.raises(PermissionError, match="scope"):
        workflow.open(
            expert_scope_handle="mentor_expert_001",
            continuation_reference=reference,
        )
