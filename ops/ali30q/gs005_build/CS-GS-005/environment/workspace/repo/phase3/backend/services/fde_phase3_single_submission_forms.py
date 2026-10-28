"""Native Form contracts for the canonical Phase 3 Bitable tables.

The module updates Form-question presentation only.  It does not inspect or
change Bitable business rows, buyer material, lifecycle decisions, or exports.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from services.fde_phase3_single_submission_schema import TableSpec, canonical_tables


PUBLIC_SHARE_LIMIT = "anyone_editable"


class FormPublishConfirmationError(ValueError):
    """Raised when Form presentation is mutated without explicit confirmation."""


class FormSchemaDriftError(ValueError):
    """Raised when a native Form no longer matches its table contract."""


class FormPublicationSafetyError(ValueError):
    """Raised before changing fields on a Form that is already public."""


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
class PausedForm:
    form_name: str
    was_shared: bool


@dataclass(frozen=True)
class FormPublicationReceipt:
    forms: tuple[PublishedForm, ...]


@dataclass(frozen=True)
class ExpertFormProbe:
    """Sanitized publication state for the expert-information Form only."""

    form_name: str
    shared: bool
    shared_limit: str | None
    submit_limit_once: bool | None
    question_count: int
    visible_question_count: int


@dataclass(frozen=True)
class LegacyForm:
    table_name: str
    form_name: str


@dataclass(frozen=True)
class RetiredForm:
    form_name: str
    shared: bool


LEGACY_PUBLIC_FORMS = (
    LegacyForm("第三期专家信息", "第三期专家信息采集"),
    LegacyForm("第三期题目预审", "第三期题目预审提交"),
    LegacyForm("第三期交互成果", "第三期交互成果补充"),
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
            required=field.public and field.name in required_names,
            visible=field.public,
        )
        for field in table.fields
    )


def public_form_configurations() -> tuple[PublicFormConfiguration, ...]:
    """Return the only two external Form contracts approved for Phase 3."""
    expert, task, _, _ = canonical_tables()
    return (
        PublicFormConfiguration(
            table_name=expert.name,
            form_name=str(expert.form_name),
            description=(
                "请如实填写，用于专家报名初筛、豆包办公任务开通和导师培训匹配。"
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
                    "工作领域": "填写当前或最近两年的主要工作领域，不限制具体行业。",
                    "工作年限": "请选择累计相关工作年限。",
                    "行业证书认证（文字描述）": "如无相关证书，请填写“无”。",
                    "每日作业时长": "请选择稳定可投入的每日时长。",
                },
                set(expert.public_field_names),
            ),
        ),
        PublicFormConfiguration(
            table_name=task.name,
            form_name=str(task.form_name),
            description=(
                "请在豆包办公任务中围绕同一题目完成至少 6 轮有效问答后，一次提交题目和交互成果。"
                "请提供对话图片、轨迹链接和日志 ID；请勿上传密码、验证码或未脱敏的个人和保密材料。"
            ),
            fields=_field_configurations(
                task,
                {
                    "UID": "为本次任务填写稳定 UID；返修时保留该 UID。",
                    "题目": "写清背景、目标、约束和期望交付，作为豆包办公任务的首轮问题。",
                    "题目领域一级目录": "选择最接近的一级目录；本期不限制具体行业。",
                    "题目领域二级目录": "填写更具体的业务或专业方向。",
                    "相关附件": "可上传已脱敏的任务材料或补充产物；无附件可留空。",
                    "附件来源": "有附件时写明来源或可核验说明；无附件可留空。",
                    "后续交互思路": "说明如何用多轮追问推进任务，并体现专业工作量。",
                    "姓名": "填写与专家信息采集表一致的姓名。",
                    "豆包UID": "填写完成本次豆包办公任务的 UID。",
                    "使用工具": "请选择豆包办公任务。",
                    "轮次数": "填写有效问答轮数，至少 6 轮。",
                    "对话图片": "上传能够覆盖完整关键交互过程的对话截图。",
                    "轨迹链接": "填写本次完整交互的可访问轨迹链接。",
                    "日志ID": "填写豆包办公任务生成的日志 ID。",
                    "本人确认": "确认由本人完成提交，且未包含密码、验证码或未脱敏保密信息。",
                    "返修关联码": "首次提交留空；仅在导师核验本人身份后填写一次性、未过期的返修关联码。请勿转发、猜测或复用。",
                },
                {
                    "UID",
                    "题目",
                    "题目领域一级目录",
                    "题目领域二级目录",
                    "后续交互思路",
                    "姓名",
                    "豆包UID",
                    "使用工具",
                    "轮次数",
                    "对话图片",
                    "轨迹链接",
                    "日志ID",
                    "本人确认",
                },
            ),
        ),
    )


class FormPublisher:
    """Publishes new Forms only after their external field contract is safe."""

    def __init__(self, client: FormClient) -> None:
        self._client = client

    @staticmethod
    def _table_lookup(tables: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for table in tables:
            name = table.get("name")
            table_id = table.get("table_id")
            if not isinstance(name, str) or not name.strip() or not isinstance(table_id, str):
                raise FormSchemaDriftError("table metadata is invalid")
            if name in lookup:
                raise FormSchemaDriftError(f"duplicate table name: {name}")
            lookup[name] = table
        return lookup

    @staticmethod
    def _view_id(views: list[dict[str, Any]], form_name: str) -> str:
        matches = [
            view
            for view in views
            if view.get("view_name") == form_name and view.get("view_type") == "form"
        ]
        if len(matches) != 1 or not isinstance(matches[0].get("view_id"), str):
            raise FormSchemaDriftError(f"native Form view missing or ambiguous: {form_name}")
        return str(matches[0]["view_id"])

    @staticmethod
    def _field_lookup(fields: list[dict[str, Any]], table_name: str) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for field in fields:
            name = field.get("field_name")
            field_id = field.get("field_id")
            if not isinstance(name, str) or not name.strip() or not isinstance(field_id, str):
                raise FormSchemaDriftError(f"field metadata is invalid: {table_name}")
            if name in lookup:
                raise FormSchemaDriftError(f"duplicate field name: {table_name}/{name}")
            lookup[name] = field
        return lookup

    @staticmethod
    def _form_field_lookup(fields: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        lookup: dict[str, dict[str, Any]] = {}
        for field in fields:
            field_id = field.get("field_id")
            if not isinstance(field_id, str) or not field_id.strip():
                raise FormSchemaDriftError("Form question identity is invalid")
            if field_id in lookup:
                raise FormSchemaDriftError(f"duplicate Form question identity: {field_id}")
            lookup[field_id] = field
        return lookup

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
        table_fields = self._field_lookup(self._client.list_fields(table_id), config.table_name)
        configured_names = {field.name for field in config.fields}
        if set(table_fields) != configured_names:
            raise FormSchemaDriftError(f"table field contract differs: {config.table_name}")
        form_fields = self._form_field_lookup(self._client.list_form_fields(table_id, form_id))
        missing = [
            field_name
            for field_name, table_field in table_fields.items()
            if str(table_field["field_id"]) not in form_fields
        ]
        if missing:
            raise FormSchemaDriftError(f"Form questions missing: {config.form_name}")
        metadata = self._client.get_form_metadata(table_id, form_id)
        return table_id, form_id, table_fields, form_fields, metadata

    @staticmethod
    def _expert_form_configuration() -> PublicFormConfiguration:
        matches = [
            config
            for config in public_form_configurations()
            if config.table_name == "第三期专家"
        ]
        if len(matches) != 1:
            raise FormSchemaDriftError("expert Form configuration is missing or ambiguous")
        return matches[0]

    def _resolve_expert_form(
        self,
    ) -> tuple[
        PublicFormConfiguration,
        str,
        str,
        dict[str, dict[str, Any]],
        dict[str, dict[str, Any]],
        dict[str, Any],
    ]:
        config = self._expert_form_configuration()
        tables = self._table_lookup(self._client.list_tables())
        table_id, form_id, table_fields, form_fields, metadata = self._resolve_form(
            config, tables
        )
        return config, table_id, form_id, table_fields, form_fields, metadata

    @staticmethod
    def _assert_field_contract(
        config: PublicFormConfiguration,
        table_fields: dict[str, dict[str, Any]],
        form_fields: dict[str, dict[str, Any]],
    ) -> None:
        for field_config in config.fields:
            field_id = str(table_fields[field_config.name]["field_id"])
            current = form_fields[field_id]
            desired = FormPublisher._field_body(field_config)
            if any(current.get(key) != value for key, value in desired.items()):
                raise FormSchemaDriftError(
                    f"Form field read-back differs: {config.form_name}/{field_config.name}"
                )

    @staticmethod
    def _expert_probe(
        config: PublicFormConfiguration,
        form_fields: dict[str, dict[str, Any]],
        metadata: dict[str, Any],
    ) -> ExpertFormProbe:
        shared_limit = metadata.get("shared_limit")
        submit_limit_once = metadata.get("submit_limit_once")
        return ExpertFormProbe(
            form_name=config.form_name,
            shared=metadata.get("shared") is True,
            shared_limit=shared_limit if isinstance(shared_limit, str) else None,
            submit_limit_once=(
                submit_limit_once if isinstance(submit_limit_once, bool) else None
            ),
            question_count=len(form_fields),
            visible_question_count=sum(
                field.get("visible") is True for field in form_fields.values()
            ),
        )

    def probe_expert_form(self) -> ExpertFormProbe:
        """Read only the fixed expert Form's metadata and question state."""

        config, _, _, _, form_fields, metadata = self._resolve_expert_form()
        return self._expert_probe(config, form_fields, metadata)

    def refresh_expert_form(self, *, confirmed: bool) -> ExpertFormProbe:
        """Reconfigure only the expert Form through a fail-closed private window."""

        if not confirmed:
            raise FormPublishConfirmationError(
                "expert Form refresh requires explicit confirmation"
            )

        config, table_id, form_id, table_fields, form_fields, metadata = (
            self._resolve_expert_form()
        )
        if metadata.get("shared") is True:
            self._client.patch_form_metadata(table_id, form_id, {"shared": False})
        private_metadata = self._client.get_form_metadata(table_id, form_id)
        if private_metadata.get("shared") is not False:
            raise FormSchemaDriftError(f"Form remains public: {config.form_name}")

        for field_config in config.fields:
            field_id = str(table_fields[field_config.name]["field_id"])
            desired = self._field_body(field_config)
            current = form_fields[field_id]
            if any(current.get(key) != value for key, value in desired.items()):
                self._client.patch_form_field(table_id, form_id, field_id, desired)

        config, table_id, form_id, table_fields, form_fields, _ = self._resolve_expert_form()
        self._assert_field_contract(config, table_fields, form_fields)
        self._client.patch_form_metadata(
            table_id,
            form_id,
            {
                "description": config.description,
                "shared": True,
                "shared_limit": config.shared_limit,
                "submit_limit_once": config.submit_limit_once,
            },
        )
        config, _, _, table_fields, form_fields, metadata = self._resolve_expert_form()
        self._assert_field_contract(config, table_fields, form_fields)
        probe = self._expert_probe(config, form_fields, metadata)
        if (
            probe.shared is not True
            or probe.shared_limit != config.shared_limit
            or probe.submit_limit_once != config.submit_limit_once
            or not isinstance(metadata.get("shared_url"), str)
            or not metadata["shared_url"]
        ):
            raise FormSchemaDriftError(f"Form publication read-back differs: {config.form_name}")
        return probe

    def plan(self) -> FormPublicationPlan:
        return self._plan(allow_public_field_changes=False)

    def reconfiguration_plan(self) -> FormPublicationPlan:
        """Plan a confirmed private-window reconfiguration without mutating Forms."""

        return self._plan(allow_public_field_changes=True)

    def _plan(self, *, allow_public_field_changes: bool) -> FormPublicationPlan:
        tables = self._table_lookup(self._client.list_tables())
        field_patches: list[FormFieldPatch] = []
        metadata_patches: list[FormMetadataPatch] = []
        for config in public_form_configurations():
            table_id, form_id, table_fields, form_fields, metadata = self._resolve_form(config, tables)
            needs_field_update = False
            for field_config in config.fields:
                field_id = str(table_fields[field_config.name]["field_id"])
                desired = self._field_body(field_config)
                current = form_fields[field_id]
                if any(current.get(key) != value for key, value in desired.items()):
                    needs_field_update = True
                    field_patches.append(
                        FormFieldPatch(
                            table_id=table_id,
                            form_id=form_id,
                            field_id=field_id,
                            field_name=field_config.name,
                            body=desired,
                        )
                    )
            if (
                metadata.get("shared") is True
                and needs_field_update
                and not allow_public_field_changes
            ):
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
                    FormMetadataPatch(table_id, form_id, config.form_name, desired_metadata)
                )
        return FormPublicationPlan(tuple(field_patches), tuple(metadata_patches))

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
        return FormPublicationReceipt(self._published_forms(tables))

    def reconfigure_public_forms(self, *, confirmed: bool) -> FormPublicationReceipt:
        """Safely update public questions through a short private window.

        A failure after unsharing intentionally leaves the affected Form private
        rather than accepting submissions against an incomplete field contract.
        """

        if not confirmed:
            raise FormPublishConfirmationError("public Form reconfiguration requires explicit confirmation")
        plan = self.reconfiguration_plan()
        affected_forms = {
            (patch.table_id, patch.form_id)
            for patch in plan.field_patches
        }
        if not affected_forms:
            return self.publish(confirmed=True)

        for table_id, form_id in sorted(affected_forms):
            metadata = self._client.get_form_metadata(table_id, form_id)
            if metadata.get("shared") is True:
                self._client.patch_form_metadata(table_id, form_id, {"shared": False})

        for patch in plan.field_patches:
            self._client.patch_form_field(
                patch.table_id, patch.form_id, patch.field_id, patch.body
            )

        tables = self._table_lookup(self._client.list_tables())
        self._assert_field_contracts(tables)
        for patch in self.plan().metadata_patches:
            self._client.patch_form_metadata(patch.table_id, patch.form_id, patch.body)
        return FormPublicationReceipt(self._published_forms(tables))

    def pause_public_forms(
        self,
        *,
        confirmed: bool,
        form_names: tuple[str, ...],
    ) -> tuple[PausedForm, ...]:
        """Unshare selected canonical Forms and verify they remain private.

        This small operation intentionally validates only Form identity and
        publication metadata. It can run before an additive table-field change,
        when a full field-contract read-back would correctly report drift.
        """

        if not confirmed:
            raise FormPublishConfirmationError("Form pause requires explicit confirmation")
        selected = set(form_names)
        available = {config.form_name for config in public_form_configurations()}
        if not selected or not selected <= available:
            raise ValueError("form_names must select canonical public Forms")

        tables = self._table_lookup(self._client.list_tables())
        paused: list[PausedForm] = []
        for config in public_form_configurations():
            if config.form_name not in selected:
                continue
            table = tables.get(config.table_name)
            if table is None:
                raise FormSchemaDriftError(f"source table missing: {config.table_name}")
            table_id = str(table["table_id"])
            form_id = self._view_id(self._client.list_views(table_id), config.form_name)
            metadata = self._client.get_form_metadata(table_id, form_id)
            was_shared = metadata.get("shared") is True
            if was_shared:
                self._client.patch_form_metadata(table_id, form_id, {"shared": False})
            verified = self._client.get_form_metadata(table_id, form_id)
            if verified.get("shared") is not False:
                raise FormSchemaDriftError(f"Form remains public: {config.form_name}")
            paused.append(PausedForm(config.form_name, was_shared=was_shared))
        return tuple(paused)

    def retire_legacy_forms(self, *, confirmed: bool) -> tuple[RetiredForm, ...]:
        if not confirmed:
            raise FormPublishConfirmationError("legacy Form retirement requires explicit confirmation")
        tables = self._table_lookup(self._client.list_tables())
        self._published_forms(tables)
        self._assert_field_contracts(tables)

        retired: list[RetiredForm] = []
        for legacy in LEGACY_PUBLIC_FORMS:
            table = tables.get(legacy.table_name)
            if table is None:
                raise FormSchemaDriftError(f"legacy source table missing: {legacy.table_name}")
            table_id = str(table["table_id"])
            form_id = self._view_id(self._client.list_views(table_id), legacy.form_name)
            metadata = self._client.get_form_metadata(table_id, form_id)
            if metadata.get("shared") is True:
                self._client.patch_form_metadata(table_id, form_id, {"shared": False})
            verified = self._client.get_form_metadata(table_id, form_id)
            if verified.get("shared") is not False:
                raise FormSchemaDriftError(f"legacy Form remains public: {legacy.form_name}")
            retired.append(RetiredForm(legacy.form_name, shared=False))
        return tuple(retired)

    def _assert_field_contracts(self, tables: dict[str, dict[str, Any]]) -> None:
        for config in public_form_configurations():
            _, _, table_fields, form_fields, _ = self._resolve_form(config, tables)
            self._assert_field_contract(config, table_fields, form_fields)

    def _published_forms(self, tables: dict[str, dict[str, Any]]) -> tuple[PublishedForm, ...]:
        published: list[PublishedForm] = []
        for config in public_form_configurations():
            _, _, _, _, metadata = self._resolve_form(config, tables)
            shared_url = metadata.get("shared_url")
            if (
                metadata.get("shared") is not True
                or metadata.get("shared_limit") != config.shared_limit
                or metadata.get("submit_limit_once") != config.submit_limit_once
                or not isinstance(shared_url, str)
                or not shared_url
            ):
                raise FormSchemaDriftError(f"Form publication read-back differs: {config.form_name}")
            published.append(PublishedForm(config.form_name, shared_url))
        return tuple(published)
