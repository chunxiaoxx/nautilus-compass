from __future__ import annotations

from dataclasses import fields

import pytest

from services.fde_phase3_question_precheck import (
    QuestionPrecheckDisposition,
    QuestionPrecheckEvidence,
    evaluate_question_precheck,
    question_precheck_updates,
    require_eligible_question_state,
)


def complete_question(**overrides: object) -> QuestionPrecheckEvidence:
    values: dict[str, object] = {
        "question_record_id": "rec_question_001",
        "expert_record_id": "rec_expert_001",
        "workflow_profile": "phase3_interactive",
        "has_question_text": True,
        "domain_tags_complete": True,
        "supporting_attachment_present": True,
        "attachment_source_complete": True,
        "followup_interaction_plan_complete": True,
        "authenticity_ok": True,
        "safety_ok": True,
        "answerable": True,
        "dedupe_clear": True,
        "model_confidence": 0.92,
        "quality_issue_codes": (),
        "integrity_issue_codes": (),
    }
    values.update(overrides)
    return QuestionPrecheckEvidence(**values)


def test_complete_question_becomes_eligible_for_interaction_not_buyer_accepted() -> None:
    decision = evaluate_question_precheck(complete_question(), policy_version="question-p0-v1")

    assert decision.disposition is QuestionPrecheckDisposition.ELIGIBLE_FOR_INTERACTION
    assert decision.reason_codes == ()
    assert decision.is_buyer_verdict is False
    assert question_precheck_updates(decision) == {
        "题目状态": "eligible_for_interaction",
        "自动P0状态": "可开始交互",
        "自动QC置信度": 0.92,
        "自动QC原因": "",
        "自动QC版本": "question-p0-v1",
        "导师下一步": "题目已通过自动预审，请在导师任务卡中完成豆包办公任务交互。",
    }


def test_question_precheck_routes_only_to_eligible_repair_or_blocked() -> None:
    assert {
        disposition.value for disposition in QuestionPrecheckDisposition
    } == {
        "eligible_for_interaction",
        "question_repair_required",
        "blocked",
    }
    repair = evaluate_question_precheck(
        complete_question(has_question_text=False, supporting_attachment_present=False),
        policy_version="question-p0-v1",
    )
    blocked = evaluate_question_precheck(
        complete_question(integrity_issue_codes=("question_integrity_mismatch",)),
        policy_version="question-p0-v1",
    )

    assert repair.disposition is QuestionPrecheckDisposition.REPAIR_REQUIRED
    assert repair.reason_codes == ("question_text_missing", "supporting_attachment_missing")
    assert blocked.disposition is QuestionPrecheckDisposition.BLOCKED
    assert blocked.reason_codes == ("question_integrity_mismatch",)


def test_overlapping_integrity_and_safety_reasons_stay_deduplicated() -> None:
    blocked = evaluate_question_precheck(
        complete_question(
            safety_ok=False,
            integrity_issue_codes=("safety_check_failed",),
        ),
        policy_version="question-p0-v1",
    )

    assert blocked.reason_codes == ("safety_check_failed",)


def test_six_turn_and_evidence_rules_do_not_belong_to_the_question_gate() -> None:
    question_fields = {field.name for field in fields(QuestionPrecheckEvidence)}

    assert {
        "tool_name",
        "turn_count",
        "has_dialogue_images",
        "has_trajectory_link",
        "has_log_id",
        "attested_by_expert",
    }.isdisjoint(question_fields)
    assert evaluate_question_precheck(
        complete_question(),
        policy_version="question-p0-v1",
    ).disposition is QuestionPrecheckDisposition.ELIGIBLE_FOR_INTERACTION


def test_interaction_gate_requires_question_eligibility_readback() -> None:
    require_eligible_question_state("eligible_for_interaction")

    with pytest.raises(PermissionError, match="eligible_for_interaction"):
        require_eligible_question_state("question_repair_required")
