"""Deterministic Phase 3 P0 routing for one expert submission record.

This module produces an auditable routing recommendation only.  A
``BUYER_READY`` decision means the record has the minimum evidence for the
buyer mapping queue; it never means that the buyer accepted the work.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from services.fde_phase3_single_submission_schema import PHASE3_WORKFLOW_PROFILE


REQUIRED_TOOL_NAME = "豆包办公任务"
MINIMUM_INTERACTION_TURNS = 6
BUYER_READY_CONFIDENCE = 0.85


class P0Disposition(str, Enum):
    """The only automatic routing outcomes permitted before buyer review."""

    BUYER_READY = "buyer_ready"
    REPAIR_REQUIRED = "repair_required"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class SubmissionEvidence:
    """Safe, structured evidence facts read from the submission Bitable row."""

    submission_record_id: str
    expert_record_id: str
    tool_name: str
    turn_count: int
    has_dialogue_images: bool
    has_trajectory_link: bool
    has_log_id: bool
    attested_by_expert: bool
    workflow_profile: str
    task_contract_complete: bool
    scene_tag_match: bool
    authenticity_ok: bool
    safety_ok: bool
    answerable: bool
    dedupe_clear: bool
    all_turns_have_human_feedback_reasons: bool
    trajectory_coherent: bool
    within_submission_deadline: bool
    model_confidence: float
    quality_issue_codes: tuple[str, ...]
    integrity_issue_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.submission_record_id, "submission_record_id")
        _require_identifier(self.expert_record_id, "expert_record_id")
        if not isinstance(self.tool_name, str) or not self.tool_name.strip():
            raise ValueError("tool_name is required")
        if self.workflow_profile != PHASE3_WORKFLOW_PROFILE:
            raise ValueError("workflow_profile must be phase3_interactive")
        if isinstance(self.turn_count, bool) or not isinstance(self.turn_count, int):
            raise ValueError("turn_count must be an integer")
        if self.turn_count < 0:
            raise ValueError("turn_count cannot be negative")
        for field_name in (
            "has_dialogue_images",
            "has_trajectory_link",
            "has_log_id",
            "attested_by_expert",
            "task_contract_complete",
            "scene_tag_match",
            "authenticity_ok",
            "safety_ok",
            "answerable",
            "dedupe_clear",
            "all_turns_have_human_feedback_reasons",
            "trajectory_coherent",
            "within_submission_deadline",
        ):
            if not isinstance(getattr(self, field_name), bool):
                raise ValueError(f"{field_name} must be a boolean")
        if isinstance(self.model_confidence, bool) or not isinstance(
            self.model_confidence, (int, float)
        ):
            raise ValueError("model_confidence must be a number")
        if not 0.0 <= float(self.model_confidence) <= 1.0:
            raise ValueError("model_confidence must be between 0 and 1")
        _require_codes(self.quality_issue_codes, "quality_issue_codes")
        _require_codes(self.integrity_issue_codes, "integrity_issue_codes")


@dataclass(frozen=True)
class P0Decision:
    """A persistent P0 proposal that cannot be mistaken for a buyer verdict."""

    submission_record_id: str
    disposition: P0Disposition
    reason_codes: tuple[str, ...]
    repair_guidance: str
    policy_version: str
    model_confidence: float
    is_buyer_verdict: bool = False

    def __post_init__(self) -> None:
        _require_identifier(self.submission_record_id, "submission_record_id")
        if not isinstance(self.disposition, P0Disposition):
            raise ValueError("disposition must be a P0Disposition")
        _require_codes(self.reason_codes, "reason_codes")
        if not isinstance(self.repair_guidance, str) or not self.repair_guidance.strip():
            raise ValueError("repair_guidance is required")
        if not isinstance(self.policy_version, str) or not self.policy_version.strip():
            raise ValueError("policy_version is required")
        if not 0.0 <= float(self.model_confidence) <= 1.0:
            raise ValueError("model_confidence must be between 0 and 1")
        if self.is_buyer_verdict:
            raise ValueError("P0 cannot create a buyer verdict")


def evaluate_submission(
    evidence: SubmissionEvidence,
    *,
    policy_version: str,
) -> P0Decision:
    """Route a submission using evidence rules before any buyer handoff.

    Integrity flags take priority.  All other gaps are repairable and are
    deliberately expressed as stable reason codes so the Mentor can provide
    versioned, task-specific guidance without exposing raw review material.
    """
    if not isinstance(evidence, SubmissionEvidence):
        raise ValueError("evidence must be a SubmissionEvidence")
    if not isinstance(policy_version, str) or not policy_version.strip():
        raise ValueError("policy_version is required")

    blocked_reasons = list(evidence.integrity_issue_codes)
    if not evidence.safety_ok:
        blocked_reasons.append("safety_check_failed")
    if blocked_reasons:
        return _decision(
            evidence,
            disposition=P0Disposition.BLOCKED,
            reason_codes=tuple(blocked_reasons),
            guidance="提交证据出现完整性或合规风险，已暂缓处理；请联系项目支持确认后再继续。",
            policy_version=policy_version,
        )

    reasons = _repair_reason_codes(evidence)
    if reasons:
        return _decision(
            evidence,
            disposition=P0Disposition.REPAIR_REQUIRED,
            reason_codes=reasons,
            guidance=_repair_guidance(reasons),
            policy_version=policy_version,
        )

    return _decision(
        evidence,
        disposition=P0Disposition.BUYER_READY,
        reason_codes=(),
        guidance="材料已满足自动 P0 的最小证据要求，等待进入买方映射与最终审核。",
        policy_version=policy_version,
    )


def _decision(
    evidence: SubmissionEvidence,
    *,
    disposition: P0Disposition,
    reason_codes: tuple[str, ...],
    guidance: str,
    policy_version: str,
) -> P0Decision:
    return P0Decision(
        submission_record_id=evidence.submission_record_id,
        disposition=disposition,
        reason_codes=reason_codes,
        repair_guidance=guidance,
        policy_version=policy_version,
        model_confidence=float(evidence.model_confidence),
    )


def _repair_reason_codes(evidence: SubmissionEvidence) -> tuple[str, ...]:
    reasons: list[str] = []
    if evidence.tool_name.strip() != REQUIRED_TOOL_NAME:
        reasons.append("required_tool_not_used")
    if evidence.turn_count < MINIMUM_INTERACTION_TURNS:
        reasons.append("minimum_turns_not_met")
    if not evidence.has_dialogue_images:
        reasons.append("dialogue_images_missing")
    if not evidence.has_trajectory_link:
        reasons.append("trajectory_link_missing")
    if not evidence.has_log_id:
        reasons.append("log_id_missing")
    if not evidence.attested_by_expert:
        reasons.append("expert_attestation_missing")
    if not evidence.task_contract_complete:
        reasons.append("task_contract_incomplete")
    if not evidence.scene_tag_match:
        reasons.append("scene_tag_mismatch")
    if not evidence.authenticity_ok:
        reasons.append("authenticity_check_failed")
    if not evidence.answerable:
        reasons.append("answerability_check_failed")
    if not evidence.dedupe_clear:
        reasons.append("dedupe_or_conflict_detected")
    if not evidence.all_turns_have_human_feedback_reasons:
        reasons.append("per_turn_human_feedback_missing")
    if not evidence.trajectory_coherent:
        reasons.append("trajectory_not_coherent")
    if not evidence.within_submission_deadline:
        reasons.append("submission_deadline_missed")
    if evidence.model_confidence < BUYER_READY_CONFIDENCE:
        reasons.append("confidence_below_threshold")
    reasons.extend(evidence.quality_issue_codes)
    return tuple(reasons)


def _repair_guidance(reason_codes: tuple[str, ...]) -> str:
    reason_set = set(reason_codes)
    if reason_set == {"minimum_turns_not_met", "dialogue_images_missing"}:
        return "请在豆包办公任务中完成至少 6 轮有效问答，并补充完整对话截图后重新提交。"

    messages: list[str] = []
    if "required_tool_not_used" in reason_set:
        messages.append("请使用豆包办公任务模式完成交互")
    if "minimum_turns_not_met" in reason_set:
        messages.append("完成至少 6 轮有效问答")
    if "dialogue_images_missing" in reason_set:
        messages.append("补充完整对话截图")
    if "trajectory_link_missing" in reason_set:
        messages.append("补充轨迹链接")
    if "log_id_missing" in reason_set:
        messages.append("补充日志 ID")
    if "expert_attestation_missing" in reason_set:
        messages.append("完成本人确认")
    if "task_contract_incomplete" in reason_set:
        messages.append("补全任务目标、产物、约束和信息来源")
    if "scene_tag_mismatch" in reason_set:
        messages.append("核对题目领域与实际工作场景是否一致")
    if "authenticity_check_failed" in reason_set:
        messages.append("补充可核验且前后一致的业务事实和专业判断")
    if "answerability_check_failed" in reason_set:
        messages.append("补足使任务可完成的输入、约束和交付要求")
    if "dedupe_or_conflict_detected" in reason_set:
        messages.append("消除与已有任务或本次材料之间的重复和冲突")
    if "per_turn_human_feedback_missing" in reason_set:
        messages.append("为每个模型回复补充带理由的人工评价")
    if "trajectory_not_coherent" in reason_set:
        messages.append("让每轮追问围绕上一轮的缺口、决策或产物推进")
    if "submission_deadline_missed" in reason_set:
        messages.append("在开始后 24 小时内完成并提交完整轨迹")
    if "confidence_below_threshold" in reason_set:
        messages.append("补充能证明题目难度和交互价值的材料")
    quality_codes = [
        code
        for code in reason_codes
        if code
        not in {
            "required_tool_not_used",
            "minimum_turns_not_met",
            "dialogue_images_missing",
            "trajectory_link_missing",
            "log_id_missing",
            "expert_attestation_missing",
            "task_contract_incomplete",
            "scene_tag_mismatch",
            "authenticity_check_failed",
            "answerability_check_failed",
            "dedupe_or_conflict_detected",
            "per_turn_human_feedback_missing",
            "trajectory_not_coherent",
            "submission_deadline_missed",
            "confidence_below_threshold",
        }
    ]
    if quality_codes:
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
