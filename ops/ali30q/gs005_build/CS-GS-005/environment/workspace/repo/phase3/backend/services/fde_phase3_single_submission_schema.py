"""Canonical schema for the high-volume Phase 3 Feishu workflow.

The external task contract and its interaction evidence share one source row.
All review, export, and lineage fields remain internal.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EXPERT_FORM_NAME = "第三期专家信息采集（正式）"
TASK_FORM_NAME = "第三期任务与交互提交（正式）"

EXPERT_EDUCATION_OPTIONS = ("本科", "硕士", "博士", "其他")
EXPERT_SCHOOL_TIER_OPTIONS = ("C9", "985", "211", "双一流", "其它院校", "海外院校")
EXPERT_WORK_YEARS_OPTIONS = ("0-2年", "3-5年", "6-10年", "10年以上")
EXPERT_DAILY_HOURS_OPTIONS = ("1小时以下", "1-2小时", "2-4小时", "4小时以上")

P0_FAILURE_CATEGORY_OPTIONS = (
    "未使用豆包办公任务",
    "不足6轮有效问答",
    "缺少对话图片",
    "缺少轨迹链接",
    "缺少日志ID",
    "未完成本人确认",
    "自动审核置信度不足",
    "质量问题",
    "完整性或合规风险",
)

PHASE3_WORKFLOW_PROFILE = "phase3_interactive"
REPAIR_REFERENCE_STATUS_OPTIONS = ("未发放", "可用", "已使用", "已过期")

PHASE3_PRIMARY_CATEGORY_OPTIONS = (
    "个人金融与理财投资",
    "商业与市场分析",
    "职业发展与教育规划",
    "企业经营与战略决策",
    "房地产与大宗资产",
    "科技与产品研发",
    "个人生活与重大决策",
    "互联网与平台业务",
    "科技软件与 AI 工作流",
    "游戏与互动内容",
    "品牌市场与电商零售",
    "投资战略、专业服务与企业经营",
    "金融服务与财富投研",
    "教育科研与生命科学",
    "法律、政务与公共服务",
)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    field_type: int
    public: bool = False
    options: tuple[str, ...] = ()
    link_target: str | None = None

    def feishu_field(self) -> dict[str, Any]:
        if self.link_target:
            raise ValueError(f"link field {self.name} requires a resolved target")
        field: dict[str, Any] = {"field_name": self.name, "type": self.field_type}
        if self.options:
            field["property"] = {"options": [{"name": option} for option in self.options]}
        return field


@dataclass(frozen=True)
class TableSpec:
    name: str
    fields: tuple[FieldSpec, ...]
    form_name: str | None = None

    @property
    def public_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.public)

    @property
    def initial_fields(self) -> tuple[FieldSpec, ...]:
        return tuple(field for field in self.fields if not field.link_target)


def expert_table() -> TableSpec:
    return TableSpec(
        name="第三期专家",
        form_name=EXPERT_FORM_NAME,
        fields=(
            FieldSpec("专家编号", 1),
            FieldSpec("姓名", 1, public=True),
            FieldSpec("豆包UID", 1, public=True),
            FieldSpec("最高学历", 3, public=True, options=EXPERT_EDUCATION_OPTIONS),
            FieldSpec("毕业院校", 1, public=True),
            FieldSpec("专业", 1, public=True),
            FieldSpec("学校层次", 3, public=True, options=EXPERT_SCHOOL_TIER_OPTIONS),
            FieldSpec("工作领域", 1, public=True),
            FieldSpec("工作年限", 3, public=True, options=EXPERT_WORK_YEARS_OPTIONS),
            FieldSpec("行业证书认证（文字描述）", 1, public=True),
            FieldSpec("每日作业时长", 3, public=True, options=EXPERT_DAILY_HOURS_OPTIONS),
            FieldSpec("专家状态", 3, options=("待培训", "活跃", "暂停", "停用")),
            FieldSpec("培训状态", 3, options=("未开始", "进行中", "已完成")),
            FieldSpec("豆包开通状态", 3, options=("待申请", "待开通", "已开通", "已停用")),
            FieldSpec("导师知识包版本", 1),
            FieldSpec("内部备注", 1),
        ),
    )


def task_submission_table() -> TableSpec:
    return TableSpec(
        name="第三期任务与交互提交",
        form_name=TASK_FORM_NAME,
        fields=(
            FieldSpec("提交编号", 1),
            FieldSpec("工作流配置", 3, options=(PHASE3_WORKFLOW_PROFILE,)),
            FieldSpec("UID", 1, public=True),
            FieldSpec("题目", 1, public=True),
            FieldSpec("题目领域一级目录", 3, public=True, options=PHASE3_PRIMARY_CATEGORY_OPTIONS),
            FieldSpec("题目领域二级目录", 1, public=True),
            FieldSpec("相关附件", 17, public=True),
            FieldSpec("附件来源", 1, public=True),
            FieldSpec("后续交互思路", 1, public=True),
            FieldSpec("姓名", 1, public=True),
            FieldSpec("豆包UID", 1, public=True),
            FieldSpec("使用工具", 3, public=True, options=("豆包办公任务",)),
            FieldSpec("轮次数", 2, public=True),
            FieldSpec("对话图片", 17, public=True),
            FieldSpec("轨迹链接", 1, public=True),
            FieldSpec("日志ID", 1, public=True),
            FieldSpec("本人确认", 7, public=True),
            FieldSpec("返修关联码", 1, public=True),
            FieldSpec("返修码状态", 3, options=REPAIR_REFERENCE_STATUS_OPTIONS),
            FieldSpec("返修码到期时间", 5),
            FieldSpec("开始时间", 5),
            FieldSpec("提交时间", 5),
            FieldSpec("最终产物", 17),
            FieldSpec("专家关联", 18, link_target="第三期专家"),
            FieldSpec("revision_of", 18, link_target="self"),
            FieldSpec("根提交编号", 1),
            FieldSpec(
                "业务状态",
                3,
                options=(
                    "已提交",
                    "自动质检中",
                    "待甲方反馈",
                    "需返修",
                    "甲方已通过",
                    "甲方已拒绝",
                    "已阻断",
                ),
            ),
            FieldSpec("自动P0状态", 3, options=("待运行", "建议进入甲方队列", "需返修", "阻断")),
            FieldSpec("自动QC置信度", 2),
            FieldSpec("自动QC原因", 1),
            FieldSpec("自动QC版本", 1),
            FieldSpec("导师下一步", 1),
            FieldSpec("买方映射状态", 3, options=("未路由", "待同步", "已同步", "反馈已回写")),
            FieldSpec("创建时间", 5),
        ),
    )


def review_feedback_table() -> TableSpec:
    return TableSpec(
        name="第三期审核与反馈",
        fields=(
            FieldSpec("审核编号", 1),
            FieldSpec("提交关联", 18, link_target="第三期任务与交互提交"),
            FieldSpec("审核来源", 3, options=("自动QC", "甲方反馈", "系统")),
            FieldSpec("P0状态", 3, options=("待运行", "建议进入甲方队列", "需返修", "阻断")),
            FieldSpec("P0失败类别", 4, options=P0_FAILURE_CATEGORY_OPTIONS),
            FieldSpec("QC策略版本", 1),
            FieldSpec("QC模型版本", 1),
            FieldSpec("QC置信度", 2),
            FieldSpec("反馈类别", 3, options=("无", "需补充", "需返修", "拒绝原因", "通过建议")),
            FieldSpec("反馈摘要（导师可用）", 1),
            FieldSpec("买方状态", 3, options=("待反馈", "已通过", "需返修", "已拒绝")),
            FieldSpec("verdict", 3, options=("待定", "Gold", "Repair", "Reject")),
            FieldSpec("证据摘要哈希", 1),
            FieldSpec("幂等键", 1),
            FieldSpec("处理时间", 5),
            FieldSpec("脱敏状态", 3, options=("待处理", "通过", "失败")),
        ),
    )


def export_receipt_table() -> TableSpec:
    return TableSpec(
        name="第三期导出与回执",
        fields=(
            FieldSpec("导出编号", 1),
            FieldSpec("提交关联", 18, link_target="第三期任务与交互提交"),
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


def canonical_tables() -> tuple[TableSpec, ...]:
    return (
        expert_table(),
        task_submission_table(),
        review_feedback_table(),
        export_receipt_table(),
    )


CANONICAL_TABLE_NAMES = tuple(table.name for table in canonical_tables())
