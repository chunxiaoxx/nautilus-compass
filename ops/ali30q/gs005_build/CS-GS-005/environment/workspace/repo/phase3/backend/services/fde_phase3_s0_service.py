"""S0 identity-first registration and human admission for the T1 pilot."""

from __future__ import annotations

import hashlib
import logging
import re
import secrets
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping

from services.fde_phase3_bitable_gateway import FeishuPhase3Gateway
from services.fde_phase3_identity_service import (
    FeishuIdentity,
    OpaqueReferenceError,
    RedisOpaqueStore,
)


LOG = logging.getLogger(__name__)
EXPERT_TABLE = "第三期专家"
S0_VERSION = "platform-t1-s0-admission-v3"
IDENTITY_BINDING_VERSION = "feishu-oauth-binding-v2"

# Keep S0 deployable as a narrow production slice. These values mirror the
# authoritative expert-table select options and are covered by schema tests.
EXPERT_EDUCATION_OPTIONS = ("本科", "硕士", "博士", "其他")
EXPERT_SCHOOL_TIER_OPTIONS = ("C9", "985", "211", "双一流", "其它院校", "海外院校")
EXPERT_WORK_YEARS_OPTIONS = ("0-2年", "3-5年", "6-10年", "10年以上")
EXPERT_DAILY_HOURS_OPTIONS = ("1小时以下", "1-2小时", "2-4小时", "4小时以上")

REGISTRATION_REQUIRED_FIELDS = (
    "姓名",
    "豆包UID",
    "联系方式",
    "最高学历",
    "毕业院校",
    "专业",
    "学校层次",
    "工作领域",
    "工作年限",
    "每日作业时长",
    "真实性与隐私承诺",
)
REGISTRATION_OPTIONAL_FIELDS = ("行业证书认证（文字描述）",)
REGISTRATION_FIELDS = REGISTRATION_REQUIRED_FIELDS + REGISTRATION_OPTIONAL_FIELDS
REGISTRATION_FIELD_OPTIONS = {
    "最高学历": EXPERT_EDUCATION_OPTIONS,
    "学校层次": EXPERT_SCHOOL_TIER_OPTIONS,
    "工作年限": EXPERT_WORK_YEARS_OPTIONS,
    "每日作业时长": EXPERT_DAILY_HOURS_OPTIONS,
}
ADMISSION_DECISIONS = ("通过", "退回补充", "异常升级")


class S0BindingError(ValueError):
    pass


@dataclass(frozen=True)
class S0Invitation:
    expert_name: str
    expert_open_id: str
    invite_token: str
    audit_ref: str
    expires_in_seconds: int


@dataclass(frozen=True)
class S0IdentityIntake:
    expert_name: str
    registration_token: str
    missing_fields: tuple[str, ...]
    existing_record: bool
    expires_in_seconds: int


@dataclass(frozen=True)
class S0RegistrationReceipt:
    status: str
    version: str
    expert_record_hash: str
    open_id_hash: str
    uid_hash: str
    bitable_readback_confirmed: bool
    agent_recommendation: str
    operator_message_id: str
    operator_message_readback_confirmed: bool
    submitted_at: str

    def safe_payload(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class S0AdmissionReceipt:
    status: str
    version: str
    expert_record_hash: str
    operator_open_id_hash: str
    decision: str
    bitable_readback_confirmed: bool
    mentor_message_id: str
    mentor_message_readback_confirmed: bool
    decided_at: str

    def safe_payload(self) -> dict[str, Any]:
        return asdict(self)


class Phase3S0Service:
    def __init__(
        self,
        *,
        gateway: FeishuPhase3Gateway,
        references: RedisOpaqueStore,
        public_base_url: str,
        operator_chat_id: str,
    ) -> None:
        self.gateway = gateway
        self.references = references
        self.public_base_url = public_base_url.rstrip("/")
        self.operator_chat_id = operator_chat_id

    def issue_pilot_invitation(
        self,
        expert_record_id: str = "",
        expected_name: str = "",
    ) -> S0Invitation:
        expert_name = expected_name.strip()
        record_hash = ""
        record_fields: Mapping[str, Any] = {}
        if expert_record_id:
            expert = self.gateway.get_record(EXPERT_TABLE, expert_record_id)
            fields = expert.get("fields") or {}
            record_fields = fields
            record_name = str(fields.get("姓名") or "").strip()
            if expert_name and record_name != expert_name:
                raise S0BindingError("邀请指定姓名与权威报名记录不一致")
            expert_name = record_name
            record_hash = _hash(expert_record_id)
        if not expert_name:
            raise S0BindingError("S0 邀请必须绑定一位明确的专家")
        expert_open_id = self._resolve_pilot_open_id(expert_name, record_fields)

        audit_ref = secrets.token_urlsafe(24)
        self.references.replace(
            "s0_audit",
            audit_ref,
            {
                "status": "pending_expert_oauth",
                "version": S0_VERSION,
                "expert_record_hash": record_hash,
                "expert_open_id_hash": _hash(expert_open_id),
            },
            7 * 86400,
        )
        invite_token = self.references.issue(
            "s0_invitation",
            {
                "expert_record_id": expert_record_id,
                "expected_name": expert_name,
                "expected_open_id": expert_open_id,
                "audit_ref": audit_ref,
            },
            86400,
        )
        return S0Invitation(
            expert_name=expert_name,
            expert_open_id=expert_open_id,
            invite_token=invite_token,
            audit_ref=audit_ref,
            expires_in_seconds=86400,
        )

    def deliver_pilot_invitation(self, invitation: S0Invitation) -> str:
        invite_url = (
            f"{self.public_base_url}/api/platform/fde/phase3/s0/bind/start"
            f"?invite={invitation.invite_token}"
        )
        message_id = self.gateway.send_interactive_card(
            invitation.expert_open_id,
            _expert_invitation_card(invitation.expert_name, invite_url),
        )
        if not message_id:
            raise S0BindingError("专家邀请未返回消息 ID")
        self.references.replace(
            "s0_invitation_delivery",
            invitation.audit_ref,
            {"message_id": message_id, "status": "sent_pending_readback"},
            7 * 86400,
        )
        message = self.gateway.get_message(message_id)
        if str(message.get("message_id") or "") != message_id:
            raise S0BindingError("专家邀请消息读回不一致")
        self.references.replace(
            "s0_invitation_delivery",
            invitation.audit_ref,
            {"message_id": message_id, "status": "readback_confirmed"},
            7 * 86400,
        )
        audit = self.references.peek("s0_audit", invitation.audit_ref)
        audit.update(
            {
                "status": "pending_expert_oauth",
                "invitation_delivery": "direct_im_readback_confirmed",
            }
        )
        self.references.replace("s0_audit", invitation.audit_ref, audit, 7 * 86400)
        return message_id

    def start_identity_intake(
        self,
        invitation: Mapping[str, Any],
        identity: FeishuIdentity,
    ) -> S0IdentityIntake:
        audit_ref = str(invitation.get("audit_ref") or "")
        expected_name = str(invitation.get("expected_name") or "").strip()
        expected_open_id = str(invitation.get("expected_open_id") or "").strip()
        invited_record_id = str(invitation.get("expert_record_id") or "")
        if not audit_ref or not expected_name or not expected_open_id or not identity.open_id:
            raise S0BindingError("身份识别入口不完整，请联系运营重新发放")
        if identity.open_id != expected_open_id:
            raise S0BindingError("该入口仅限受邀专家本人使用，已停止绑定")

        with self.references.lock(f"s0-intake:{identity.open_id}"):
            record, _ = self._resolve_record(
                record_id=invited_record_id,
                expected_name=expected_name,
                open_id=identity.open_id,
            )
            fields = (record or {}).get("fields") or {}
            self._assert_identity_compatible(fields, identity)
            missing = tuple(
                field for field in REGISTRATION_FIELDS if _is_missing(fields.get(field))
            )
            registration_token = self.references.issue(
                "s0_registration",
                {
                    "expert_record_id": str((record or {}).get("record_id") or ""),
                    "expected_name": expected_name,
                    "open_id": identity.open_id,
                    "union_id": identity.union_id,
                    "identity_name": identity.name,
                    "audit_ref": audit_ref,
                },
                900,
            )
            self.references.replace(
                "s0_audit",
                audit_ref,
                {
                    "status": "awaiting_registration_confirmation",
                    "version": S0_VERSION,
                    "expert_record_hash": _hash(str((record or {}).get("record_id") or "")),
                    "open_id_hash": _hash(identity.open_id),
                    "missing_field_count": len(missing),
                },
                7 * 86400,
            )
        return S0IdentityIntake(
            expert_name=expected_name,
            registration_token=registration_token,
            missing_fields=missing,
            existing_record=record is not None,
            expires_in_seconds=900,
        )

    def submit_registration(
        self,
        intake: Mapping[str, Any],
        submitted: Mapping[str, Any],
    ) -> S0RegistrationReceipt:
        open_id = str(intake.get("open_id") or "")
        identity = FeishuIdentity(
            open_id=open_id,
            union_id=str(intake.get("union_id") or ""),
            name=str(intake.get("identity_name") or ""),
        )
        expected_name = str(intake.get("expected_name") or "").strip()
        audit_ref = str(intake.get("audit_ref") or "")
        claimed_record_id = str(intake.get("expert_record_id") or "")
        if not open_id or not expected_name or not audit_ref:
            raise S0BindingError("报名确认会话不完整，请从一次性入口重新进入")

        try:
            with self.references.lock(f"s0-register:{open_id}"):
                record, records = self._resolve_record(
                    record_id=claimed_record_id,
                    expected_name=expected_name,
                    open_id=open_id,
                )
                fields = (record or {}).get("fields") or {}
                self._assert_identity_compatible(fields, identity)
                values = self._validated_registration_values(
                    fields=fields,
                    submitted=submitted,
                    expected_name=expected_name,
                )
                record_id = str((record or {}).get("record_id") or "")
                duplicate_names = _matching_records(records, "姓名", values["姓名"], record_id)
                duplicate_uids = _matching_records(records, "豆包UID", values["豆包UID"], record_id)
                if duplicate_names:
                    raise S0BindingError("存在同名报名冲突，未写入身份或报名信息")
                if duplicate_uids:
                    raise S0BindingError("豆包 UID 与其他报名记录冲突，未写入身份或报名信息")
                recommendation = "建议通过"
                summary = _agent_summary(
                    duplicate_name_count=len(duplicate_names),
                    duplicate_uid_count=len(duplicate_uids),
                )
                now = datetime.now(timezone.utc)
                updates = self._registration_updates(fields, values)
                updates.update(
                    {
                        "飞书open_id": identity.open_id,
                        "飞书union_id": identity.union_id,
                        "身份绑定状态": "已绑定",
                        "身份绑定时间": int(now.timestamp() * 1000),
                        "身份绑定版本": IDENTITY_BINDING_VERSION,
                        "准入状态": "待审核",
                        "Agent准入检查摘要": summary,
                        "Agent准入建议": recommendation,
                        "运营准入决定": "待确认",
                    }
                )
                if _is_missing(fields.get("专家状态")):
                    updates["专家状态"] = "待培训"
                if _is_missing(fields.get("培训状态")):
                    updates["培训状态"] = "未开始"
                if _is_missing(fields.get("豆包开通状态")):
                    updates["豆包开通状态"] = "待申请"

                verify_fields = (
                    "姓名",
                    "豆包UID",
                    "飞书open_id",
                    "身份绑定状态",
                    "身份绑定版本",
                    "准入状态",
                    "Agent准入检查摘要",
                    "Agent准入建议",
                    "运营准入决定",
                )
                if record is None:
                    readback = self.gateway.create_record(
                        EXPERT_TABLE,
                        updates,
                        verify_fields=verify_fields,
                    )
                    record_id = str(readback.get("record_id") or "")
                else:
                    readback = self.gateway.update_record(
                        EXPERT_TABLE,
                        record_id,
                        updates,
                        verify_fields=verify_fields,
                    )
                readback_fields = readback.get("fields") or {}
                self._assert_registration_readback(readback_fields, values, identity, recommendation)

                review_token = self.references.issue(
                    "s0_review",
                    {"expert_record_id": record_id, "audit_ref": audit_ref},
                    7 * 86400,
                )
                review_url = (
                    f"{self.public_base_url}/api/platform/fde/phase3/s0/pilot/review/start"
                    f"?review={review_token}"
                )
                message_id = self.gateway.send_interactive_card(
                    self.operator_chat_id,
                    _operator_review_card(expected_name, recommendation, summary, review_url),
                    receive_id_type="chat_id",
                )
                if not message_id:
                    raise S0BindingError("运营准入卡片未返回消息 ID")
                message = self.gateway.get_message(message_id)
                message_ok = str(message.get("message_id") or "") == message_id
                if not message_ok:
                    raise S0BindingError("运营准入卡片读回不一致")
                receipt = S0RegistrationReceipt(
                    status="pending_operator_admission",
                    version=S0_VERSION,
                    expert_record_hash=_hash(record_id),
                    open_id_hash=_hash(open_id),
                    uid_hash=_hash(values["豆包UID"]),
                    bitable_readback_confirmed=True,
                    agent_recommendation=recommendation,
                    operator_message_id=message_id,
                    operator_message_readback_confirmed=True,
                    submitted_at=now.isoformat(),
                )
        except Exception as exc:
            self._record_failure(audit_ref, claimed_record_id, exc)
            raise

        self.references.replace("s0_audit", audit_ref, receipt.safe_payload(), 7 * 86400)
        return receipt

    def operator_review(self, review: Mapping[str, Any]) -> dict[str, str]:
        record_id = str(review.get("expert_record_id") or "")
        if not record_id:
            raise S0BindingError("运营审核入口不完整")
        record = self.gateway.get_record(EXPERT_TABLE, record_id)
        fields = record.get("fields") or {}
        return {
            "expert_name": str(fields.get("姓名") or "专家"),
            "agent_summary": str(fields.get("Agent准入检查摘要") or "Agent 尚未形成可追溯摘要"),
            "agent_recommendation": str(fields.get("Agent准入建议") or "建议升级"),
            "current_decision": str(fields.get("运营准入决定") or "待确认"),
        }

    def assert_operator(self, identity: FeishuIdentity) -> None:
        members = set(self.gateway.list_chat_member_open_ids(self.operator_chat_id))
        if identity.open_id not in members:
            raise S0BindingError("当前飞书身份不是指定运营群成员，不能处理准入")

    def apply_admission_decision(
        self,
        review: Mapping[str, Any],
        identity: FeishuIdentity,
        decision: str,
        note: str = "",
    ) -> S0AdmissionReceipt:
        if decision not in ADMISSION_DECISIONS:
            raise S0BindingError("运营决定必须从三个选项中选择")
        self.assert_operator(identity)
        record_id = str(review.get("expert_record_id") or "")
        audit_ref = str(review.get("audit_ref") or "")
        if not record_id or not audit_ref:
            raise S0BindingError("运营审核入口不完整")

        with self.references.lock(f"s0-admission:{record_id}"):
            record = self.gateway.get_record(EXPERT_TABLE, record_id)
            fields = record.get("fields") or {}
            current_decision = str(fields.get("运营准入决定") or "")
            resuming_delivery = current_decision != "待确认"
            if resuming_delivery and (
                current_decision != decision
                or str(fields.get("运营准入人open_id") or "") != identity.open_id
            ):
                raise S0BindingError("该准入事项已由其他决定处理")
            recommendation = str(fields.get("Agent准入建议") or "")
            if not str(fields.get("Agent准入检查摘要") or "").strip():
                raise S0BindingError("Agent 准入证据摘要缺失，已停止人工确认")
            cleaned_note = note.strip()[:500]
            if not resuming_delivery and decision != "通过" and not cleaned_note:
                raise S0BindingError("退回补充或异常升级必须填写简短原因")
            if not resuming_delivery and decision == "通过" and recommendation != "建议通过" and not cleaned_note:
                raise S0BindingError("运营与 Agent 建议不一致时必须填写说明")

            admission_state = {
                "通过": "已通过",
                "退回补充": "需补充",
                "异常升级": "待审核",
            }[decision]
            now = datetime.now(timezone.utc)
            if resuming_delivery:
                readback_fields = fields
            else:
                readback = self.gateway.update_record(
                    EXPERT_TABLE,
                    record_id,
                    {
                        "准入状态": admission_state,
                        "运营准入决定": decision,
                        "运营准入人open_id": identity.open_id,
                        "运营准入时间": int(now.timestamp() * 1000),
                        "准入处理说明": cleaned_note,
                    },
                    verify_fields=(
                        "准入状态",
                        "运营准入决定",
                        "运营准入人open_id",
                        "准入处理说明",
                    ),
                )
                readback_fields = readback.get("fields") or {}
            decision_ok = (
                str(readback_fields.get("准入状态") or "") == admission_state
                and str(readback_fields.get("运营准入决定") or "") == decision
                and str(readback_fields.get("运营准入人open_id") or "") == identity.open_id
            )
            if not decision_ok:
                raise S0BindingError("Bitable 独立回读未确认运营准入决定")

            expert_open_id = str(readback_fields.get("飞书open_id") or "")
            if not expert_open_id:
                raise S0BindingError("专家飞书身份缺失，无法发送准入结果")
            delivery = self._optional_reference("s0_admission_delivery", audit_ref)
            message_id = str(delivery.get("message_id") or "")
            decided_at = str(delivery.get("decided_at") or now.isoformat())
            if not message_id:
                continuation_url = ""
                if decision == "退回补充":
                    continuation = self.issue_pilot_invitation(
                        expert_record_id=record_id,
                        expected_name=str(readback_fields.get("姓名") or ""),
                    )
                    continuation_url = (
                        f"{self.public_base_url}/api/platform/fde/phase3/s0/bind/start"
                        f"?invite={continuation.invite_token}"
                    )
                message_id = self.gateway.send_interactive_card(
                    expert_open_id,
                    _expert_admission_card(decision, continuation_url),
                )
                if not message_id:
                    raise S0BindingError("专家准入结果未返回消息 ID")
                self.references.replace(
                    "s0_admission_delivery",
                    audit_ref,
                    {
                        "decision": decision,
                        "message_id": message_id,
                        "decided_at": decided_at,
                        "status": "sent_pending_readback",
                    },
                    7 * 86400,
                )
            message = self.gateway.get_message(message_id)
            message_ok = str(message.get("message_id") or "") == message_id
            if not message_ok:
                raise S0BindingError("专家准入结果消息读回不一致")
            self.references.replace(
                "s0_admission_delivery",
                audit_ref,
                {
                    "decision": decision,
                    "message_id": message_id,
                    "decided_at": decided_at,
                    "status": "readback_confirmed",
                },
                7 * 86400,
            )
            receipt = S0AdmissionReceipt(
                status={
                    "通过": "admitted_waiting_first_task",
                    "退回补充": "registration_supplement_required",
                    "异常升级": "project_support_required",
                }[decision],
                version=S0_VERSION,
                expert_record_hash=_hash(record_id),
                operator_open_id_hash=_hash(identity.open_id),
                decision=decision,
                bitable_readback_confirmed=True,
                mentor_message_id=message_id,
                mentor_message_readback_confirmed=True,
                decided_at=decided_at,
            )
        self.references.replace("s0_audit", audit_ref, receipt.safe_payload(), 7 * 86400)
        return receipt

    def audit_status(self, audit_ref: str) -> dict[str, Any]:
        return self.references.peek("s0_audit", audit_ref)

    def _resolve_pilot_open_id(
        self,
        expert_name: str,
        record_fields: Mapping[str, Any],
    ) -> str:
        matches = [
            item
            for item in self.gateway.list_chat_members(self.operator_chat_id)
            if str(item.get("name") or "").strip() == expert_name
        ]
        if len(matches) != 1:
            raise S0BindingError("运营群中未找到唯一同名专家，禁止生成邀请")
        group_open_id = str(matches[0].get("member_id") or "").strip()
        record_open_id = str(record_fields.get("飞书open_id") or "").strip()
        if not group_open_id:
            raise S0BindingError("运营群成员缺少可绑定的飞书身份")
        if record_open_id and record_open_id != group_open_id:
            raise S0BindingError("权威记录与运营群飞书身份不一致")
        return group_open_id

    def _optional_reference(self, purpose: str, token: str) -> dict[str, Any]:
        try:
            return self.references.peek(purpose, token)
        except (OpaqueReferenceError, KeyError):
            return {}

    def _resolve_record(
        self,
        *,
        record_id: str,
        expected_name: str,
        open_id: str,
    ) -> tuple[dict[str, Any] | None, list[dict[str, Any]]]:
        records = self.gateway.list_records(EXPERT_TABLE)
        by_identity = [
            item
            for item in records
            if str((item.get("fields") or {}).get("飞书open_id") or "") == open_id
        ]
        if len(by_identity) > 1:
            raise S0BindingError("该飞书身份关联多条报名记录，已转异常处理")

        selected = None
        if record_id:
            selected = next((item for item in records if str(item.get("record_id") or "") == record_id), None)
            if selected is None:
                raise S0BindingError("邀请对应的权威报名记录不存在")
            if by_identity and str(by_identity[0].get("record_id") or "") != record_id:
                raise S0BindingError("该飞书身份已关联另一条报名记录")
        elif by_identity:
            selected = by_identity[0]
        else:
            by_name = [
                item
                for item in records
                if str((item.get("fields") or {}).get("姓名") or "").strip() == expected_name
            ]
            if len(by_name) > 1:
                raise S0BindingError("存在多条同名报名记录，已转异常处理")
            if by_name:
                selected = by_name[0]

        if selected is not None:
            record_name = str((selected.get("fields") or {}).get("姓名") or "").strip()
            if record_name and record_name != expected_name:
                raise S0BindingError("邀请指定姓名与权威报名记录不一致")
        return selected, records

    @staticmethod
    def _assert_identity_compatible(fields: Mapping[str, Any], identity: FeishuIdentity) -> None:
        existing_open_id = str(fields.get("飞书open_id") or "")
        existing_union_id = str(fields.get("飞书union_id") or "")
        if existing_open_id and existing_open_id != identity.open_id:
            raise S0BindingError("该报名记录已经绑定其他飞书身份")
        if existing_union_id and identity.union_id and existing_union_id != identity.union_id:
            raise S0BindingError("该报名记录的飞书身份校验不一致")
        if str(fields.get("专家状态") or "") in {"暂停", "停用"}:
            raise S0BindingError("该专家当前不可进入 S0")

    @staticmethod
    def _validated_registration_values(
        *,
        fields: Mapping[str, Any],
        submitted: Mapping[str, Any],
        expected_name: str,
    ) -> dict[str, Any]:
        submitted_name = str(submitted.get("姓名") or "").strip()
        if submitted_name and submitted_name != expected_name:
            raise S0BindingError("报名姓名必须与本次邀请一致")
        values: dict[str, Any] = {}
        for field in REGISTRATION_FIELDS:
            current = fields.get(field)
            incoming = submitted.get(field)
            if field == "真实性与隐私承诺":
                current = _as_bool(current)
                incoming = _as_bool(incoming)
            elif incoming is not None:
                incoming = str(incoming).strip()
            if not _is_missing(current):
                if not _is_missing(incoming) and incoming != current:
                    if field == "豆包UID":
                        raise S0BindingError("豆包 UID 只能填写一次，不能覆盖")
                    raise S0BindingError(f"{field} 已存在，不能通过 S0 覆盖")
                values[field] = current
            else:
                values[field] = incoming
        values["姓名"] = expected_name
        missing = [field for field in REGISTRATION_REQUIRED_FIELDS if _is_missing(values.get(field))]
        if missing:
            raise S0BindingError("请完成页面显示的必填信息后再提交")
        if not re.fullmatch(r"[0-9]{6,32}", str(values["豆包UID"])):
            raise S0BindingError("豆包 UID 格式不正确，请只填写数字")
        for field, options in REGISTRATION_FIELD_OPTIONS.items():
            if values[field] not in options:
                raise S0BindingError(f"{field} 必须从页面选项中选择")
        if not _as_bool(values["真实性与隐私承诺"]):
            raise S0BindingError("必须确认真实性与隐私承诺")
        values["真实性与隐私承诺"] = True
        return values

    @staticmethod
    def _registration_updates(fields: Mapping[str, Any], values: Mapping[str, Any]) -> dict[str, Any]:
        updates: dict[str, Any] = {}
        for field in REGISTRATION_FIELDS:
            if _is_missing(fields.get(field)) and not _is_missing(values.get(field)):
                updates[field] = values[field]
        return updates

    @staticmethod
    def _assert_registration_readback(
        fields: Mapping[str, Any],
        values: Mapping[str, Any],
        identity: FeishuIdentity,
        recommendation: str,
    ) -> None:
        ok = (
            str(fields.get("姓名") or "") == values["姓名"]
            and str(fields.get("豆包UID") or "") == values["豆包UID"]
            and str(fields.get("飞书open_id") or "") == identity.open_id
            and str(fields.get("身份绑定状态") or "") == "已绑定"
            and str(fields.get("身份绑定版本") or "") == IDENTITY_BINDING_VERSION
            and str(fields.get("准入状态") or "") == "待审核"
            and str(fields.get("Agent准入建议") or "") == recommendation
            and str(fields.get("运营准入决定") or "") == "待确认"
        )
        if not ok:
            raise S0BindingError("Bitable 独立回读未确认报名、身份和 Agent 建议")

    def _record_failure(self, audit_ref: str, record_id: str, exc: Exception) -> None:
        if not audit_ref:
            return
        self.references.replace(
            "s0_audit",
            audit_ref,
            {
                "status": "failed",
                "version": S0_VERSION,
                "expert_record_hash": _hash(record_id),
                "failure": _safe_failure(exc),
            },
            7 * 86400,
        )


def _operator_review_card(
    expert_name: str,
    recommendation: str,
    summary: str,
    review_url: str,
) -> dict[str, Any]:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "turquoise",
            "title": {"tag": "plain_text", "content": "T1 首题 · 准入待确认"},
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"**专家：**{expert_name}\n\n"
                        f"**Agent 建议：**{recommendation}\n\n"
                        f"**证据摘要：**{summary}"
                    ),
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "type": "primary",
                        "text": {"tag": "plain_text", "content": "打开并选择"},
                        "url": review_url,
                    }
                ],
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "运营不重做评分，只核对 Agent 摘要后选择通过、退回补充或异常升级。",
                    }
                ],
            },
        ],
    }


def _expert_invitation_card(expert_name: str, invite_url: str) -> dict[str, Any]:
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "turquoise",
            "title": {"tag": "plain_text", "content": "智涌导师 · T1 身份确认"},
        },
        "elements": [
            {
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": (
                        f"{expert_name}，请确认飞书身份并完成第三期 T1 准入。"
                        "\n\n当前不会开放题目或交互；已有资料不会要求重复填写。"
                    ),
                },
            },
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "type": "primary",
                        "text": {"tag": "plain_text", "content": "确认身份并继续"},
                        "url": invite_url,
                    }
                ],
            },
            {
                "tag": "note",
                "elements": [
                    {
                        "tag": "plain_text",
                        "content": "入口仅限本人、24 小时有效且不可转用；无需填写记录号或任务编号。",
                    }
                ],
            },
        ],
    }


def _expert_admission_card(decision: str, continuation_url: str) -> dict[str, Any]:
    copy = {
        "通过": (
            "准入已完成",
            "你的报名信息、飞书身份和准入结果已完成账本回读。",
            "当前唯一下一步：等待智涌导师发放首题入口。",
        ),
        "退回补充": (
            "请补充报名信息",
            "运营已根据 Agent 摘要确认需要补充信息。",
            "当前唯一下一步：点击下方按钮，只补充缺失信息。",
        ),
        "异常升级": (
            "已转项目支持",
            "身份或报名信息存在需要人工核对的异常。",
            "当前无需重复报名，等待项目支持联系。",
        ),
    }[decision]
    title, message, next_action = copy
    elements: list[dict[str, Any]] = [
        {
            "tag": "div",
            "text": {"tag": "lark_md", "content": f"{message}\n\n**{next_action}**"},
        }
    ]
    if continuation_url:
        elements.append(
            {
                "tag": "action",
                "actions": [
                    {
                        "tag": "button",
                        "type": "primary",
                        "text": {"tag": "plain_text", "content": "补充缺失信息"},
                        "url": continuation_url,
                    }
                ],
            }
        )
    elements.append(
        {
            "tag": "note",
            "elements": [
                {"tag": "plain_text", "content": "无需填写记录号、任务编号或内部状态。"}
            ],
        }
    )
    return {
        "config": {"wide_screen_mode": True},
        "header": {
            "template": "turquoise" if decision == "通过" else "orange",
            "title": {"tag": "plain_text", "content": f"智涌导师 · {title}"},
        },
        "elements": elements,
    }


def _agent_summary(*, duplicate_name_count: int, duplicate_uid_count: int) -> str:
    return (
        "飞书身份已确认；报名必填项完整；"
        f"同名冲突 {duplicate_name_count} 条；UID 冲突 {duplicate_uid_count} 条；"
        "未披露 UID、内部记录号或评分阈值。"
    )


def _matching_records(
    records: list[dict[str, Any]],
    field_name: str,
    value: Any,
    current_record_id: str,
) -> list[dict[str, Any]]:
    expected = str(value or "").strip()
    return [
        item
        for item in records
        if str(item.get("record_id") or "") != current_record_id
        and str((item.get("fields") or {}).get(field_name) or "").strip() == expected
    ]


def _as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "on", "是"}


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value is False


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest() if value else ""


def _safe_failure(exc: Exception) -> str:
    if isinstance(exc, S0BindingError):
        return str(exc)[:200]
    LOG.exception("S0 admission failed")
    return "external_write_or_readback_failed"
