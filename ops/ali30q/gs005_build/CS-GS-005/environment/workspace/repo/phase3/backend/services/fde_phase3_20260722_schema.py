"""Verified Phase 3 (2026-07-22) public-form schema contract.

The contract contains only field names and enumerations read from the approved
buyer-schema copy. Internal lifecycle fields are deliberately separate from
each table's public form list.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


EXPERT_EDUCATION_OPTIONS = ("本科", "硕士", "博士", "其他")
EXPERT_SCHOOL_TIER_OPTIONS = ("C9", "985", "211", "双一流", "其它院校", "海外院校")
EXPERT_WORK_YEARS_OPTIONS = ("0-2年", "3-5年", "6-10年", "10年以上")

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

PUBLIC_FORM_NAMES = (
    "第三期专家信息采集",
    "第三期题目预审提交",
    "第三期交互成果补充",
)

TASK_PRESCREEN_PUBLIC_FIELDS = (
    "UID",
    "题目",
    "题目领域一级目录",
    "题目领域二级目录",
    "相关附件",
    "附件来源",
    "后续交互思路",
)

INTERACTION_RESULT_PUBLIC_FIELDS = (
    "UID",
    "姓名",
    "豆包UID",
    "对话图片",
    "轨迹链接",
    "日志ID",
)


@dataclass(frozen=True)
class FieldSpec:
    name: str
    field_type: int
    public: bool = False
    options: tuple[str, ...] = ()

    def feishu_field(self) -> dict[str, Any]:
        field: dict[str, Any] = {"field_name": self.name, "type": self.field_type}
        if self.options:
            field["property"] = {"options": [{"name": item} for item in self.options]}
        return field


@dataclass(frozen=True)
class TableSpec:
    name: str
    form_name: str
    fields: tuple[FieldSpec, ...]

    @property
    def public_field_names(self) -> tuple[str, ...]:
        return tuple(field.name for field in self.fields if field.public)

    def public_form_fields(self) -> tuple[FieldSpec, ...]:
        return tuple(field for field in self.fields if field.public)

    def feishu_fields(self) -> list[dict[str, Any]]:
        return [field.feishu_field() for field in self.fields]


def expert_info_table() -> TableSpec:
    return TableSpec(
        name="第三期专家信息",
        form_name=PUBLIC_FORM_NAMES[0],
        fields=(
            FieldSpec("姓名", 1, public=True),
            FieldSpec("豆包UID", 1, public=True),
            FieldSpec("最高学历", 3, public=True, options=EXPERT_EDUCATION_OPTIONS),
            FieldSpec("毕业院校", 1, public=True),
            FieldSpec("专业", 1, public=True),
            FieldSpec("学校层次", 3, public=True, options=EXPERT_SCHOOL_TIER_OPTIONS),
            FieldSpec("工作领域", 1, public=True),
            FieldSpec("工作年限", 3, public=True, options=EXPERT_WORK_YEARS_OPTIONS),
            FieldSpec("行业证书认证（文字描述）", 1, public=True),
            FieldSpec("每日作业时长", 1, public=True),
            FieldSpec("内部状态", 3, options=("待审核", "已通过", "已拒绝", "已停用")),
            FieldSpec("豆包开通状态", 3, options=("待申请", "待开通", "已开通", "已停用")),
            FieldSpec("内部备注", 1),
        ),
    )


def task_prescreen_table() -> TableSpec:
    return TableSpec(
        name="第三期题目预审",
        form_name=PUBLIC_FORM_NAMES[1],
        fields=(
            FieldSpec("UID", 1, public=True),
            FieldSpec("题目", 1, public=True),
            FieldSpec(
                "题目领域一级目录",
                3,
                public=True,
                options=PHASE3_PRIMARY_CATEGORY_OPTIONS,
            ),
            FieldSpec("题目领域二级目录", 1, public=True),
            FieldSpec("相关附件", 17, public=True),
            FieldSpec("附件来源", 1, public=True),
            FieldSpec("后续交互思路", 1, public=True),
            FieldSpec("预审状态", 3, options=("待审核", "需要修改", "已通过", "废弃")),
            FieldSpec("预审意见", 1),
            FieldSpec("来源任务记录", 1),
        ),
    )


def interaction_result_table() -> TableSpec:
    return TableSpec(
        name="第三期交互成果",
        form_name=PUBLIC_FORM_NAMES[2],
        fields=(
            FieldSpec("UID", 1, public=True),
            FieldSpec("姓名", 1, public=True),
            FieldSpec("豆包UID", 1, public=True),
            FieldSpec("对话图片", 17, public=True),
            FieldSpec("轨迹链接", 1, public=True),
            FieldSpec("日志ID", 1, public=True),
            FieldSpec("提交日期", 5),
            FieldSpec("交互质检状态", 3, options=("已提交", "需要修改")),
            FieldSpec("来源任务记录", 1),
            FieldSpec("来源交互尝试", 1),
        ),
    )


def public_form_tables() -> tuple[TableSpec, ...]:
    return (expert_info_table(), task_prescreen_table(), interaction_result_table())
