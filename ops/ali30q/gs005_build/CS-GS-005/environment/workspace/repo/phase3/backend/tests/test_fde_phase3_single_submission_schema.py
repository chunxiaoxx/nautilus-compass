from services.fde_phase3_single_submission_schema import (
    CANONICAL_TABLE_NAMES,
    EXPERT_FORM_NAME,
    TASK_FORM_NAME,
    canonical_tables,
    expert_table,
    export_receipt_table,
    task_submission_table,
)


def test_canonical_schema_has_four_tables_and_two_public_forms():
    assert CANONICAL_TABLE_NAMES == (
        "第三期专家",
        "第三期任务与交互提交",
        "第三期审核与反馈",
        "第三期导出与回执",
    )
    assert tuple(table.name for table in canonical_tables()) == CANONICAL_TABLE_NAMES
    assert EXPERT_FORM_NAME == "第三期专家信息采集（正式）"
    assert TASK_FORM_NAME == "第三期任务与交互提交（正式）"
    assert tuple(table.form_name for table in canonical_tables() if table.form_name) == (
        EXPERT_FORM_NAME,
        TASK_FORM_NAME,
    )


def test_expert_form_keeps_the_buyer_required_profile_contract():
    assert expert_table().public_field_names == (
        "姓名",
        "豆包UID",
        "最高学历",
        "毕业院校",
        "专业",
        "学校层次",
        "工作领域",
        "工作年限",
        "行业证书认证（文字描述）",
        "每日作业时长",
    )


def test_standardized_profile_and_p0_fields_do_not_imply_buyer_acceptance():
    daily_hours = next(field for field in expert_table().fields if field.name == "每日作业时长")
    task_p0 = next(field for field in task_submission_table().fields if field.name == "自动P0状态")
    business_status = next(field for field in task_submission_table().fields if field.name == "业务状态")

    assert daily_hours.field_type == 3
    assert daily_hours.options == ("1小时以下", "1-2小时", "2-4小时", "4小时以上")
    assert "建议进入甲方队列" in task_p0.options
    assert "甲方已通过" in business_status.options


def test_task_form_combines_task_contract_and_interaction_evidence():
    assert task_submission_table().public_field_names == (
        "UID",
        "题目",
        "题目领域一级目录",
        "题目领域二级目录",
        "相关附件",
        "附件来源",
        "后续交互思路",
        "姓名",
        "豆包UID",
        "使用工具",
        "轮次数",
        "对话图片",
        "轨迹链接",
        "日志ID",
        "本人确认",
        "返修关联码",
    )
    assert "开始时间" not in task_submission_table().public_field_names
    assert "提交时间" not in task_submission_table().public_field_names
    assert "最终产物" not in task_submission_table().public_field_names


def test_task_revision_lineage_is_internal_self_link_not_form_question():
    table = task_submission_table()
    revision = next(field for field in table.fields if field.name == "revision_of")
    workflow_profile = next(field for field in table.fields if field.name == "工作流配置")
    repair_reference = next(field for field in table.fields if field.name == "返修关联码")
    repair_status = next(field for field in table.fields if field.name == "返修码状态")
    repair_expiry = next(field for field in table.fields if field.name == "返修码到期时间")

    assert revision.public is False
    assert revision.link_target == "self"
    assert "revision_of" not in table.public_field_names
    assert workflow_profile.public is False
    assert workflow_profile.options == ("phase3_interactive",)
    assert repair_reference.public is True
    assert repair_status.public is False
    assert repair_status.options == ("未发放", "可用", "已使用", "已过期")
    assert repair_expiry.public is False
    assert repair_expiry.field_type == 5


def test_public_forms_never_expose_lifecycle_review_or_export_fields():
    public_names = {
        field.name
        for table in canonical_tables()
        for field in table.fields
        if field.public
    }

    assert public_names.isdisjoint(
        {
            "业务状态",
            "自动P0状态",
            "自动QC置信度",
            "自动QC原因",
            "买方状态",
            "verdict",
            "revision_of",
            "导出状态",
            "compass_receipt_hash",
        }
    )


def test_export_receipt_keeps_signer_and_receipt_idempotency_metadata_internal():
    fields = {field.name: field for field in export_receipt_table().fields}

    assert fields["V5签名键ID"].public is False
    assert fields["Compass签名键ID"].public is False
    assert fields["回执幂等键"].public is False
