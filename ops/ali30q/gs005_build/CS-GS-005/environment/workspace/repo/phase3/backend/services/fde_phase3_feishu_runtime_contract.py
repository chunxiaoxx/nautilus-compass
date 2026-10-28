"""Application-role and redaction contract for the Phase 3 Feishu loop.

The native Feishu Form is the only external ingress.  This module governs the
controlled follow-up mutations and downstream projections after a Bitable
read-back; it deliberately performs no network or storage I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import hashlib
import re
from types import MappingProxyType
from typing import Any, Mapping, Protocol, runtime_checkable

from services.fde_phase3_continuations import MentorContinuationAction
from services.fde_phase3_feishu import ExportReadback
from services.fde_phase3_mentor_projection import MentorTaskGuidance
from services.fde_phase3_single_submission_schema import PHASE3_WORKFLOW_PROFILE


_SHA256_PATTERN = re.compile(r"sha256:[0-9a-f]{64}\Z")
_V3_TASK_ID_PATTERN = re.compile(r"task_v3_[A-Za-z0-9_-]{1,80}\Z")
_MENTOR_EXPERT_HANDLE_PATTERN = re.compile(r"mentor_expert_[A-Za-z0-9_-]{1,80}\Z")
_MENTOR_TASK_HANDLE_PATTERN = re.compile(r"mentor_task_[A-Za-z0-9_-]{1,80}\Z")
_REPAIR_REFERENCE_PATTERN = re.compile(r"repair_[A-Za-z0-9_-]{1,80}\Z")


class AppRole(str, Enum):
    """The deployed application roles, not developer-chat participants."""

    NAUTILUS = "nautilus"
    MENTOR = "mentor"


class RuntimeRoute(str, Enum):
    """The only Bitable-led business events accepted by this contract."""

    QUESTION_CREATED = "question_created"
    QUESTION_PRECHECK_COMPLETED = "question_precheck_completed"
    INTERACTION_SUBMITTED = "interaction_submitted"
    SUBMISSION_CREATED = "submission_created"
    QC_COMPLETED = "qc_completed"
    REPAIR_REQUIRED = "repair_required"
    BUYER_FEEDBACK_RECORDED = "buyer_feedback_recorded"
    COMPASS_RECEIPT_RECORDED = "compass_receipt_recorded"


class RepairReferenceState(str, Enum):
    """The only server-side lifecycle states for an issued repair reference."""

    ACTIVE = "active"
    USED = "used"
    EXPIRED = "expired"


class CanonicalTable(str, Enum):
    """The canonical Phase 3 tables eligible for controlled mutation."""

    EXPERT = "第三期专家"
    QUESTION_PRECHECK = "第三期题目预审"
    INTERACTION_RESULT = "第三期交互成果"
    TASK_SUBMISSION = "第三期任务与交互提交"
    REVIEW_FEEDBACK = "第三期审核与反馈"
    EXPORT_RECEIPT = "第三期导出与回执"


_TASK_QC_FIELDS = frozenset(
    {
        "业务状态",
        "自动P0状态",
        "自动QC置信度",
        "自动QC原因",
        "自动QC版本",
        "导师下一步",
        "买方映射状态",
    }
)
_TASK_SUBMISSION_INITIALIZATION_FIELDS = frozenset(
    {
        "工作流配置",
        "专家关联",
        "业务状态",
        "自动P0状态",
    }
)
_TASK_REPAIR_FIELDS = _TASK_QC_FIELDS | frozenset(
    {"返修关联码", "返修码状态", "返修码到期时间"}
)
_QUESTION_INITIALIZATION_FIELDS = frozenset(
    {"工作流配置", "专家关联", "题目状态", "自动P0状态"}
)
_QUESTION_PRECHECK_FIELDS = frozenset(
    {
        "题目状态",
        "自动P0状态",
        "自动QC置信度",
        "自动QC原因",
        "自动QC版本",
        "导师下一步",
        "交互入口状态",
        "交互入口到期时间",
    }
)
_INTERACTION_INITIALIZATION_FIELDS = frozenset(
    {"工作流配置", "题目关联", "专家关联", "交互状态", "自动P0状态"}
)
_REVIEW_QC_FIELDS = frozenset(
    {
        "提交关联",
        "审核来源",
        "P0状态",
        "P0失败类别",
        "QC策略版本",
        "QC模型版本",
        "QC置信度",
        "反馈类别",
        "反馈摘要（导师可用）",
        "幂等键",
        "处理时间",
        "脱敏状态",
    }
)
_REVIEW_BUYER_FIELDS = frozenset(
    {
        "审核来源",
        "反馈类别",
        "反馈摘要（导师可用）",
        "买方状态",
        "verdict",
        "证据摘要哈希",
        "幂等键",
        "处理时间",
        "脱敏状态",
    }
)
_V5_EXPORT_FIELDS = frozenset(
    {
        "提交关联",
        "审核关联",
        "导出状态",
        "资格或阻断原因",
        "opaque_task_id",
        "event_id",
        "payload_hash",
        "manifest_hash",
        "V5签名键ID",
        "导出时间",
        "脱敏状态",
    }
)
_COMPASS_RECEIPT_FIELDS = frozenset(
    {"导出状态", "资格或阻断原因", "compass_receipt_hash", "Compass签名键ID", "回执幂等键", "回执时间"}
)
_MUTABLE_FIELDS_BY_ROUTE: Mapping[
    RuntimeRoute, Mapping[CanonicalTable, frozenset[str]]
] = MappingProxyType(
    {
        RuntimeRoute.QUESTION_CREATED: MappingProxyType(
            {
                CanonicalTable.QUESTION_PRECHECK: _QUESTION_INITIALIZATION_FIELDS,
            }
        ),
        RuntimeRoute.QUESTION_PRECHECK_COMPLETED: MappingProxyType(
            {
                CanonicalTable.QUESTION_PRECHECK: _QUESTION_PRECHECK_FIELDS,
            }
        ),
        RuntimeRoute.INTERACTION_SUBMITTED: MappingProxyType(
            {
                CanonicalTable.INTERACTION_RESULT: _INTERACTION_INITIALIZATION_FIELDS,
            }
        ),
        RuntimeRoute.SUBMISSION_CREATED: MappingProxyType(
            {
                CanonicalTable.TASK_SUBMISSION: _TASK_SUBMISSION_INITIALIZATION_FIELDS
            }
        ),
        RuntimeRoute.QC_COMPLETED: MappingProxyType(
            {
                CanonicalTable.TASK_SUBMISSION: _TASK_QC_FIELDS,
                CanonicalTable.REVIEW_FEEDBACK: _REVIEW_QC_FIELDS,
            }
        ),
        RuntimeRoute.REPAIR_REQUIRED: MappingProxyType(
            {
                CanonicalTable.TASK_SUBMISSION: _TASK_REPAIR_FIELDS,
                CanonicalTable.REVIEW_FEEDBACK: _REVIEW_QC_FIELDS,
            }
        ),
        RuntimeRoute.BUYER_FEEDBACK_RECORDED: MappingProxyType(
            {
                CanonicalTable.TASK_SUBMISSION: frozenset(
                    {"业务状态", "买方映射状态", "导师下一步"}
                ),
                CanonicalTable.REVIEW_FEEDBACK: _REVIEW_BUYER_FIELDS,
                CanonicalTable.EXPORT_RECEIPT: _V5_EXPORT_FIELDS,
            }
        ),
        RuntimeRoute.COMPASS_RECEIPT_RECORDED: MappingProxyType(
            {
                CanonicalTable.EXPORT_RECEIPT: _COMPASS_RECEIPT_FIELDS,
            }
        ),
    }
)


@dataclass(frozen=True)
class BitableEventEnvelope:
    """A non-content event bound to one Bitable identity and row version."""

    route: RuntimeRoute
    record_id: str
    record_version: int
    source_event_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.route, RuntimeRoute):
            raise ValueError("route must be a RuntimeRoute")
        _require_compact_identifier(self.record_id, "record_id")
        _require_compact_identifier(self.source_event_id, "source_event_id")
        if isinstance(self.record_version, bool) or not isinstance(self.record_version, int):
            raise ValueError("record_version must be a positive integer")
        if self.record_version < 1:
            raise ValueError("record_version must be a positive integer")

    @property
    def idempotency_key(self) -> str:
        """Stable across delivery retries, but changes on a new row version."""

        material = "\\x1f".join(
            (self.route.value, self.record_id, str(self.record_version))
        ).encode("utf-8")
        return "phase3:" + hashlib.sha256(material).hexdigest()


@dataclass(frozen=True)
class V3ManifestReadback:
    """The signed, deidentified V5 artifact bound to one Bitable export row."""

    export_record_id: str
    opaque_task_id: str
    event_id: str
    payload_hash: str
    manifest_hash: str
    signer_key_id: str
    signature: str

    def __post_init__(self) -> None:
        _require_compact_identifier(self.export_record_id, "export_record_id")
        _require_pattern(self.opaque_task_id, _V3_TASK_ID_PATTERN, "opaque_task_id")
        _require_compact_identifier(self.event_id, "event_id")
        _require_hash(self.payload_hash, "payload_hash")
        _require_hash(self.manifest_hash, "manifest_hash")
        _require_compact_identifier(self.signer_key_id, "signer_key_id")
        _require_compact_identifier(self.signature, "signature")


@dataclass(frozen=True)
class CompassReceipt:
    """The signed Compass response over one exact V5 artifact."""

    opaque_task_id: str
    event_id: str
    payload_hash: str
    manifest_hash: str
    receipt_hash: str
    signer_key_id: str
    signature: str

    def __post_init__(self) -> None:
        _require_pattern(self.opaque_task_id, _V3_TASK_ID_PATTERN, "opaque_task_id")
        _require_compact_identifier(self.event_id, "event_id")
        _require_hash(self.payload_hash, "payload_hash")
        _require_hash(self.manifest_hash, "manifest_hash")
        _require_hash(self.receipt_hash, "receipt_hash")
        _require_compact_identifier(self.signer_key_id, "signer_key_id")
        _require_compact_identifier(self.signature, "signature")


@runtime_checkable
class ReceiptSignatureVerifier(Protocol):
    """Trust-store adapter; no signing key or raw artifact belongs in this module."""

    def verify_v5_manifest(self, artifact: V3ManifestReadback) -> bool: ...

    def verify_compass_receipt(
        self,
        artifact: V3ManifestReadback,
        receipt: CompassReceipt,
    ) -> bool: ...


@dataclass(frozen=True)
class RepairReferenceReadback:
    """Internal lookup result for a mentor-issued opaque repair reference."""

    repair_reference: str
    expert_scope_handle: str
    bound_expert_record_id: str
    predecessor_submission_record_id: str
    predecessor_business_status: str
    expires_at: datetime
    state: RepairReferenceState
    claimed_by_submission_record_id: str | None = None

    def __post_init__(self) -> None:
        _require_pattern(
            self.repair_reference,
            _REPAIR_REFERENCE_PATTERN,
            "repair_reference",
        )
        _require_pattern(
            self.expert_scope_handle,
            _MENTOR_EXPERT_HANDLE_PATTERN,
            "expert_scope_handle",
        )
        _require_compact_identifier(self.bound_expert_record_id, "bound_expert_record_id")
        _require_compact_identifier(
            self.predecessor_submission_record_id,
            "predecessor_submission_record_id",
        )
        if self.predecessor_business_status not in {"需返修", "repair_required"}:
            raise ValueError("predecessor must be in repair_required state")
        _require_aware_datetime(self.expires_at, "expires_at")
        if not isinstance(self.state, RepairReferenceState):
            raise ValueError("state must be a RepairReferenceState")
        if self.claimed_by_submission_record_id is not None:
            _require_compact_identifier(
                self.claimed_by_submission_record_id,
                "claimed_by_submission_record_id",
            )
        if (
            self.state is RepairReferenceState.USED
            and self.claimed_by_submission_record_id is None
        ):
            raise ValueError("used repair reference requires a claimed submission")
        if (
            self.state is not RepairReferenceState.USED
            and self.claimed_by_submission_record_id is not None
        ):
            raise ValueError("only a used repair reference may have a claim")


@dataclass(frozen=True)
class AuthorizedRevisionLink:
    """A controlled self-link from a new submission to its repair predecessor."""

    envelope: BitableEventEnvelope
    repair_reference: str
    successor_submission_record_id: str
    revision_of_record_id: str

    @property
    def idempotency_key(self) -> str:
        return self.envelope.idempotency_key


@dataclass(frozen=True)
class EligibleQuestionReadback:
    """The minimum Bitable read-back needed to link one interaction attempt."""

    question_record_id: str
    expert_record_id: str
    question_state: str

    def __post_init__(self) -> None:
        _require_compact_identifier(self.question_record_id, "question_record_id")
        _require_compact_identifier(self.expert_record_id, "expert_record_id")
        if self.question_state != "eligible_for_interaction":
            raise ValueError("question_state must be eligible_for_interaction")


@dataclass(frozen=True)
class AuthorizedCanonicalMutation:
    """A mutation proposal that a Nautilus adapter may execute and read back."""

    envelope: BitableEventEnvelope
    target_table: CanonicalTable
    target_record_id: str
    updates: Mapping[str, Any]

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, BitableEventEnvelope):
            raise ValueError("envelope must be a BitableEventEnvelope")
        if not isinstance(self.target_table, CanonicalTable):
            raise ValueError("target_table must be a CanonicalTable")
        _require_compact_identifier(self.target_record_id, "target_record_id")
        if not isinstance(self.updates, Mapping) or not self.updates:
            raise ValueError("updates must be a non-empty mapping")
        object.__setattr__(self, "updates", MappingProxyType(dict(self.updates)))

    @property
    def idempotency_key(self) -> str:
        return self.envelope.idempotency_key


def authorize_canonical_mutation(
    *,
    actor: AppRole,
    envelope: BitableEventEnvelope,
    target_table: CanonicalTable,
    target_record_id: str,
    updates: Mapping[str, Any],
) -> AuthorizedCanonicalMutation:
    """Authorize a narrow post-form Bitable update for Nautilus only.

    The caller still has to perform Bitable read-back before and after the
    write.  The Mentor cannot call this gate, and the native Form ingress is
    deliberately outside it because Feishu owns that initial row creation.
    """

    if actor is not AppRole.NAUTILUS:
        raise PermissionError("only Nautilus may authorize canonical Bitable mutations")
    if not isinstance(envelope, BitableEventEnvelope):
        raise ValueError("envelope must be a BitableEventEnvelope")
    if not isinstance(target_table, CanonicalTable):
        raise ValueError("target_table must be a CanonicalTable")
    _require_compact_identifier(target_record_id, "target_record_id")
    if not isinstance(updates, Mapping) or not updates:
        raise ValueError("updates must be a non-empty mapping")

    allowed_by_table = _MUTABLE_FIELDS_BY_ROUTE[envelope.route]
    allowed_fields = allowed_by_table.get(target_table)
    if allowed_fields is None:
        raise PermissionError(
            f"{envelope.route.value} may not mutate {target_table.value}"
        )
    unknown_fields = sorted(set(updates) - allowed_fields)
    if unknown_fields:
        raise PermissionError(
            "route is not approved to mutate fields: " + ", ".join(unknown_fields)
        )
    if (
        target_table
        in {
            CanonicalTable.TASK_SUBMISSION,
            CanonicalTable.QUESTION_PRECHECK,
            CanonicalTable.INTERACTION_RESULT,
        }
        and target_record_id != envelope.record_id
    ):
        raise ValueError("task mutation must target the event record identity")
    if "工作流配置" in updates and updates["工作流配置"] != PHASE3_WORKFLOW_PROFILE:
        raise ValueError("workflow profile must be phase3_interactive")

    return AuthorizedCanonicalMutation(
        envelope=envelope,
        target_table=target_table,
        target_record_id=target_record_id,
        updates=updates,
    )


def authorize_question_interaction_link(
    *,
    actor: AppRole,
    envelope: BitableEventEnvelope,
    eligible_question: EligibleQuestionReadback,
) -> AuthorizedCanonicalMutation:
    """Create internal interaction relations from a verified eligible question.

    The caller supplies no relation identifiers.  Both targets are resolved by
    Nautilus from the question and interaction read-backs, keeping the Mentor,
    Form client and automation extension outside this mutation boundary.
    """

    if actor is not AppRole.NAUTILUS:
        raise PermissionError("only Nautilus may link question and interaction records")
    if not isinstance(envelope, BitableEventEnvelope):
        raise ValueError("envelope must be a BitableEventEnvelope")
    if envelope.route is not RuntimeRoute.INTERACTION_SUBMITTED:
        raise ValueError("question interaction link requires interaction_submitted")
    if not isinstance(eligible_question, EligibleQuestionReadback):
        raise ValueError("eligible_question must be an EligibleQuestionReadback")
    if envelope.record_id == eligible_question.question_record_id:
        raise ValueError("interaction record must differ from root question")

    return authorize_canonical_mutation(
        actor=actor,
        envelope=envelope,
        target_table=CanonicalTable.INTERACTION_RESULT,
        target_record_id=envelope.record_id,
        updates={
            "工作流配置": PHASE3_WORKFLOW_PROFILE,
            "题目关联": [eligible_question.question_record_id],
            "专家关联": [eligible_question.expert_record_id],
            "交互状态": "interaction_qc_running",
            "自动P0状态": "待运行",
        },
    )


def authorize_revision_link(
    *,
    actor: AppRole,
    envelope: BitableEventEnvelope,
    expert_scope_handle: str,
    authenticated_expert_record_id: str,
    repair_reference: str,
    predecessor: RepairReferenceReadback,
    now: datetime,
) -> AuthorizedRevisionLink:
    """Authorize a self-link only for the owner of a repair reference.

    The adapter must obtain ``predecessor`` by Bitable read-back. The opaque
    reference is safe to send to the expert, while the record identities remain
    inside Nautilus and are never returned to the Mentor.
    """

    if actor is not AppRole.NAUTILUS:
        raise PermissionError("only Nautilus may authorize revision lineage")
    if not isinstance(envelope, BitableEventEnvelope):
        raise ValueError("envelope must be a BitableEventEnvelope")
    if envelope.route is not RuntimeRoute.SUBMISSION_CREATED:
        raise ValueError("revision lineage requires submission_created")
    _require_pattern(
        expert_scope_handle,
        _MENTOR_EXPERT_HANDLE_PATTERN,
        "expert_scope_handle",
    )
    _require_compact_identifier(
        authenticated_expert_record_id,
        "authenticated_expert_record_id",
    )
    _require_pattern(repair_reference, _REPAIR_REFERENCE_PATTERN, "repair_reference")
    if not isinstance(predecessor, RepairReferenceReadback):
        raise ValueError("predecessor must be a RepairReferenceReadback")
    if repair_reference != predecessor.repair_reference:
        raise PermissionError("repair_reference does not match predecessor")
    if expert_scope_handle != predecessor.expert_scope_handle:
        raise PermissionError("repair reference does not belong to this expert")
    if authenticated_expert_record_id != predecessor.bound_expert_record_id:
        raise PermissionError("repair reference does not belong to the bound expert")
    if envelope.record_id == predecessor.predecessor_submission_record_id:
        raise ValueError("revision successor must be a new submission record")
    _require_aware_datetime(now, "now")
    if predecessor.state is RepairReferenceState.USED:
        if predecessor.claimed_by_submission_record_id != envelope.record_id:
            raise PermissionError("repair reference is already claimed")
    elif predecessor.state is RepairReferenceState.EXPIRED or now >= predecessor.expires_at:
        raise PermissionError("repair reference is expired")
    elif predecessor.state is not RepairReferenceState.ACTIVE:
        raise PermissionError("repair reference is not active")

    return AuthorizedRevisionLink(
        envelope=envelope,
        repair_reference=repair_reference,
        successor_submission_record_id=envelope.record_id,
        revision_of_record_id=predecessor.predecessor_submission_record_id,
    )


def authorize_compass_receipt_write(
    *,
    actor: AppRole,
    envelope: BitableEventEnvelope,
    artifact: V3ManifestReadback,
    receipt: CompassReceipt,
    verifier: ReceiptSignatureVerifier,
) -> AuthorizedCanonicalMutation:
    """Verify a receipt against one V5 artifact before Nautilus can write it."""

    if actor is not AppRole.NAUTILUS:
        raise PermissionError("only Nautilus may write a verified Compass receipt")
    if not isinstance(envelope, BitableEventEnvelope):
        raise ValueError("envelope must be a BitableEventEnvelope")
    if envelope.route is not RuntimeRoute.COMPASS_RECEIPT_RECORDED:
        raise ValueError("Compass receipt write requires compass_receipt_recorded")
    if not isinstance(artifact, V3ManifestReadback):
        raise ValueError("artifact must be a V3ManifestReadback")
    if not isinstance(receipt, CompassReceipt):
        raise ValueError("receipt must be a CompassReceipt")
    if not isinstance(verifier, ReceiptSignatureVerifier):
        raise ValueError("verifier must implement ReceiptSignatureVerifier")
    if envelope.record_id != artifact.export_record_id:
        raise ValueError("Compass receipt must target the bound export record")
    _require_receipt_binding(artifact, receipt)
    if verifier.verify_v5_manifest(artifact) is not True:
        raise PermissionError("V5 manifest signature verification failed")
    if verifier.verify_compass_receipt(artifact, receipt) is not True:
        raise PermissionError("Compass receipt signature verification failed")
    return authorize_canonical_mutation(
        actor=actor,
        envelope=envelope,
        target_table=CanonicalTable.EXPORT_RECEIPT,
        target_record_id=artifact.export_record_id,
        updates={
            "导出状态": "已回执",
            "compass_receipt_hash": receipt.receipt_hash,
            "Compass签名键ID": receipt.signer_key_id,
            "回执幂等键": envelope.idempotency_key,
        },
    )


@dataclass(frozen=True)
class MentorProjection:
    """The complete external-facing payload for one authenticated expert."""

    expert_scope_handle: str
    task_handle: str
    p0_disposition: str
    next_action: str
    reason_codes: tuple[str, ...]
    repair_guidance: str
    knowledge_pack_version: str
    lessons: tuple[tuple[str, str, str], ...]
    repair_reference: str | None = None
    human_interaction_ref_hash: str | None = None
    continuation_action: MentorContinuationAction | None = None

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "expert_scope_handle": self.expert_scope_handle,
            "p0_disposition": self.p0_disposition,
            "next_action": self.next_action,
            "reason_codes": list(self.reason_codes),
            "repair_guidance": self.repair_guidance,
            "knowledge_pack_version": self.knowledge_pack_version,
            "lessons": [
                {"lesson_id": lesson_id, "category": category, "guidance": guidance}
                for lesson_id, category, guidance in self.lessons
            ],
        }
        if self.continuation_action is None:
            payload["task_handle"] = self.task_handle
        else:
            payload["continuation"] = self.continuation_action.to_mentor_payload()
        if self.human_interaction_ref_hash is not None:
            payload["human_interaction_ref_hash"] = self.human_interaction_ref_hash
        if self.repair_reference is not None:
            payload["repair_reference"] = self.repair_reference
        return payload

    def to_workbench_payload(self) -> dict[str, Any]:
        """Return expert-safe UI state without internal handles or reason codes."""

        from services.fde_phase3_t1_workbench_contract import (
            legacy_workbench_projection,
        )

        workbench = legacy_workbench_projection(
            p0_disposition=self.p0_disposition,
            reason_codes=self.reason_codes,
            repair_guidance=self.repair_guidance,
            has_continuation=self.continuation_action is not None,
        )
        payload = workbench.to_payload()
        primary_action = payload["primary_action"]
        if not isinstance(primary_action, dict):
            raise RuntimeError("workbench primary action is invalid")
        if self.continuation_action is not None:
            primary_action["continuation"] = self.continuation_action.to_mentor_payload()
        elif self.repair_reference is not None:
            primary_action["continuation_reference"] = self.repair_reference
        return payload


def build_mentor_projection(
    *,
    guidance: MentorTaskGuidance,
    expert_scope_handle: str,
    task_handle: str,
    repair_reference: str | None = None,
    human_interaction_ref_hash: str | None = None,
    continuation_action: MentorContinuationAction | None = None,
) -> MentorProjection:
    """Remove record identities and raw evidence before a Mentor response."""

    if not isinstance(guidance, MentorTaskGuidance):
        raise ValueError("guidance must be a MentorTaskGuidance")
    _require_pattern(
        expert_scope_handle,
        _MENTOR_EXPERT_HANDLE_PATTERN,
        "expert_scope_handle",
    )
    _require_pattern(task_handle, _MENTOR_TASK_HANDLE_PATTERN, "task_handle")
    if task_handle != guidance.task_handle:
        raise PermissionError("task handle must match the guidance scope")
    if continuation_action is not None and not isinstance(
        continuation_action,
        MentorContinuationAction,
    ):
        raise ValueError("continuation_action must be a MentorContinuationAction")
    if (
        continuation_action is not None
        and guidance.continuation_action is not None
        and continuation_action != guidance.continuation_action
    ):
        raise ValueError("continuation_action must match guidance when both are supplied")
    if guidance.p0_disposition.value == "repair_required":
        if repair_reference is None:
            raise ValueError("repair_reference is required for repair guidance")
        _require_pattern(repair_reference, _REPAIR_REFERENCE_PATTERN, "repair_reference")
    elif repair_reference is not None:
        raise ValueError("repair_reference is only valid for repair guidance")
    _require_optional_hash(human_interaction_ref_hash, "human_interaction_ref_hash")
    _require_redacted_text(guidance.repair_guidance, "repair_guidance")

    lessons: list[tuple[str, str, str]] = []
    for lesson in guidance.lessons:
        _require_redacted_text(lesson.guidance, f"lesson {lesson.lesson_id}")
        lessons.append((lesson.lesson_id, lesson.category, lesson.guidance))

    return MentorProjection(
        expert_scope_handle=expert_scope_handle,
        task_handle=task_handle,
        p0_disposition=guidance.p0_disposition.value,
        next_action=guidance.next_action,
        reason_codes=guidance.reason_codes,
        repair_guidance=guidance.repair_guidance,
        knowledge_pack_version=guidance.knowledge_pack_version,
        lessons=tuple(lessons),
        repair_reference=repair_reference,
        human_interaction_ref_hash=human_interaction_ref_hash,
        continuation_action=continuation_action or guidance.continuation_action,
    )


@dataclass(frozen=True)
class V5EligibleProjection:
    """Minimal deidentified input allowed to enter V5's v3 exporter."""

    opaque_task_id: str
    p0_state: str
    feedback_class_code: str
    verdict: str
    evidence_hash: str
    human_interaction_ref_hash: str | None = None

    def to_payload(self) -> dict[str, str]:
        payload = {
            "task_id": self.opaque_task_id,
            "p0_state": self.p0_state,
            "feedback_class": self.feedback_class_code,
            "verdict": self.verdict,
            "evidence_hash": self.evidence_hash,
        }
        if self.human_interaction_ref_hash is not None:
            payload["human_interaction_ref_hash"] = self.human_interaction_ref_hash
        return payload


def build_v5_eligible_projection(
    *,
    source_event: BitableEventEnvelope,
    export_readback: ExportReadback,
    opaque_task_id: str,
    p0_state: str,
    feedback_class_code: str,
    verdict: str,
    evidence_hash: str,
    human_interaction_ref_hash: str | None = None,
) -> V5EligibleProjection:
    """Build V5 input only after an eligible Bitable read-back.

    This output intentionally has no Bitable record identifier, personal
    identity, attachment, conversation content, share reference, or raw buyer
    feedback.  V5 signs and materializes the downstream v3 event separately.
    """

    if not isinstance(source_event, BitableEventEnvelope):
        raise ValueError("source_event must be a BitableEventEnvelope")
    if source_event.route is not RuntimeRoute.BUYER_FEEDBACK_RECORDED:
        raise ValueError("V5 projection requires buyer_feedback_recorded")
    if not isinstance(export_readback, ExportReadback):
        raise ValueError("export_readback must be an ExportReadback")
    export_readback.assert_eligible()
    _require_pattern(opaque_task_id, _V3_TASK_ID_PATTERN, "opaque_task_id")
    if p0_state != "passed":
        raise ValueError("p0_state must be passed for an eligible V5 projection")
    if feedback_class_code not in {"accepted", "accepted_with_advisory"}:
        raise ValueError("feedback_class_code is not eligible for V5 export")
    if feedback_class_code != export_readback.feedback_class:
        raise ValueError("feedback_class_code must match Bitable export read-back")
    if verdict not in {"Gold", "Repair"}:
        raise ValueError("eligible V5 projection verdict must be Gold or Repair")
    if verdict != export_readback.buyer_verdict:
        raise ValueError("V5 projection verdict must match Bitable buyer verdict")
    if export_readback.is_repair and verdict != "Repair":
        raise ValueError("repair export requires Repair verdict")
    if not export_readback.is_repair and verdict != "Gold":
        raise ValueError("initial accepted export requires Gold verdict")
    _require_hash(evidence_hash, "evidence_hash")
    _require_optional_hash(human_interaction_ref_hash, "human_interaction_ref_hash")

    return V5EligibleProjection(
        opaque_task_id=opaque_task_id,
        p0_state=p0_state,
        feedback_class_code=feedback_class_code,
        verdict=verdict,
        evidence_hash=evidence_hash,
        human_interaction_ref_hash=human_interaction_ref_hash,
    )


def _require_compact_identifier(value: str, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{label} must be a non-empty compact string")


def _require_pattern(value: str, pattern: re.Pattern[str], label: str) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} has an invalid opaque format")


def _require_hash(value: str, label: str) -> None:
    if not isinstance(value, str) or _SHA256_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a sha256 hash")


def _require_aware_datetime(value: datetime, label: str) -> None:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{label} must be a timezone-aware datetime")


def _require_optional_hash(value: str | None, label: str) -> None:
    if value is not None:
        _require_hash(value, label)


def _require_redacted_text(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be non-empty redacted text")
    lowered = value.lower()
    forbidden_markers = (
        "raw_buyer_feedback",
        "buyer_identity",
        "attachment",
        "conversation_transcript",
        "share_url",
        "http://",
        "https://",
        "rec_",
    )
    if any(marker in lowered for marker in forbidden_markers):
        raise ValueError(f"{label} must be redacted")


def _require_receipt_binding(
    artifact: V3ManifestReadback,
    receipt: CompassReceipt,
) -> None:
    for field_name in ("opaque_task_id", "event_id", "payload_hash", "manifest_hash"):
        if getattr(artifact, field_name) != getattr(receipt, field_name):
            raise ValueError(f"Compass receipt {field_name} does not match V5 artifact")
