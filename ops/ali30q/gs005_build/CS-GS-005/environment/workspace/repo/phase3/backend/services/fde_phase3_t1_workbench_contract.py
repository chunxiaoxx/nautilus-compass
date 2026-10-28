"""T1 expert workbench projections and operator gate contracts.

Bitable remains authoritative. This module performs no business-state I/O; it
loads reviewed expert copy and builds redacted UI or operator projections.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import Enum
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
from typing import Any


PROJECT_CODE = "FDE_PHASE3_VERTICAL"
CONTENT_PACK_ENV = "FDE_PHASE3_T1_MICROGUIDES_PATH"
DEFAULT_CONTENT_PACK = (
    Path(__file__).resolve().parents[1] / "resources" / "t1_expert_microguides_v1.json"
)


class ExpertVisibleState(str, Enum):
    ADMISSION_PENDING = "准入审核中"
    ADMISSION_REPAIR = "准入需补充"
    QUESTION_READY = "可开始出题"
    QUESTION_CHECKING = "题目检查中"
    QUESTION_REPAIR = "题目需补充"
    INTERACTION_READY = "可开始交互"
    INTERACTION_IN_PROGRESS = "交互进行中"
    INTERACTION_CHECKING = "交互检查中"
    INTERACTION_REPAIR = "交互需补充"
    BUYER_REVIEW = "甲方审核中"
    REVISION_REQUIRED = "需返修"
    ACCEPTED = "已验收"
    TERMINATED = "已终止"


@dataclass(frozen=True)
class PrimaryAction:
    code: str
    enabled: bool = True


_STATE_ACTIONS = {
    ExpertVisibleState.ADMISSION_PENDING: PrimaryAction("wait_for_notice", False),
    ExpertVisibleState.ADMISSION_REPAIR: PrimaryAction("complete_admission"),
    ExpertVisibleState.QUESTION_READY: PrimaryAction("start_question"),
    ExpertVisibleState.QUESTION_CHECKING: PrimaryAction("wait_for_question_review", False),
    ExpertVisibleState.QUESTION_REPAIR: PrimaryAction("revise_question"),
    ExpertVisibleState.INTERACTION_READY: PrimaryAction("start_interaction"),
    ExpertVisibleState.INTERACTION_IN_PROGRESS: PrimaryAction("continue_interaction"),
    ExpertVisibleState.INTERACTION_CHECKING: PrimaryAction("wait_for_interaction_review", False),
    ExpertVisibleState.INTERACTION_REPAIR: PrimaryAction("repair_interaction"),
    ExpertVisibleState.BUYER_REVIEW: PrimaryAction("wait_for_buyer", False),
    ExpertVisibleState.REVISION_REQUIRED: PrimaryAction("start_revision"),
    ExpertVisibleState.ACCEPTED: PrimaryAction("view_result"),
    ExpertVisibleState.TERMINATED: PrimaryAction("view_reason"),
}


class ExceptionCategory(str, Enum):
    UID_PERMISSION = "uid_permission"
    FEISHU_ACCOUNT = "feishu_account"
    ATTACHMENT = "attachment"
    TASK_OPERATION = "task_operation"
    STATUS_OR_DUPLICATE = "status_or_duplicate"
    PRIVACY_COMPLIANCE = "privacy_compliance"
    OTHER = "other"


_EXCEPTION_LABELS = {
    ExceptionCategory.UID_PERMISSION: "UID/权限",
    ExceptionCategory.FEISHU_ACCOUNT: "飞书账号",
    ExceptionCategory.ATTACHMENT: "附件上传或访问",
    ExceptionCategory.TASK_OPERATION: "题目或交互操作",
    ExceptionCategory.STATUS_OR_DUPLICATE: "状态或重复提交",
    ExceptionCategory.PRIVACY_COMPLIANCE: "隐私合规",
    ExceptionCategory.OTHER: "其他",
}


def _sequence(pack: Mapping[str, object], key: str) -> tuple[object, ...]:
    value = pack.get(key)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise ValueError(f"{key} must be an array")
    return tuple(value)


def _text(mapping: Mapping[str, object], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{key} is required")
    return value.strip()


@lru_cache(maxsize=1)
def load_t1_microguide_pack() -> dict[str, Any]:
    configured = os.getenv(CONTENT_PACK_ENV)
    path = Path(configured) if configured else DEFAULT_CONTENT_PACK
    raw = path.read_bytes()
    parsed = json.loads(raw.decode("utf-8-sig"))
    if not isinstance(parsed, Mapping):
        raise ValueError("T1 microguide content must be an object")
    pack = dict(parsed)
    if pack.get("contract_version") != "platform-t1-interface-v1":
        raise ValueError("unsupported T1 microguide contract version")
    states = _sequence(pack, "states")
    if len(states) != 13 or any(not isinstance(item, Mapping) for item in states):
        raise ValueError("T1 microguide states are invalid")
    if {_text(item, "status") for item in states} != {
        state.value for state in ExpertVisibleState
    }:
        raise ValueError("T1 microguide states do not match the platform contract")
    expected_counts = {
        "expert_visible_conclusions": 3,
        "p0_feedback_categories": 7,
        "p1_improvement_topics": 9,
        "error_microguides": 13,
    }
    for key, count in expected_counts.items():
        if len(_sequence(pack, key)) != count:
            raise ValueError(f"{key} count does not match the platform contract")
    pack["content_hash"] = hashlib.sha256(raw).hexdigest()
    return pack


def _state_copy(state: ExpertVisibleState) -> Mapping[str, object]:
    for item in _sequence(load_t1_microguide_pack(), "states"):
        if isinstance(item, Mapping) and item.get("status") == state.value:
            return item
    raise ValueError("T1 state copy is unavailable")


def _p0_correction(category: str) -> str:
    for item in _sequence(load_t1_microguide_pack(), "p0_feedback_categories"):
        if isinstance(item, Mapping) and item.get("category") == category:
            return _text(item, "correction")
    raise ValueError("T1 P0 correction is unavailable")


@dataclass(frozen=True)
class VisibleFeedback:
    category: str
    problem: str
    guidance: str
    evidence_hint: str = ""

    def __post_init__(self) -> None:
        for field_name in ("category", "problem", "guidance"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{field_name} is required")

    def to_payload(self) -> dict[str, str]:
        payload = {
            "category": self.category,
            "problem": self.problem,
            "guidance": self.guidance,
        }
        if self.evidence_hint:
            payload["evidence_hint"] = self.evidence_hint
        return payload


@dataclass(frozen=True)
class ExpertWorkbenchProjection:
    state: ExpertVisibleState
    progress_detail: str
    conclusion: str | None = None
    feedback: tuple[VisibleFeedback, ...] = ()
    deadline: str | None = None
    exception_open: bool = False

    def __post_init__(self) -> None:
        if not isinstance(self.state, ExpertVisibleState):
            raise ValueError("state must be an ExpertVisibleState")
        if not isinstance(self.progress_detail, str) or not self.progress_detail.strip():
            raise ValueError("progress_detail is required")
        conclusions = _sequence(load_t1_microguide_pack(), "expert_visible_conclusions")
        if self.conclusion is not None and self.conclusion not in conclusions:
            raise ValueError("conclusion is not approved for expert display")
        if any(not isinstance(item, VisibleFeedback) for item in self.feedback):
            raise ValueError("feedback must contain VisibleFeedback values")

    def to_payload(self) -> dict[str, Any]:
        pack = load_t1_microguide_pack()
        copy = _state_copy(self.state)
        action = _STATE_ACTIONS[self.state]
        return {
            "contract_version": pack["contract_version"],
            "content_hash": pack["content_hash"],
            "project": {"code": PROJECT_CODE, "name": pack["project_name"]},
            "status": {"code": self.state.name.lower(), "label": self.state.value},
            "headline": _text(copy, "headline"),
            "progress_detail": self.progress_detail,
            "explanation": _text(copy, "explanation"),
            "do_not": _text(copy, "do_not"),
            "conclusion": self.conclusion,
            "primary_action": {
                "code": action.code,
                "label": _text(copy, "primary_action"),
                "enabled": action.enabled and not self.exception_open,
            },
            "deadline": self.deadline,
            "feedback": [item.to_payload() for item in self.feedback],
            "exception": {
                "open": self.exception_open,
                "label": "异常处理中" if self.exception_open else None,
            },
            "auxiliary_actions": [
                {"code": "view_progress", "label": "查看进度"},
                {"code": "report_issue", "label": "遇到问题"},
            ],
        }


_REASON_CATEGORY = {
    "required_tool_not_used": "场景或题型不符合",
    "minimum_turns_not_met": "交互证据不完整或不一致",
    "dialogue_images_missing": "交互证据不完整或不一致",
    "trajectory_link_missing": "交互证据不完整或不一致",
    "log_id_missing": "交互证据不完整或不一致",
    "expert_attestation_missing": "信息不完整",
    "confidence_below_threshold": "任务不可执行或不可稳定回答",
}
_REASON_PROBLEM = {
    "required_tool_not_used": "未使用指定的豆包办公任务模式",
    "minimum_turns_not_met": "有效交互不足六轮",
    "dialogue_images_missing": "完整对话截图缺失",
    "trajectory_link_missing": "轨迹或分享链接缺失",
    "log_id_missing": "日志 ID 缺失",
    "expert_attestation_missing": "专家确认缺失",
    "confidence_below_threshold": "任务质量需要继续完善",
}


def visible_feedback_from_reason_codes(
    reason_codes: tuple[str, ...],
    repair_guidance: str,
) -> tuple[VisibleFeedback, ...]:
    visible: list[VisibleFeedback] = []
    seen: set[tuple[str, str]] = set()
    for code in reason_codes:
        category = _REASON_CATEGORY.get(
            code,
            "真实性或来源不足" if code.startswith("evidence_") else "信息不完整",
        )
        problem = _REASON_PROBLEM.get(code, "提交内容需要补充或核对")
        if (category, problem) in seen:
            continue
        visible.append(
            VisibleFeedback(
                category,
                problem,
                repair_guidance.strip() or _p0_correction(category),
            )
        )
        seen.add((category, problem))
    return tuple(visible)


def legacy_workbench_projection(
    *,
    p0_disposition: str,
    reason_codes: tuple[str, ...],
    repair_guidance: str,
    has_continuation: bool,
) -> ExpertWorkbenchProjection:
    conclusions = _sequence(load_t1_microguide_pack(), "expert_visible_conclusions")
    feedback = visible_feedback_from_reason_codes(reason_codes, repair_guidance)
    if has_continuation:
        return ExpertWorkbenchProjection(
            ExpertVisibleState.INTERACTION_READY,
            "题目已锁定，可以开始豆包交互。",
            conclusions[0],  # type: ignore[arg-type]
            feedback,
        )
    if p0_disposition == "repair_required":
        return ExpertWorkbenchProjection(
            ExpertVisibleState.QUESTION_REPAIR,
            "题目检查发现需要补充的内容。",
            conclusions[1],  # type: ignore[arg-type]
            feedback,
        )
    if p0_disposition == "blocked":
        return ExpertWorkbenchProjection(
            ExpertVisibleState.QUESTION_CHECKING,
            "任务已转项目支持处理。",
            conclusions[2],  # type: ignore[arg-type]
            feedback,
            exception_open=True,
        )
    if p0_disposition == "buyer_ready":
        return ExpertWorkbenchProjection(
            ExpertVisibleState.QUESTION_CHECKING,
            "Agent 已完成检查，等待运营确认锁题。",
            conclusions[0],  # type: ignore[arg-type]
            feedback,
        )
    raise ValueError("unsupported P0 disposition")


class OperatorGate(str, Enum):
    QUESTION_LOCK = "question_lock"
    BUYER_SUBMIT = "buyer_submit"


class CheckStatus(str, Enum):
    GREEN = "green"
    AMBER = "amber"
    RED = "red"


_GATE_CHECKS = {
    OperatorGate.QUESTION_LOCK: {
        "identity_permission": "身份和豆包权限有效",
        "question_complete": "题目必填信息完整",
        "attachment_safe": "附件可读、来源清楚且已脱敏",
        "p0_passed": "Agent P0 硬项全部通过",
        "p1_available": "Agent P1 建议已生成",
        "no_open_exception": "没有未处理的身份、合规或系统异常",
    },
    OperatorGate.BUYER_SUBMIT: {
        "question_locked": "根题目已锁定且未变化",
        "minimum_rounds": "有效交互不少于六轮",
        "round_feedback_complete": "每轮点赞或踩、标签和具体理由齐全",
        "evidence_accessible": "截图、轨迹和日志均可访问",
        "evidence_consistent": "交互证据相互对应",
        "interaction_p0_passed": "交互 P0 硬项全部通过",
        "interaction_p1_available": "交互 P1 建议已生成",
        "identity_lineage_valid": "身份、题目关系和返修血缘正确",
        "no_open_exception": "没有未处理的身份、合规或系统异常",
    },
}


@dataclass(frozen=True)
class GateEvidenceCheck:
    code: str
    status: CheckStatus
    evidence: str


@dataclass(frozen=True)
class OperatorGateSummary:
    gate: OperatorGate
    checks: tuple[GateEvidenceCheck, ...]

    def __post_init__(self) -> None:
        expected = set(_GATE_CHECKS[self.gate])
        actual = [check.code for check in self.checks]
        if len(actual) != len(set(actual)) or set(actual) != expected:
            raise ValueError("gate checklist must contain every required check exactly once")

    @property
    def release_allowed(self) -> bool:
        return all(check.status is CheckStatus.GREEN for check in self.checks)

    def to_operator_payload(self) -> dict[str, Any]:
        labels = _GATE_CHECKS[self.gate]
        decisions = ["return", "escalate"]
        if self.release_allowed:
            decisions.insert(0, "release")
        return {
            "gate": self.gate.value,
            "checks": [
                {
                    "code": check.code,
                    "label": labels[check.code],
                    "status": check.status.value,
                    "evidence": check.evidence,
                }
                for check in self.checks
            ],
            "release_allowed": self.release_allowed,
            "allowed_decisions": decisions,
            "release_requires_bitable_readback": True,
        }


def public_interface_contract_payload() -> dict[str, Any]:
    pack = load_t1_microguide_pack()
    states = []
    for state in ExpertVisibleState:
        copy = _state_copy(state)
        action = _STATE_ACTIONS[state]
        states.append(
            {
                "code": state.name.lower(),
                "label": state.value,
                "headline": _text(copy, "headline"),
                "explanation": _text(copy, "explanation"),
                "do_not": _text(copy, "do_not"),
                "primary_action": {
                    "code": action.code,
                    "label": _text(copy, "primary_action"),
                    "enabled": action.enabled,
                },
            }
        )
    return {
        "contract_version": pack["contract_version"],
        "content_hash": pack["content_hash"],
        "project": {"code": PROJECT_CODE, "name": pack["project_name"]},
        "states": states,
        "expert_visible_conclusions": list(_sequence(pack, "expert_visible_conclusions")),
        "p0_feedback_categories": list(_sequence(pack, "p0_feedback_categories")),
        "p1_improvement_topics": list(_sequence(pack, "p1_improvement_topics")),
        "exception_categories": [
            {"code": item.value, "label": _EXCEPTION_LABELS[item]}
            for item in ExceptionCategory
        ],
        "error_microguides": list(_sequence(pack, "error_microguides")),
        "auxiliary_actions": [
            {"code": "view_progress", "label": "查看进度"},
            {"code": "report_issue", "label": "遇到问题"},
        ],
    }
