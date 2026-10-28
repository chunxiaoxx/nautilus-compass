"""Question-only P0 for the Phase 3 Mentor-gated workflow.

This gate decides only whether a question may open a Doubao interaction. It
does not inspect interaction evidence, make a buyer decision, or trigger
export and settlement work.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from services.fde_phase3_single_submission_schema import PHASE3_WORKFLOW_PROFILE


QUESTION_ELIGIBLE_CONFIDENCE = 0.80


class QuestionPrecheckDisposition(str, Enum):
    """The only states that can result from automatic question precheck."""

    ELIGIBLE_FOR_INTERACTION = "eligible_for_interaction"
    REPAIR_REQUIRED = "question_repair_required"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class QuestionPrecheckEvidence:
    """Structured, non-content facts read from one question-precheck row."""

    question_record_id: str
    expert_record_id: str
    workflow_profile: str
    has_question_text: bool
    domain_tags_complete: bool
    supporting_attachment_present: bool
    attachment_source_complete: bool
    followup_interaction_plan_complete: bool
    authenticity_ok: bool
    safety_ok: bool
    answerable: bool
    dedupe_clear: bool
    model_confidence: float
    quality_issue_codes: tuple[str, ...]
    integrity_issue_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.question_record_id, "question_record_id")
        _require_identifier(self.expert_record_id, "expert_record_id")
        if self.workflow_profile != PHASE3_WORKFLOW_PROFILE:
            raise ValueError("workflow_profile must be phase3_interactive")
        for field_name in (
            "has_question_text",
            "domain_tags_complete",
            "supporting_attachment_present",
            "attachment_source_complete",
            "followup_interaction_plan_complete",
            "authenticity_ok",
            "safety_ok",
            "answerable",
            "dedupe_clear",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a boolean")
        if isinstance(self.model_confidence, bool) or not isinstance(
            self.model_confidence,
            (int, float),
        ):
            raise ValueError("model_confidence must be a number")
        if not 0.0 <= float(self.model_confidence) <= 1.0:
            raise ValueError("model_confidence must be between 0 and 1")
        _require_codes(self.quality_issue_codes, "quality_issue_codes")
        _require_codes(self.integrity_issue_codes, "integrity_issue_codes")


@dataclass(frozen=True)
class QuestionPrecheckDecision:
    """A routing recommendation that cannot be mistaken for a buyer verdict."""

    question_record_id: str
    disposition: QuestionPrecheckDisposition
    reason_codes: tuple[str, ...]
    mentor_guidance: str
    policy_version: str
    model_confidence: float
    is_buyer_verdict: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.question_record_id, "question_record_id")
        if not isinstance(self.disposition, QuestionPrecheckDisposition):
            raise ValueError("disposition must be a QuestionPrecheckDisposition")
        _require_codes(self.reason_codes, "reason_codes")
        if not isinstance(self.mentor_guidance, str) or not self.mentor_guidance.strip():
            raise ValueError("mentor_guidance is required")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version is required")
        if not 0.0 <= float(self.model_confidence) <= 1.0:
            raise ValueError("model_confidence must be between 0 and 1")
        if self.is_buyer_verdict:
            raise ValueError("question precheck cannot create a buyer verdict")


def evaluate_question_precheck(
    evidence: QuestionPrecheckEvidence,
    *,
    policy_version: str,
) -> QuestionPrecheckDecision:
    """Route question readiness before any Doubao interaction starts."""

    if not isinstance(evidence, QuestionPrecheckEvidence):
        raise ValueError("evidence must be a QuestionPrecheckEvidence")
    if not isinstance(policy_version, str) or not policy_version.strip():
        raise ValueError("policy_version is required")

    blocked_reasons = list(evidence.integrity_issue_codes)
    if not evidence.safety_ok:
        blocked_reasons.append("safety_check_failed")
    if blocked_reasons:
        return _decision(
            evidence,
            disposition=QuestionPrecheckDisposition.BLOCKED,
            reason_codes=tuple(dict.fromkeys(blocked_reasons)),
            guidance="题目存在完整性或合规风险，已暂缓处理；请联系项目支持确认后再继续。",
            policy_version=policy_version,
        )

    reasons = _repair_reason_codes(evidence)
    if reasons:
        return _decision(
            evidence,
            disposition=QuestionPrecheckDisposition.REPAIR_REQUIRED,
            reason_codes=reasons,
            guidance=_repair_guidance(reasons),
            policy_version=policy_version,
        )

    return _decision(
        evidence,
        disposition=QuestionPrecheckDisposition.ELIGIBLE_FOR_INTERACTION,
        reason_codes=(),
        guidance="题目已通过自动预审，请在导师任务卡中完成豆包办公任务交互。",
        policy_version=policy_version,
    )


def question_precheck_updates(decision: QuestionPrecheckDecision) -> dict[str, object]:
    """Return the narrow internal fields Nautilus may write after read-back."""

    if not isinstance(decision, QuestionPrecheckDecision):
        raise ValueError("decision must be a QuestionPrecheckDecision")
    state, p0_status = {
        QuestionPrecheckDisposition.ELIGIBLE_FOR_INTERACTION: (
            "eligible_for_interaction",
            "可开始交互",
        ),
        QuestionPrecheckDisposition.REPAIR_REQUIRED: (
            "question_repair_required",
            "需返修",
        ),
        QuestionPrecheckDisposition.BLOCKED: ("blocked", "阻断"),
    }[decision.disposition]
    return {
        "题目状态": state,
        "自动P0状态": p0_status,
        "自动QC置信度": decision.model_confidence,
        "自动QC原因": ";".join(decision.reason_codes),
        "自动QC版本": decision.policy_version,
        "导师下一步": decision.mentor_guidance,
    }


def require_eligible_question_state(question_state: str) -> None:
    """Reject interaction work unless the root question was read back eligible."""

    if question_state != QuestionPrecheckDisposition.ELIGIBLE_FOR_INTERACTION.value:
        raise PermissionError("interaction requires eligible_for_interaction question read-back")


def _decision(
    evidence: QuestionPrecheckEvidence,
    *,
    disposition: QuestionPrecheckDisposition,
    reason_codes: tuple[str, ...],
    guidance: str,
    policy_version: str,
) -> QuestionPrecheckDecision:
    return QuestionPrecheckDecision(
        question_record_id=evidence.question_record_id,
        disposition=disposition,
        reason_codes=reason_codes,
        mentor_guidance=guidance,
        policy_version=policy_version,
        model_confidence=float(evidence.model_confidence),
    )


def _repair_reason_codes(evidence: QuestionPrecheckEvidence) -> tuple[str, ...]:
    reasons: list[str] = []
    if not evidence.has_question_text:
        reasons.append("question_text_missing")
    if not evidence.domain_tags_complete:
        reasons.append("domain_tags_incomplete")
    if not evidence.supporting_attachment_present:
        reasons.append("supporting_attachment_missing")
    if not evidence.attachment_source_complete:
        reasons.append("attachment_source_incomplete")
    if not evidence.followup_interaction_plan_complete:
        reasons.append("followup_interaction_plan_missing")
    if not evidence.authenticity_ok:
        reasons.append("authenticity_check_failed")
    if not evidence.answerable:
        reasons.append("answerability_check_failed")
    if not evidence.dedupe_clear:
        reasons.append("dedupe_or_conflict_detected")
    if evidence.model_confidence < QUESTION_ELIGIBLE_CONFIDENCE:
        reasons.append("confidence_below_threshold")
    reasons.extend(evidence.quality_issue_codes)
    return tuple(reasons)


def _repair_guidance(reason_codes: tuple[str, ...]) -> str:
    messages: list[str] = []
    reason_set = set(reason_codes)
    if "question_text_missing" in reason_set:
        messages.append("补全题目、目标和约束")
    if "domain_tags_incomplete" in reason_set:
        messages.append("补全题目领域一级和二级目录")
    if "supporting_attachment_missing" in reason_set:
        messages.append("补充相关附件")
    if "attachment_source_incomplete" in reason_set:
        messages.append("说明附件来源")
    if "followup_interaction_plan_missing" in reason_set:
        messages.append("补全后续交互思路")
    if "authenticity_check_failed" in reason_set:
        messages.append("补充可核验且前后一致的业务事实和专业判断")
    if "answerability_check_failed" in reason_set:
        messages.append("补足完成任务所需的输入、约束和交付要求")
    if "dedupe_or_conflict_detected" in reason_set:
        messages.append("消除与已有题目或本次材料之间的重复和冲突")
    if "confidence_below_threshold" in reason_set:
        messages.append("补充能说明题目难度和交互价值的材料")
    if any(
        code
        not in {
            "question_text_missing",
            "domain_tags_incomplete",
            "supporting_attachment_missing",
            "attachment_source_incomplete",
            "followup_interaction_plan_missing",
            "authenticity_check_failed",
            "answerability_check_failed",
            "dedupe_or_conflict_detected",
            "confidence_below_threshold",
        }
        for code in reason_codes
    ):
        messages.append("按导师提示处理质量问题")
    return "请" + "，并".join(messages) + "后重新提交。"


def _require_identifier(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required")


def _require_codes(value: tuple[str, ...], field_name: str) -> None:
    if not isinstance(value, tuple):
        raise ValueError(f"{field_name} must be a tuple")
    if any(not isinstance(code, str) or not code.strip() for code in value):
        raise ValueError(f"{field_name} must contain non-empty strings")
    if len(set(value)) != len(value):
        raise ValueError(f"{field_name} must not contain duplicates")
