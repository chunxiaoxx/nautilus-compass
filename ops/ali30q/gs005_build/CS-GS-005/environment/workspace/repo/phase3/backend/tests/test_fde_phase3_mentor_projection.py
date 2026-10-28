from __future__ import annotations

from datetime import datetime, timezone

from services.fde_phase3_continuations import MentorContinuationAction
from services.fde_phase3_feishu_runtime_contract import build_mentor_projection
from services.fde_phase3_mentor_projection import CuratedLesson, MentorTaskGuidance
from services.fde_phase3_single_submission_qc import P0Disposition


def test_mentor_projection_renders_continuation_without_task_or_record_identifier() -> None:
    guidance = MentorTaskGuidance(
        task_handle="mentor_task_001",
        p0_disposition=P0Disposition.BUYER_READY,
        next_action="begin_doubao_office_task",
        reason_codes=(),
        repair_guidance="按任务卡完成豆包办公任务后提交交互成果。",
        knowledge_pack_version="mentor-p3-v2",
        lessons=(
            CuratedLesson(
                lesson_id="office-task",
                category="general",
                guidance="请在豆包办公任务中完成多轮交互并保留必要证据。",
            ),
        ),
    )
    continuation = MentorContinuationAction(
        continuation_reference="mentor_continue_ABCDEFGHIJKLMNOPQRSTUVWXYZ123456",
        expires_at=datetime(2026, 7, 24, 11, tzinfo=timezone.utc),
    )

    payload = build_mentor_projection(
        guidance=guidance,
        expert_scope_handle="mentor_expert_001",
        task_handle="mentor_task_001",
        continuation_action=continuation,
    ).to_payload()

    assert payload["continuation"] == continuation.to_mentor_payload()
    assert "task_handle" not in payload
    assert "record_id" not in str(payload)
