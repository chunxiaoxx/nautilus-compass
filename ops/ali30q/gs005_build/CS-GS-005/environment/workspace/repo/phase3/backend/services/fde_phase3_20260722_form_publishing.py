"""Guarded native-Form publication for the verified Phase 3 intake tables.

This module changes Form-view presentation only. It never reads or writes
business records, buyer material, lifecycle state, or downstream exports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_20260722_schema import TableSpec, public_form_tables


PUBLIC_SHARE_LIMIT = "anyone_editable"


class FormPublishConfirmationError(ValueError):
    """Raised when a remote Form mutation lacks explicit confirmation."""


class FormSchemaDriftError(ValueError):
    """Raised when the native Form no longer matches the approved source table."""


class FormPublicationSafetyError(ValueError):
    """Raised before changing a Form that is already public but misconfigured."""


class FormClient(Protocol):
    def list_tables(self) -> list[dict[str, Any]]: ...

    def list_fields(self, table_id: str) -> list[dict[str, Any]]: ...

    def list_views(self, table_id: str) -> list[dict[str, Any]]: ...

    def get_form_metadata(self, table_id: str, form_id: str) -> dict[str, Any]: ...

    def list_form_fields(self, table_id: str, form_id: str) -> list[dict[str, Any]]: ...

    def patch_form_metadata(
        self, table_id: str, form_id: str, body: dict[str, Any]
    ) -> dict[str, Any]: ...

    def patch_form_field(
        self, table_id: str, form_id: str, field_id: str, body: dict[str, Any]
    ) -> dict[str, Any]: ...


@dataclass(frozen=True)
class FormFieldConfiguration:
    name: str
    title: str
    description: str
    required: bool
    visible: bool


@dataclass(frozen=True)
class PublicFormConfiguration:
    table_name: str
    form_name: str
    description: str
    fields: tuple[FormFieldConfiguration, ...]
    shared_limit: str = PUBLIC_SHARE_LIMIT
    submit_limit_once: bool = False


@dataclass(frozen=True)
class FormFieldPatch:
    table_id: str
    form_id: str
    field_id: str
    field_name: str
    body: dict[str, Any]


@dataclass(frozen=True)
class FormMetadataPatch:
    table_id: str
    form_id: str
    form_name: str
    body: dict[str, Any]


@dataclass(frozen=True)
class FormPublicationPlan:
    field_patches: tuple[FormFieldPatch, ...]
    metadata_patches: tuple[FormMetadataPatch, ...]


@dataclass(frozen=True)
class PublishedForm:
    form_name: str
    shared_url: str


@dataclass(frozen=True)
class FormPublicationReceipt:
    forms: tuple[PublishedForm, ...]


@dataclass(frozen=True)
class RetiredForm:
    form_name: str
    shared: bool


@dataclass(frozen=True)
class ObsoleteForm:
    table_name: str
    form_name: str


OBSOLETE_FORMS = (
    ObsoleteForm("外部题目提交", "第三期题目与交互成果提交"),
    ObsoleteForm("专家申请", "第三期专家申请与豆包开通"),
)


def _field_configurations(
    table: TableSpec,
    descriptions: dict[str, str],
    required_names: set[str],
) -> tuple[FormFieldConfiguration, ...]:
    return tuple(
        FormFieldConfiguration(
            name=field.name,
            title=field.name,
            description=descriptions.get(field.name, ""),
            required=field.name in required_names,
            visible=field.public,
        )
        for field in table.fields
    )


def public_form_configurations() -> tuple[PublicFormConfiguration, ...]:
    """Return the approved Form UX without exposing internal lifecycle fields."""

    expert, prescreen, result = public_form_tables()
    return (
        PublicFormConfiguration(
            table_name=expert.name,
            form_name=expert.form_name,
            description=(
                "请如实填写，用于资格审核与豆包办公任务开通。"
                "请勿填写密码、验证码、身份证号或银行卡信息。"
            ),
            fields=_field_configurations(
                expert,
                {
                    "姓名": "请填写与豆包账号对应的姓名。",
                    "豆包UID": "填写豆包 UID，不填写手机号、密码或验证码。",
                    "最高学历": "请选择已获得的最高学历。",
                    "毕业院校": "填写毕业院校全称。",
                    "专业": "填写主要专业或研究方向。",
                    "学校层次": "请选择最符合的学校层次。",
                    "工作领域": "填写当前或最近两年的主要工作领域。",
                    "工作年限": "请选择累计相关工作年限。",
                    "行业证书认证（文字描述）": "如无相关证书，请填写“无”。",
                    "每日作业时长": "填写稳定可投入的每日时长，例如“2-3 小时”。",
                },
                set(expert.public_field_names),
            ),
        ),
        PublicFormConfiguration(
            table_name=prescreen.name,
            form_name=prescreen.form_name,
            description=(
                "仅提交计划在豆包办公任务模式完成的高难度工作任务。"
                "预审通过后，初始题目不得改写；请勿上传未脱敏的个人或保密材料。"
            ),
            fields=_field_configurations(
                prescreen,
                {
                    "UID": "格式建议：实名_日期_序号；后续交互成果须使用同一 UID。",
                    "题目": "写清背景、目标、约束和交付物，作为首轮原始提问。",
                    "题目领域一级目录": "请选择最匹配的一项一级目录。",
                    "题目领域二级目录": "填写更具体的业务或专业方向。",
                    "相关附件": "可上传首轮需要使用的已脱敏材料；无附件可留空。",
                    "附件来源": "有附件时填写每份附件的来源或可核验说明；无附件可留空。",
                    "后续交互思路": "说明如何通过多轮追问推进任务，并体现专业工作量。",
                },
                {
                    "UID",
                    "题目",
                    "题目领域一级目录",
                    "题目领域二级目录",
                    "后续交互思路",
                },
            ),
        ),
        PublicFormConfiguration(
            table_name=result.name,
            form_name=result.form_name,
            description=(
                "仅用于已通过预审的同一 UID。请提交完整交互证据；"
                "请勿上传密码、验证码或未脱敏个人信息。"
            ),
            fields=_field_configurations(
                result,
                {
                    "UID": "填写预审通过时使用的同一 UID。",
                    "姓名": "填写与专家信息表一致的姓名。",
                    "豆包UID": "填写完成本次豆包办公任务的 UID。",
                    "对话图片": "上传覆盖完整交互过程的对话截图。",
                    "轨迹链接": "填写本次完整对话的可访问轨迹链接。",
                    "日志ID": "填写豆包办公任务生成的日志 ID。",
                },
                set(result.public_field_names),
            ),
        ),
    )


class FormPublisher:
    """Publishes approved Forms only after their field visibility is verified."""

    def __init__(self, client: FormClient) -> None:
        self._client = client

    @staticmethod
    def _table_lookup(tables: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(table["name"]): table for table in tables}

    @staticmethod
    def _view_id(views: list[dict[str, Any]], form_name: str) -> str:
        matches = [view for view in views if view.get("view_name") == form_name]
        if len(matches) != 1 or matches[0].get("view_type") != "form":
            raise FormSchemaDriftError(f"native Form view missing or ambiguous: {form_name}")
        return str(matches[0]["view_id"])

    @staticmethod
    def _field_lookup(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(field["field_name"]): field for field in fields}

    @staticmethod
    def _form_field_lookup(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        return {str(field["field_id"]): field for field in fields}

    @staticmethod
    def _field_body(config: FormFieldConfiguration) -> dict[str, Any]:
        if not config.visible:
            return {"visible": False}
        return {
            "title": config.title,
            "description": config.description,
            "required": config.required,
            "visible": True,
        }

    def _resolve_form(
        self,
        config: PublicFormConfiguration,
        table_lookup: dict[str, dict[str, Any]],
    ) -> tuple[str, str, dict[str, dict[str, Any]], dict[str, dict[str, Any]], dict[str, Any]]:
        table = table_lookup.get(config.table_name)
        if table is None:
            raise FormSchemaDriftError(f"source table missing: {config.table_name}")
        table_id = str(table["table_id"])
        form_id = self._view_id(self._client.list_views(table_id), config.form_name)
        table_fields = self._field_lookup(self._client.list_fields(table_id))
        configured_names = tuple(field.name for field in config.fields)
        if set(table_fields) != set(configured_names):
            raise FormSchemaDriftError(f"table field contract differs: {config.table_name}")
        form_fields = self._form_field_lookup(self._client.list_form_fields(table_id, form_id))
        missing_form_fields = [
            name for name, field in table_fields.items() if str(field["field_id"]) not in form_fields
        ]
        if missing_form_fields:
            raise FormSchemaDriftError(f"Form questions missing: {config.form_name}")
        metadata = self._client.get_form_metadata(table_id, form_id)
        return table_id, form_id, table_fields, form_fields, metadata

    def plan(self) -> FormPublicationPlan:
        tables = self._table_lookup(self._client.list_tables())
        field_patches: list[FormFieldPatch] = []
        metadata_patches: list[FormMetadataPatch] = []

        for config in public_form_configurations():
            table_id, form_id, table_fields, form_fields, metadata = self._resolve_form(config, tables)
            form_needs_field_updates = False
            for field_config in config.fields:
                field_id = str(table_fields[field_config.name]["field_id"])
                current = form_fields[field_id]
                desired = self._field_body(field_config)
                if any(current.get(key) != value for key, value in desired.items()):
                    form_needs_field_updates = True
                    field_patches.append(
                        FormFieldPatch(
                            table_id=table_id,
                            form_id=form_id,
                            field_id=field_id,
                            field_name=field_config.name,
                            body=desired,
                        )
                    )
            if metadata.get("shared") and form_needs_field_updates:
                raise FormPublicationSafetyError(
                    f"public Form requires field changes before publication: {config.form_name}"
                )

            desired_metadata = {
                "description": config.description,
                "shared": True,
                "shared_limit": config.shared_limit,
                "submit_limit_once": config.submit_limit_once,
            }
            if any(metadata.get(key) != value for key, value in desired_metadata.items()):
                metadata_patches.append(
                    FormMetadataPatch(
                        table_id=table_id,
                        form_id=form_id,
                        form_name=config.form_name,
                        body=desired_metadata,
                    )
                )
        return FormPublicationPlan(tuple(field_patches), tuple(metadata_patches))

    def _assert_field_contracts(self, tables: dict[str, dict[str, Any]]) -> None:
        for config in public_form_configurations():
            table_id, form_id, table_fields, form_fields, _ = self._resolve_form(config, tables)
            del table_id, form_id
            for field_config in config.fields:
                field_id = str(table_fields[field_config.name]["field_id"])
                current = form_fields[field_id]
                desired = self._field_body(field_config)
                if any(current.get(key) != value for key, value in desired.items()):
                    raise FormSchemaDriftError(
                        f"Form field read-back differs: {config.form_name}/{field_config.name}"
                    )

    def _published_forms(self, tables: dict[str, dict[str, Any]]) -> tuple[PublishedForm, ...]:
        published: list[PublishedForm] = []
        for config in public_form_configurations():
            table_id, form_id, _, _, metadata = self._resolve_form(config, tables)
            del table_id, form_id
            if (
                metadata.get("shared") is not True
                or metadata.get("shared_limit") != config.shared_limit
                or metadata.get("submit_limit_once") != config.submit_limit_once
                or not isinstance(metadata.get("shared_url"), str)
                or not metadata["shared_url"]
            ):
                raise FormSchemaDriftError(f"Form publication read-back differs: {config.form_name}")
            published.append(PublishedForm(config.form_name, metadata["shared_url"]))
        return tuple(published)

    def publish(self, *, confirmed: bool) -> FormPublicationReceipt:
        if not confirmed:
            raise FormPublishConfirmationError("public Form publication requires explicit confirmation")

        plan = self.plan()
        for patch in plan.field_patches:
            self._client.patch_form_field(
                patch.table_id, patch.form_id, patch.field_id, patch.body
            )

        tables = self._table_lookup(self._client.list_tables())
        self._assert_field_contracts(tables)

        for patch in plan.metadata_patches:
            self._client.patch_form_metadata(patch.table_id, patch.form_id, patch.body)

        return FormPublicationReceipt(forms=self._published_forms(tables))

    def retire_obsolete_forms(self, *, confirmed: bool) -> tuple[RetiredForm, ...]:
        if not confirmed:
            raise FormPublishConfirmationError("Form retirement requires explicit confirmation")

        tables = self._table_lookup(self._client.list_tables())
        self._assert_field_contracts(tables)
        self._published_forms(tables)

        retired: list[RetiredForm] = []
        for obsolete in OBSOLETE_FORMS:
            table = tables.get(obsolete.table_name)
            if table is None:
                raise FormSchemaDriftError(f"obsolete source table missing: {obsolete.table_name}")
            table_id = str(table["table_id"])
            form_id = self._view_id(self._client.list_views(table_id), obsolete.form_name)
            metadata = self._client.get_form_metadata(table_id, form_id)
            if metadata.get("shared"):
                self._client.patch_form_metadata(
                    table_id,
                    form_id,
                    {"shared": False},
                )
            verified = self._client.get_form_metadata(table_id, form_id)
            if verified.get("shared") is not False:
                raise FormSchemaDriftError(f"obsolete Form remains public: {obsolete.form_name}")
            retired.append(RetiredForm(obsolete.form_name, shared=False))
        return tuple(retired)
