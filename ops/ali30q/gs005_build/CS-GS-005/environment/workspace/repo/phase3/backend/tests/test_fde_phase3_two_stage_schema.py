from __future__ import annotations

import pytest

from services.fde_phase3_feishu_runtime_contract import (
    AppRole,
    BitableEventEnvelope,
    CanonicalTable,
    EligibleQuestionReadback,
    RuntimeRoute,
    authorize_question_interaction_link,
)
from services.fde_phase3_two_stage_schema import (
    INTERACTION_MENTOR_SUBMISSION_FIELDS,
    canonical_tables,
)


def _event() -> BitableEventEnvelope:
    return BitableEventEnvelope(
        route=RuntimeRoute.INTERACTION_SUBMITTED,
        record_id="rec_interaction_001",
        record_version=1,
        source_event_id="evt_interaction_001",
    )


def test_two_stage_schema_has_five_related_canonical_tables() -> None:
    tables = {table.name: table for table in canonical_tables()}

    assert tuple(tables) == (
        "第三期专家",
        "第三期题目预审",
        "第三期交互成果",
        "第三期审核与反馈",
        "第三期导出与回执",
    )
    question = tables["第三期题目预审"]
    interaction = tables["第三期交互成果"]
    expert = tables["第三期专家"]
    review = tables["第三期审核与反馈"]
    export = tables["第三期导出与回执"]

    assert question.form_name is None
    assert question.public_field_names == ()
    assert set(question.mentor_submission_field_names) == {
        "题目",
        "题目领域一级目录",
        "题目领域二级目录",
        "真实工作场景",
        "期望交付结果",
        "相关附件",
        "附件来源",
        "附件脱敏确认",
        "后续交互思路",
        "本人确认",
    }
    assert question.mentor_submission_field_names == (
        "题目",
        "题目领域一级目录",
        "题目领域二级目录",
        "真实工作场景",
        "期望交付结果",
        "相关附件",
        "附件来源",
        "附件脱敏确认",
        "后续交互思路",
        "本人确认",
    )
    assert interaction.form_name is None
    assert interaction.public_field_names == ()
    assert interaction.mentor_submission_field_names == INTERACTION_MENTOR_SUBMISSION_FIELDS
    assert expert.form_name is None
    assert expert.public_field_names == ()

    question_fields = {field.name: field for field in question.fields}
    interaction_fields = {field.name: field for field in interaction.fields}
    expert_fields = {field.name: field for field in tables["第三期专家"].fields}
    review_fields = {field.name: field for field in review.fields}
    export_fields = {field.name: field for field in export.fields}
    assert question_fields["专家关联"].link_target == "第三期专家"
    assert interaction_fields["题目关联"].link_target == "第三期题目预审"
    assert interaction_fields["专家关联"].link_target == "第三期专家"
    assert review_fields["题目关联"].link_target == "第三期题目预审"
    assert review_fields["交互关联"].link_target == "第三期交互成果"
    assert export_fields["题目关联"].link_target == "第三期题目预审"
    assert export_fields["交互关联"].link_target == "第三期交互成果"
    assert {"飞书open_id", "身份绑定状态", "身份绑定时间"}.issubset(expert_fields)
    assert expert_fields["飞书open_id"].public is False
    assert {
        "Agent准入检查摘要",
        "Agent准入建议",
        "运营准入决定",
        "运营准入人open_id",
        "运营准入时间",
        "准入处理说明",
    }.issubset(expert_fields)
    assert expert_fields["Agent准入建议"].options == ("建议通过", "建议退回", "建议升级")
    assert expert_fields["运营准入决定"].options == ("待确认", "通过", "退回补充", "异常升级")
    assert {
        "题面哈希",
        "锁题清单JSON",
        "运营锁题决定",
        "运营锁题人open_id",
        "锁题时间",
    }.issubset(question_fields)
    assert {
        "逐轮评价JSON",
        "提交甲方清单JSON",
        "运营送审决定",
        "运营送审人open_id",
        "送审时间",
    }.issubset(interaction_fields)
    assert {
        "P0检查JSON",
        "P1建议JSON",
        "专家可见结论",
        "运营决定",
    }.issubset(review_fields)


def test_identity_and_lineage_are_server_controlled_after_admission() -> None:
    tables = {table.name: table for table in canonical_tables()}
    question = tables["第三期题目预审"]
    interaction = tables["第三期交互成果"]

    forbidden = {
        "UID",
        "豆包UID",
        "姓名",
        "专家关联",
        "题目关联",
        "revision_of",
        "题目状态",
        "交互状态",
        "自动P0状态",
        "运营锁题决定",
        "运营送审决定",
    }
    assert forbidden.isdisjoint(question.mentor_submission_field_names)
    assert forbidden.isdisjoint(interaction.mentor_submission_field_names)
    assert "逐轮评价JSON" in interaction.mentor_submission_field_names


def test_public_contract_never_exposes_internal_lineage_or_downstream_fields() -> None:
    tables = canonical_tables()
    exposed = {
        field_name
        for table in tables
        for field_name in table.public_field_names
    }

    assert {
        "record_id",
        "专家关联",
        "题目关联",
        "revision_of",
        "交互续办句柄",
        "原始买方反馈",
        "verdict",
        "opaque_task_id",
        "event_id",
        "payload_hash",
        "manifest_hash",
        "compass_receipt_hash",
    }.isdisjoint(exposed)


def test_only_nautilus_can_create_question_interaction_relation_from_eligible_readback() -> None:
    eligible_question = EligibleQuestionReadback(
        question_record_id="rec_question_001",
        expert_record_id="rec_expert_001",
        question_state="eligible_for_interaction",
    )

    with pytest.raises(PermissionError, match="Nautilus"):
        authorize_question_interaction_link(
            actor=AppRole.MENTOR,
            envelope=_event(),
            eligible_question=eligible_question,
        )

    mutation = authorize_question_interaction_link(
        actor=AppRole.NAUTILUS,
        envelope=_event(),
        eligible_question=eligible_question,
    )

    assert mutation.target_table is CanonicalTable.INTERACTION_RESULT
    assert mutation.target_record_id == "rec_interaction_001"
    assert mutation.updates["题目关联"] == ["rec_question_001"]
    assert mutation.updates["专家关联"] == ["rec_expert_001"]
    assert mutation.updates["交互状态"] == "interaction_qc_running"
    assert mutation.updates["自动P0状态"] == "待运行"


def test_question_interaction_relation_rejects_noneligible_question() -> None:
    with pytest.raises(ValueError, match="eligible_for_interaction"):
        EligibleQuestionReadback(
            question_record_id="rec_question_001",
            expert_record_id="rec_expert_001",
            question_state="precheck_pending",
        )
