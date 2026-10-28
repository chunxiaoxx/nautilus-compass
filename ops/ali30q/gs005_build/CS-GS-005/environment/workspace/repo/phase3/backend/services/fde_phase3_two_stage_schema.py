"""Canonical schema for the Phase 3 Mentor-gated two-stage workflow.

Only the expert profile has a native public Form. Question and interaction
evidence are submitted from authenticated Mentor continuations, so identity,
lineage, review and state fields never become client-controlled inputs.
"""

from __future__ import annotations

from dataclasses import dataclass

from services.fde_phase3_single_submission_schema import (
    EXPERT_DAILY_HOURS_OPTIONS,
    EXPERT_EDUCATION_OPTIONS,
    EXPERT_FORM_NAME,
    EXPERT_SCHOOL_TIER_OPTIONS,
    EXPERT_WORK_YEARS_OPTIONS,
    P0_FAILURE_CATEGORY_OPTIONS,
    PHASE3_PRIMARY_CATEGORY_OPTIONS,
    PHASE3_WORKFLOW_PROFILE,
    FieldSpec,
)


QUESTION_FORM_NAME = "第三期题目预审（正式）"

QUESTION_STATES = (
    "precheck_pending",
    "precheck_running",
    "awaiting_operator_lock",
    "eligible_for_interaction",
    "question_repair_required",
    "exception_open",
    "terminated",
    "blocked",
)
INTERACTION_STATES = (
    "interaction_draft",
    "interaction_qc_running",
    "awaiting_operator_submit",
    "buyer_ready",
    "buyer_review",
    "repair_required",
    "exception_open",
    "terminated",
    "blocked",
    "buyer_accepted",
    "buyer_rejected",
)
QUESTION_MENTOR_SUBMISSION_FIELDS = (
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
INTERACTION_MENTOR_SUBMISSION_FIELDS = (
    "使用工具",
    "轮次数",
    "逐轮评价JSON",
    "对话图片",
    "轨迹链接",
    "日志ID",
    "本人确认",
)


@dataclass(frozen=True)
class TwoStageTableSpec:
    """Immutable table and ingress contract for the two-stage workflow."""

    name: str
    fields: tuple[FieldSpec, ...]
    form_name: str | None = None
    mentor_submission_field_names: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        names = tuple(field.name for field in self.fields)
        if len(set(names)) != len(names):
            raise ValueError(f"{self.name} contains duplicate field names")
        if self.form_name is None and any(field.public for field in self.fields):
            raise ValueError("only a native Form table may expose public fields")
        unknown_mentor_fields = set(self.mentor_submission_field_names) - set(names)
        if unknown_mentor_fields:
            raise ValueError("Mentor submission fields must belong to the table")

    @property
    def public_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.public)

    @property
    def initial_fields(self) -> tuple[FieldSpec, ...]:
        return tuple(field for field in self.fields if not field.link_target)


def expert_table() -> TwoStageTableSpec:
    """Identity-first registration is mediated by Mentor, never a public Base Form."""

    return TwoStageTableSpec(
        name="第三期专家",
        fields=(
            FieldSpec("专家编号", 1),
            FieldSpec("姓名", 1),
            FieldSpec("豆包UID", 1),
            FieldSpec("联系方式", 1),
            FieldSpec("最高学历", 3, options=EXPERT_EDUCATION_OPTIONS),
            FieldSpec("毕业院校", 1),
            FieldSpec("专业", 1),
            FieldSpec("学校层次", 3, options=EXPERT_SCHOOL_TIER_OPTIONS),
            FieldSpec("工作领域", 1),
            FieldSpec("工作年限", 3, options=EXPERT_WORK_YEARS_OPTIONS),
            FieldSpec("行业证书认证（文字描述）", 1),
            FieldSpec("每日作业时长", 3, options=EXPERT_DAILY_HOURS_OPTIONS),
            FieldSpec("真实性与隐私承诺", 7),
            FieldSpec("飞书open_id", 1),
            FieldSpec("飞书union_id", 1),
            FieldSpec(
                "身份绑定状态",
                3,
                options=("待绑定", "已绑定", "绑定冲突", "已解除"),
            ),
            FieldSpec("身份绑定时间", 5),
            FieldSpec("身份绑定版本", 1),
            FieldSpec(
                "准入状态",
                3,
                options=("待审核", "需补充", "已通过", "未通过"),
            ),
            FieldSpec("Agent准入检查摘要", 1),
            FieldSpec("Agent准入建议", 3, options=("建议通过", "建议退回", "建议升级")),
            FieldSpec("运营准入决定", 3, options=("待确认", "通过", "退回补充", "异常升级")),
            FieldSpec("运营准入人open_id", 1),
            FieldSpec("运营准入时间", 5),
            FieldSpec("准入处理说明", 1),
            FieldSpec("专家状态", 3, options=("待培训", "活跃", "暂停", "停用")),
            FieldSpec("培训状态", 3, options=("未开始", "进行中", "已完成")),
            FieldSpec("豆包开通状态", 3, options=("待申请", "待开通", "已开通", "已停用")),
            FieldSpec("导师知识包版本", 1),
            FieldSpec("内部备注", 1),
        ),
    )


def question_precheck_table() -> TwoStageTableSpec:
    """Question content is accepted only from an authenticated Mentor session."""

    return TwoStageTableSpec(
        name="第三期题目预审",
        mentor_submission_field_names=QUESTION_MENTOR_SUBMISSION_FIELDS,
        fields=(
            FieldSpec("题目编号", 1),
            FieldSpec("工作流配置", 3, options=(PHASE3_WORKFLOW_PROFILE,)),
            FieldSpec("题目", 1),
            FieldSpec("题目领域一级目录", 3, options=PHASE3_PRIMARY_CATEGORY_OPTIONS),
            FieldSpec("题目领域二级目录", 1),
            FieldSpec("真实工作场景", 1),
            FieldSpec("期望交付结果", 1),
            FieldSpec("相关附件", 17),
            FieldSpec("附件来源", 1),
            FieldSpec("附件脱敏确认", 7),
            FieldSpec("后续交互思路", 1),
            FieldSpec("本人确认", 7),
            FieldSpec("专家关联", 18, link_target="第三期专家"),
            FieldSpec("revision_of", 18, link_target="self"),
            FieldSpec("根题目编号", 1),
            FieldSpec("题目状态", 3, options=QUESTION_STATES),
            FieldSpec("自动P0状态", 3, options=("待运行", "可开始交互", "需返修", "阻断")),
            FieldSpec("自动QC置信度", 2),
            FieldSpec("自动QC原因", 1),
            FieldSpec("自动QC版本", 1),
            FieldSpec("自动P1建议", 1),
            FieldSpec("Agent检查摘要", 1),
            FieldSpec("题面哈希", 1),
            FieldSpec("锁题清单JSON", 1),
            FieldSpec(
                "运营锁题决定",
                3,
                options=("待确认", "锁题并开放交互", "退回补充", "异常升级"),
            ),
            FieldSpec("运营锁题人open_id", 1),
            FieldSpec("锁题时间", 5),
            FieldSpec("导师下一步", 1),
            FieldSpec("交互入口状态", 3, options=("未发放", "可用", "已使用", "已过期")),
            FieldSpec("交互入口到期时间", 5),
            FieldSpec("异常状态", 3, options=("无", "处理中", "已解决")),
            FieldSpec("异常类别", 1),
            FieldSpec("记录版本", 2),
            FieldSpec("最后读回时间", 5),
            FieldSpec("创建时间", 5),
        ),
    )


def interaction_result_table() -> TwoStageTableSpec:
    """Interaction evidence is Mentor-scoped, never a broadly shared Form."""

    return TwoStageTableSpec(
        name="第三期交互成果",
        mentor_submission_field_names=INTERACTION_MENTOR_SUBMISSION_FIELDS,
        fields=(
            FieldSpec("交互编号", 1),
            FieldSpec("工作流配置", 3, options=(PHASE3_WORKFLOW_PROFILE,)),
            FieldSpec("使用工具", 3, options=("豆包办公任务",)),
            FieldSpec("轮次数", 2),
            FieldSpec("逐轮评价JSON", 1),
            FieldSpec("逐轮评价摘要", 1),
            FieldSpec("对话图片", 17),
            FieldSpec("轨迹链接", 1),
            FieldSpec("日志ID", 1),
            FieldSpec("本人确认", 7),
            FieldSpec("题目关联", 18, link_target="第三期题目预审"),
            FieldSpec("专家关联", 18, link_target="第三期专家"),
            FieldSpec("revision_of", 18, link_target="self"),
            FieldSpec("根交互编号", 1),
            FieldSpec("交互状态", 3, options=INTERACTION_STATES),
            FieldSpec("自动P0状态", 3, options=("待运行", "建议进入甲方队列", "需返修", "阻断")),
            FieldSpec("自动QC置信度", 2),
            FieldSpec("自动QC原因", 1),
            FieldSpec("自动QC版本", 1),
            FieldSpec("自动P1建议", 1),
            FieldSpec("Agent检查摘要", 1),
            FieldSpec("提交甲方清单JSON", 1),
            FieldSpec(
                "运营送审决定",
                3,
                options=("待确认", "提交甲方", "退回补充", "异常升级"),
            ),
            FieldSpec("运营送审人open_id", 1),
            FieldSpec("送审时间", 5),
            FieldSpec("导师下一步", 1),
            FieldSpec("买方映射状态", 3, options=("未路由", "待同步", "已同步", "反馈已回写")),
            FieldSpec("异常状态", 3, options=("无", "处理中", "已解决")),
            FieldSpec("异常类别", 1),
            FieldSpec("记录版本", 2),
            FieldSpec("最后读回时间", 5),
            FieldSpec("创建时间", 5),
        ),
    )


def review_feedback_table() -> TwoStageTableSpec:
    return TwoStageTableSpec(
        name="第三期审核与反馈",
        fields=(
            FieldSpec("审核编号", 1),
            FieldSpec("题目关联", 18, link_target="第三期题目预审"),
            FieldSpec("交互关联", 18, link_target="第三期交互成果"),
            FieldSpec("审核来源", 3, options=("题目自动QC", "交互自动QC", "甲方反馈", "系统")),
            FieldSpec("P0状态", 3, options=("待运行", "可开始交互", "建议进入甲方队列", "需返修", "阻断")),
            FieldSpec("P0失败类别", 4, options=P0_FAILURE_CATEGORY_OPTIONS),
            FieldSpec("P0检查JSON", 1),
            FieldSpec("P1建议JSON", 1),
            FieldSpec("证据引用JSON", 1),
            FieldSpec("QC策略版本", 1),
            FieldSpec("QC模型版本", 1),
            FieldSpec("QC置信度", 2),
            FieldSpec("反馈类别", 3, options=("无", "需补充", "需返修", "拒绝原因", "通过建议")),
            FieldSpec("反馈摘要（导师可用）", 1),
            FieldSpec(
                "专家可见结论",
                3,
                options=("可以进入下一步", "请补充后再提交", "已转项目支持"),
            ),
            FieldSpec(
                "运营决定",
                3,
                options=("待确认", "发布确认", "退回补充", "异常升级"),
            ),
            FieldSpec("运营人open_id", 1),
            FieldSpec("运营决定时间", 5),
            FieldSpec("买方状态", 3, options=("待反馈", "已通过", "需返修", "已拒绝")),
            FieldSpec("verdict", 3, options=("待定", "Gold", "Repair", "Reject")),
            FieldSpec("证据摘要哈希", 1),
            FieldSpec("幂等键", 1),
            FieldSpec("处理时间", 5),
            FieldSpec("脱敏状态", 3, options=("待处理", "通过", "失败")),
        ),
    )


def export_receipt_table() -> TwoStageTableSpec:
    return TwoStageTableSpec(
        name="第三期导出与回执",
        fields=(
            FieldSpec("导出编号", 1),
            FieldSpec("题目关联", 18, link_target="第三期题目预审"),
            FieldSpec("交互关联", 18, link_target="第三期交互成果"),
            FieldSpec("审核关联", 18, link_target="第三期审核与反馈"),
            FieldSpec("导出状态", 3, options=("不符合", "待导出", "已验证", "已阻断", "已回执")),
            FieldSpec("资格或阻断原因", 1),
            FieldSpec("opaque_task_id", 1),
            FieldSpec("event_id", 1),
            FieldSpec("payload_hash", 1),
            FieldSpec("manifest_hash", 1),
            FieldSpec("V5签名键ID", 1),
            FieldSpec("compass_receipt_hash", 1),
            FieldSpec("Compass签名键ID", 1),
            FieldSpec("回执幂等键", 1),
            FieldSpec("导出时间", 5),
            FieldSpec("回执时间", 5),
            FieldSpec("脱敏状态", 3, options=("待处理", "通过", "失败")),
        ),
    )


def canonical_tables() -> tuple[TwoStageTableSpec, ...]:
    return (
        expert_table(),
        question_precheck_table(),
        interaction_result_table(),
        review_feedback_table(),
        export_receipt_table(),
    )


CANONICAL_TABLE_NAMES = tuple(table.name for table in canonical_tables())
