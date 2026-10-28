from __future__ import annotations

import pytest

from services.fde_phase3_mentor_projection import (
    CuratedLesson,
    HmacTaskHandleIssuer,
    MentorKnowledgePack,
    build_task_guidance,
)
from services.fde_phase3_single_submission_qc import (
    P0Disposition,
    SubmissionEvidence,
    evaluate_submission,
)


TASK_HANDLE_ISSUER = HmacTaskHandleIssuer(b"phase3-test-task-handle-secret")


def complete_evidence(**overrides: object) -> SubmissionEvidence:
    values: dict[str, object] = {
        "submission_record_id": "rec_submission_001",
        "expert_record_id": "rec_expert_001",
        "tool_name": "豆包办公任务",
        "turn_count": 6,
        "has_dialogue_images": True,
        "has_trajectory_link": True,
        "has_log_id": True,
        "attested_by_expert": True,
        "workflow_profile": "phase3_interactive",
        "task_contract_complete": True,
        "scene_tag_match": True,
        "authenticity_ok": True,
        "safety_ok": True,
        "answerable": True,
        "dedupe_clear": True,
        "all_turns_have_human_feedback_reasons": True,
        "trajectory_coherent": True,
        "within_submission_deadline": True,
        "model_confidence": 0.92,
        "quality_issue_codes": (),
        "integrity_issue_codes": (),
    }
    values.update(overrides)
    return SubmissionEvidence(**values)


def test_complete_high_confidence_submission_is_buyer_ready_not_accepted() -> None:
    decision = evaluate_submission(complete_evidence(), policy_version="p0-v1")

    assert decision.disposition is P0Disposition.BUYER_READY
    assert decision.reason_codes == ()
    assert decision.policy_version == "p0-v1"
    assert decision.is_buyer_verdict is False


def test_missing_interaction_evidence_routes_to_repair_with_actionable_reason() -> None:
    decision = evaluate_submission(
        complete_evidence(turn_count=5, has_dialogue_images=False),
        policy_version="p0-v1",
    )

    assert decision.disposition is P0Disposition.REPAIR_REQUIRED
    assert decision.reason_codes == ("minimum_turns_not_met", "dialogue_images_missing")
    assert decision.repair_guidance == (
        "请在豆包办公任务中完成至少 6 轮有效问答，并补充完整对话截图后重新提交。"
    )


def test_integrity_risk_blocks_submission_before_quality_routing() -> None:
    decision = evaluate_submission(
        complete_evidence(integrity_issue_codes=("evidence_mismatch",)),
        policy_version="p0-v1",
    )

    assert decision.disposition is P0Disposition.BLOCKED
    assert decision.reason_codes == ("evidence_mismatch",)


@pytest.mark.parametrize(
    ("evidence_field", "reason_code"),
    [
        ("task_contract_complete", "task_contract_incomplete"),
        ("scene_tag_match", "scene_tag_mismatch"),
        ("authenticity_ok", "authenticity_check_failed"),
        ("answerable", "answerability_check_failed"),
        ("dedupe_clear", "dedupe_or_conflict_detected"),
        (
            "all_turns_have_human_feedback_reasons",
            "per_turn_human_feedback_missing",
        ),
        ("trajectory_coherent", "trajectory_not_coherent"),
        ("within_submission_deadline", "submission_deadline_missed"),
    ],
)
def test_each_repairable_phase3_p0_gate_routes_to_repair(
    evidence_field: str,
    reason_code: str,
) -> None:
    decision = evaluate_submission(
        complete_evidence(**{evidence_field: False}),
        policy_version="p0-v1",
    )

    assert decision.disposition is P0Disposition.REPAIR_REQUIRED
    assert decision.reason_codes == (reason_code,)
    assert decision.is_buyer_verdict is False


def test_safety_failure_blocks_submission_before_repair_routing() -> None:
    decision = evaluate_submission(
        complete_evidence(safety_ok=False, turn_count=3),
        policy_version="p0-v1",
    )

    assert decision.disposition is P0Disposition.BLOCKED
    assert decision.reason_codes == ("safety_check_failed",)


def test_out_of_range_model_confidence_is_rejected_as_invalid_input() -> None:
    with pytest.raises(ValueError, match="model_confidence"):
        evaluate_submission(complete_evidence(model_confidence=1.1), policy_version="p0-v1")


def test_non_phase3_workflow_profile_is_rejected_before_p0_routing() -> None:
    with pytest.raises(ValueError, match="workflow_profile"):
        complete_evidence(workflow_profile="generic_evidence_pack")


def test_mentor_can_only_receive_the_requesting_experts_task_guidance() -> None:
    decision = evaluate_submission(
        complete_evidence(turn_count=3),
        policy_version="p0-v1",
    )
    pack = MentorKnowledgePack(
        version="mentor-p3-v1",
        lessons=(
            CuratedLesson(
                lesson_id="interaction-evidence",
                category="interaction_evidence",
                guidance="提交前核对轮次数、截图、轨迹链接和日志 ID。",
            ),
        ),
    )

    with pytest.raises(PermissionError, match="requesting expert"):
        build_task_guidance(
            requesting_expert_record_id="rec_expert_other",
            expert_scope_handle="mentor_expert_001",
            task_handle_issuer=TASK_HANDLE_ISSUER,
            submission_evidence=complete_evidence(),
            decision=decision,
            knowledge_pack=pack,
        )


def test_mentor_guidance_is_redacted_and_contains_only_owned_task_feedback() -> None:
    evidence = complete_evidence(turn_count=3)
    decision = evaluate_submission(evidence, policy_version="p0-v1")
    pack = MentorKnowledgePack(
        version="mentor-p3-v1",
        lessons=(
            CuratedLesson(
                lesson_id="interaction-evidence",
                category="interaction_evidence",
                guidance="提交前核对轮次数、截图、轨迹链接和日志 ID。",
            ),
        ),
    )

    guidance = build_task_guidance(
        requesting_expert_record_id="rec_expert_001",
        expert_scope_handle="mentor_expert_001",
        task_handle_issuer=TASK_HANDLE_ISSUER,
        submission_evidence=evidence,
        decision=decision,
        knowledge_pack=pack,
    )

    assert guidance.task_handle == TASK_HANDLE_ISSUER.issue(
        expert_scope_handle="mentor_expert_001",
        submission_record_id="rec_submission_001",
    )
    assert guidance.next_action == "repair_and_resubmit"
    assert guidance.reason_codes == ("minimum_turns_not_met",)
    assert guidance.knowledge_pack_version == "mentor-p3-v1"
    assert guidance.lessons[0].lesson_id == "interaction-evidence"
    assert not hasattr(guidance, "raw_buyer_feedback")
    assert not hasattr(guidance, "submission_record_id")
    assert not hasattr(guidance, "attachments")
    assert not hasattr(guidance, "dialogue_images")


def test_curated_knowledge_pack_rejects_raw_or_identity_bearing_lessons() -> None:
    with pytest.raises(ValueError, match="redacted"):
        CuratedLesson(
            lesson_id="unsafe",
            category="buyer_feedback",
            guidance="raw_buyer_feedback: keep this private",
        )
