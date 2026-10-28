"""Redacted, expert-scoped input contract for the 智涌导师 application.

The Mentor uses curated rules and the requesting expert's own P0 result.  It
does not query the canonical Base as a broad knowledge source and never sees
raw buyer feedback, raw internal QC drafts, other experts' submissions, or
interaction attachments.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
import re
from typing import Protocol, runtime_checkable

from services.fde_phase3_continuations import MentorContinuationAction
from services.fde_phase3_single_submission_qc import (
    P0Decision,
    P0Disposition,
    SubmissionEvidence,
)


_FORBIDDEN_LESSON_MARKERS = (
    "raw_buyer_feedback",
    "buyer_raw_feedback",
    "原始验收",
    "身份证",
    "银行卡",
    "手机号",
    "record_id",
)
_MENTOR_EXPERT_HANDLE_PATTERN = re.compile(r"mentor_expert_[A-Za-z0-9_-]{1,80}\Z")
_MENTOR_TASK_HANDLE_PATTERN = re.compile(r"mentor_task_[A-Za-z0-9_-]{1,80}\Z")


@runtime_checkable
class TaskHandleIssuer(Protocol):
    """Deterministically issue an opaque Mentor handle for one expert/task scope."""

    def issue(self, *, expert_scope_handle: str, submission_record_id: str) -> str: ...


@dataclass(frozen=True)
class HmacTaskHandleIssuer:
    """HMAC-backed issuer; the secret is injected from controlled runtime config."""

    secret: bytes

    def __post_init__(self) -> None:
        if not isinstance(self.secret, bytes) or len(self.secret) < 16:
            raise ValueError("task handle issuer secret must contain at least 16 bytes")

    def issue(self, *, expert_scope_handle: str, submission_record_id: str) -> str:
        _require_pattern(
            expert_scope_handle,
            _MENTOR_EXPERT_HANDLE_PATTERN,
            "expert_scope_handle",
        )
        _require_compact_identifier(submission_record_id, "submission_record_id")
        material = "\x1f".join((expert_scope_handle, submission_record_id)).encode("utf-8")
        digest = hmac.new(self.secret, material, hashlib.sha256).hexdigest()
        return "mentor_task_" + digest


@dataclass(frozen=True)
class CuratedLesson:
    """A reviewed, redacted rule derived from restricted operational inputs."""

    lesson_id: str
    category: str
    guidance: str

    def __post_init__(self) -> None:
        for field_name in ("lesson_id", "category", "guidance"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")
        lowered = self.guidance.lower()
        if any(marker.lower() in lowered for marker in _FORBIDDEN_LESSON_MARKERS):
            raise ValueError("lesson guidance must be redacted")


@dataclass(frozen=True)
class MentorKnowledgePack:
    """Versioned and reviewed instruction material for the Mentor."""

    version: str
    lessons: tuple[CuratedLesson, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.version, str) or not self.version.strip():
            raise ValueError("knowledge pack version is required")
        if not isinstance(self.lessons, tuple) or not self.lessons:
            raise ValueError("knowledge pack must contain curated lessons")
        if any(not isinstance(lesson, CuratedLesson) for lesson in self.lessons):
            raise ValueError("knowledge pack lessons must be CuratedLesson values")
        lesson_ids = [lesson.lesson_id for lesson in self.lessons]
        if len(set(lesson_ids)) != len(lesson_ids):
            raise ValueError("knowledge pack lesson IDs must be unique")


@dataclass(frozen=True)
class MentorTaskGuidance:
    """The only task-specific data the Mentor may return to an expert."""

    task_handle: str
    p0_disposition: P0Disposition
    next_action: str
    reason_codes: tuple[str, ...]
    repair_guidance: str
    knowledge_pack_version: str
    lessons: tuple[CuratedLesson, ...]
    continuation_action: MentorContinuationAction | None = None

    def __post_init__(self) -> None:
        _require_pattern(self.task_handle, _MENTOR_TASK_HANDLE_PATTERN, "task_handle")
        if self.continuation_action is not None and not isinstance(
            self.continuation_action,
            MentorContinuationAction,
        ):
            raise ValueError("continuation_action must be a MentorContinuationAction")


def build_task_guidance(
    *,
    requesting_expert_record_id: str,
    expert_scope_handle: str,
    task_handle_issuer: TaskHandleIssuer,
    submission_evidence: SubmissionEvidence,
    decision: P0Decision,
    knowledge_pack: MentorKnowledgePack,
) -> MentorTaskGuidance:
    """Build a least-privilege response for one authenticated expert.

    The caller must authenticate the requesting expert before invoking this
    function.  A mismatch is denied rather than transformed into a lookup of
    another expert's record.
    """
    if not isinstance(requesting_expert_record_id, str) or not requesting_expert_record_id.strip():
        raise ValueError("requesting expert record ID is required")
    if not isinstance(submission_evidence, SubmissionEvidence):
        raise ValueError("submission_evidence must be a SubmissionEvidence")
    if not isinstance(decision, P0Decision):
        raise ValueError("decision must be a P0Decision")
    if not isinstance(knowledge_pack, MentorKnowledgePack):
        raise ValueError("knowledge_pack must be a MentorKnowledgePack")
    if not isinstance(task_handle_issuer, TaskHandleIssuer):
        raise ValueError("task_handle_issuer must implement TaskHandleIssuer")
    if requesting_expert_record_id != submission_evidence.expert_record_id:
        raise PermissionError("requesting expert does not own this submission")
    if decision.submission_record_id != submission_evidence.submission_record_id:
        raise ValueError("decision does not belong to this submission")

    return MentorTaskGuidance(
        task_handle=task_handle_issuer.issue(
            expert_scope_handle=expert_scope_handle,
            submission_record_id=decision.submission_record_id,
        ),
        p0_disposition=decision.disposition,
        next_action=_next_action(decision.disposition),
        reason_codes=decision.reason_codes,
        repair_guidance=decision.repair_guidance,
        knowledge_pack_version=knowledge_pack.version,
        lessons=_relevant_lessons(knowledge_pack, decision.reason_codes),
    )


def _next_action(disposition: P0Disposition) -> str:
    if disposition is P0Disposition.BUYER_READY:
        return "await_buyer_mapping"
    if disposition is P0Disposition.REPAIR_REQUIRED:
        return "repair_and_resubmit"
    if disposition is P0Disposition.BLOCKED:
        return "contact_project_support"
    raise ValueError("unknown P0 disposition")


def _relevant_lessons(
    knowledge_pack: MentorKnowledgePack,
    reason_codes: tuple[str, ...],
) -> tuple[CuratedLesson, ...]:
    categories = {"general"}
    if any(
        code
        in {
            "required_tool_not_used",
            "minimum_turns_not_met",
            "dialogue_images_missing",
            "trajectory_link_missing",
            "log_id_missing",
            "expert_attestation_missing",
        }
        for code in reason_codes
    ):
        categories.add("interaction_evidence")
    if "confidence_below_threshold" in reason_codes:
        categories.add("quality")
    if reason_codes and all(code not in {"confidence_below_threshold"} for code in reason_codes):
        categories.add("quality")
    if reason_codes and any(code.startswith("evidence_") for code in reason_codes):
        categories.add("integrity")

    selected = tuple(
        lesson for lesson in knowledge_pack.lessons if lesson.category in categories
    )
    return selected or knowledge_pack.lessons


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
