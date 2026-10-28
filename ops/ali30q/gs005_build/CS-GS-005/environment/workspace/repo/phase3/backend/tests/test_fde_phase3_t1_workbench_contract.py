from __future__ import annotations

import pytest

from services.fde_phase3_t1_workbench_contract import (
    CheckStatus,
    ExceptionCategory,
    ExpertVisibleState,
    ExpertWorkbenchProjection,
    GateEvidenceCheck,
    OperatorGate,
    OperatorGateSummary,
    load_t1_microguide_pack,
    public_interface_contract_payload,
    visible_feedback_from_reason_codes,
)


def _checks(gate: OperatorGate, status: CheckStatus) -> tuple[GateEvidenceCheck, ...]:
    codes = {
        OperatorGate.QUESTION_LOCK: (
            "identity_permission",
            "question_complete",
            "attachment_safe",
            "p0_passed",
            "p1_available",
            "no_open_exception",
        ),
        OperatorGate.BUYER_SUBMIT: (
            "question_locked",
            "minimum_rounds",
            "round_feedback_complete",
            "evidence_accessible",
            "evidence_consistent",
            "interaction_p0_passed",
            "interaction_p1_available",
            "identity_lineage_valid",
            "no_open_exception",
        ),
    }[gate]
    return tuple(GateEvidenceCheck(code, status, "已由权威表格读回") for code in codes)


def test_content_pack_matches_locked_interface_contract() -> None:
    pack = load_t1_microguide_pack()
    payload = public_interface_contract_payload()

    assert pack["contract_version"] == "platform-t1-interface-v1"
    assert len(ExpertVisibleState) == 13
    assert len(payload["states"]) == 13
    assert len(ExceptionCategory) == 7
    assert len(payload["exception_categories"]) == 7
    assert len(payload["p0_feedback_categories"]) == 7
    assert len(payload["p1_improvement_topics"]) == 9
    assert len(payload["error_microguides"]) == 13
    assert len(payload["content_hash"]) == 64


def test_expert_projection_contains_no_internal_identity_or_reason_code() -> None:
    feedback = visible_feedback_from_reason_codes(
        ("minimum_turns_not_met", "internal_unknown_code"),
        "请补齐后重新提交。",
    )
    payload = ExpertWorkbenchProjection(
        ExpertVisibleState.INTERACTION_REPAIR,
        "交互证据检查发现需要补充的内容。",
        "请补充后再提交",
        feedback,
    ).to_payload()
    rendered = str(payload)

    assert payload["primary_action"]["code"] == "repair_interaction"
    assert "minimum_turns_not_met" not in rendered
    assert "internal_unknown_code" not in rendered
    assert "record_id" not in rendered
    assert "expert_scope" not in rendered


def test_operator_release_is_enabled_only_when_every_check_is_green() -> None:
    green = OperatorGateSummary(
        OperatorGate.QUESTION_LOCK,
        _checks(OperatorGate.QUESTION_LOCK, CheckStatus.GREEN),
    ).to_operator_payload()
    blocked_checks = list(_checks(OperatorGate.BUYER_SUBMIT, CheckStatus.GREEN))
    blocked_checks[2] = GateEvidenceCheck(
        "round_feedback_complete",
        CheckStatus.RED,
        "第 4 轮评价缺失",
    )
    blocked = OperatorGateSummary(
        OperatorGate.BUYER_SUBMIT,
        tuple(blocked_checks),
    ).to_operator_payload()

    assert green["release_allowed"] is True
    assert green["allowed_decisions"] == ["release", "return", "escalate"]
    assert green["release_requires_bitable_readback"] is True
    assert blocked["release_allowed"] is False
    assert blocked["allowed_decisions"] == ["return", "escalate"]


def test_operator_gate_refuses_incomplete_or_extra_checklist() -> None:
    incomplete = _checks(OperatorGate.QUESTION_LOCK, CheckStatus.GREEN)[:-1]
    with pytest.raises(ValueError):
        OperatorGateSummary(OperatorGate.QUESTION_LOCK, incomplete)

    extra = incomplete + (
        GateEvidenceCheck("client_supplied_override", CheckStatus.GREEN, "x"),
    )
    with pytest.raises(ValueError):
        OperatorGateSummary(OperatorGate.QUESTION_LOCK, extra)
