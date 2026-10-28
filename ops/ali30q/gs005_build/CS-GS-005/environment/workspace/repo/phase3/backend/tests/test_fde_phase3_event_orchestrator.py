from __future__ import annotations

import pytest

from services.fde_phase3_event_orchestrator import (
    AuthenticatedEventEnvelope,
    BitableRouteReadback,
    ControlledCanonicalWrite,
    EventOrchestrator,
    EventRoutePlan,
    StaleEventError,
)
from services.fde_phase3_feishu_runtime_contract import (
    AppRole,
    BitableEventEnvelope,
    CanonicalTable,
    EligibleQuestionReadback,
    MentorProjection,
    RuntimeRoute,
    authorize_canonical_mutation,
    authorize_question_interaction_link,
)
from services.fde_phase3_single_submission_schema import PHASE3_WORKFLOW_PROFILE


def event(*, actor: AppRole = AppRole.NAUTILUS, version: int = 3) -> AuthenticatedEventEnvelope:
    return AuthenticatedEventEnvelope(
        actor=actor,
        event=BitableEventEnvelope(
            route=RuntimeRoute.SUBMISSION_CREATED,
            record_id="rec_submission_001",
            record_version=version,
            source_event_id="evt_feishu_001",
        ),
    )


class FakeRepository:
    def __init__(
        self,
        *,
        version: int = 3,
        advance_after_write: bool = True,
        table: CanonicalTable = CanonicalTable.TASK_SUBMISSION,
        record_id: str = "rec_submission_001",
        root_question_state: str | None = None,
    ) -> None:
        self.current = BitableRouteReadback(
            table=table,
            record_id=record_id,
            record_version=version,
            root_question_state=root_question_state,
        )
        self.advance_after_write = advance_after_write
        self.read_count = 0
        self.write_count = 0

    def read_back(self, envelope: BitableEventEnvelope) -> BitableRouteReadback:
        assert envelope.record_id == self.current.record_id
        self.read_count += 1
        return self.current

    def write_controlled(self, write: ControlledCanonicalWrite) -> None:
        assert len(write.mutations) == 1
        self.write_count += 1
        if self.advance_after_write:
            self.current = BitableRouteReadback(
                table=self.current.table,
                record_id=self.current.record_id,
                record_version=self.current.record_version + 1,
                root_question_state=self.current.root_question_state,
            )


class FakeIdempotencyStore:
    def __init__(self) -> None:
        self._completed: set[str] = set()
        self._reserved: set[str] = set()

    def acquire(self, key: str) -> str:
        if key in self._completed:
            return "completed"
        if key in self._reserved:
            return "in_progress"
        self._reserved.add(key)
        return "acquired"

    def complete(self, key: str) -> None:
        assert key in self._reserved
        self._reserved.remove(key)
        self._completed.add(key)

    def release_before_write(self, key: str) -> None:
        self._reserved.discard(key)


class FakeProjectionPublisher:
    def __init__(self) -> None:
        self.published: list[MentorProjection] = []

    def publish(self, projection: MentorProjection) -> None:
        self.published.append(projection)


class SubmissionPlanner:
    def __init__(self, *, projection: MentorProjection | None = None) -> None:
        self.projection = projection
        self.calls = 0

    def plan(
        self,
        envelope: BitableEventEnvelope,
        readback: BitableRouteReadback,
    ) -> EventRoutePlan:
        self.calls += 1
        mutation = authorize_canonical_mutation(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            target_table=CanonicalTable.TASK_SUBMISSION,
            target_record_id=readback.record_id,
            updates={
                "工作流配置": PHASE3_WORKFLOW_PROFILE,
                "专家关联": ["rec_expert_001"],
                "业务状态": "自动质检中",
                "自动P0状态": "待运行",
            },
        )
        return EventRoutePlan(
            write=ControlledCanonicalWrite(envelope=envelope, mutations=(mutation,)),
            mentor_projection=self.projection,
        )


def two_stage_event(
    *,
    route: RuntimeRoute,
    record_id: str,
    version: int = 3,
) -> AuthenticatedEventEnvelope:
    return AuthenticatedEventEnvelope(
        actor=AppRole.NAUTILUS,
        event=BitableEventEnvelope(
            route=route,
            record_id=record_id,
            record_version=version,
            source_event_id="evt_two_stage_001",
        ),
    )


class InteractionPlanner:
    def plan(
        self,
        envelope: BitableEventEnvelope,
        readback: BitableRouteReadback,
    ) -> EventRoutePlan:
        mutation = authorize_question_interaction_link(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            eligible_question=EligibleQuestionReadback(
                question_record_id="rec_question_001",
                expert_record_id="rec_expert_001",
                question_state="eligible_for_interaction",
            ),
        )
        return EventRoutePlan(
            write=ControlledCanonicalWrite(envelope=envelope, mutations=(mutation,)),
        )


class QuestionPrecheckPlanner:
    def plan(
        self,
        envelope: BitableEventEnvelope,
        readback: BitableRouteReadback,
    ) -> EventRoutePlan:
        mutation = authorize_canonical_mutation(
            actor=AppRole.NAUTILUS,
            envelope=envelope,
            target_table=CanonicalTable.QUESTION_PRECHECK,
            target_record_id=readback.record_id,
            updates={
                "题目状态": "eligible_for_interaction",
                "自动P0状态": "可开始交互",
                "自动QC置信度": 0.92,
                "自动QC原因": "",
                "自动QC版本": "question-p0-v1",
                "导师下一步": "请在导师任务卡中继续。",
            },
        )
        return EventRoutePlan(
            write=ControlledCanonicalWrite(envelope=envelope, mutations=(mutation,)),
        )


def test_orchestrator_reads_writes_reads_back_and_replays_idempotently() -> None:
    repository = FakeRepository()
    idempotency = FakeIdempotencyStore()
    publisher = FakeProjectionPublisher()
    orchestrator = EventOrchestrator(repository, SubmissionPlanner(), idempotency, publisher)

    first = orchestrator.handle(event())
    replay = orchestrator.handle(event())

    assert first.outcome == "written_and_read_back"
    assert replay.outcome == "already_processed"
    assert repository.write_count == 1
    assert repository.read_count == 2


def test_orchestrator_rejects_stale_versions_before_any_write() -> None:
    repository = FakeRepository(version=4)
    orchestrator = EventOrchestrator(
        repository,
        SubmissionPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    with pytest.raises(StaleEventError, match="record version"):
        orchestrator.handle(event(version=3))

    assert repository.write_count == 0


def test_orchestrator_rejects_non_nautilus_actor_before_readback() -> None:
    repository = FakeRepository()
    planner = SubmissionPlanner()
    orchestrator = EventOrchestrator(
        repository,
        planner,
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    with pytest.raises(PermissionError, match="Nautilus"):
        orchestrator.handle(event(actor=AppRole.MENTOR))

    assert repository.read_count == 0
    assert planner.calls == 0


def test_orchestrator_requires_a_post_write_readback_with_a_new_version() -> None:
    repository = FakeRepository(advance_after_write=False)
    orchestrator = EventOrchestrator(
        repository,
        SubmissionPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    with pytest.raises(StaleEventError, match="post-write"):
        orchestrator.handle(event())

    assert repository.write_count == 1


def test_orchestrator_publishes_only_the_redacted_projection_from_the_route_plan() -> None:
    projection = MentorProjection(
        expert_scope_handle="mentor_expert_001",
        task_handle="mentor_task_001",
        p0_disposition="buyer_ready",
        next_action="await_buyer_mapping",
        reason_codes=(),
        repair_guidance="请等待后续流程通知。",
        knowledge_pack_version="mentor-p3-v1",
        lessons=(),
    )
    publisher = FakeProjectionPublisher()
    orchestrator = EventOrchestrator(
        FakeRepository(),
        SubmissionPlanner(projection=projection),
        FakeIdempotencyStore(),
        publisher,
    )

    orchestrator.handle(event())

    assert publisher.published == [projection]


def test_orchestrator_rejects_interaction_before_eligible_question_readback() -> None:
    repository = FakeRepository(
        table=CanonicalTable.INTERACTION_RESULT,
        record_id="rec_interaction_001",
        root_question_state="question_repair_required",
    )
    orchestrator = EventOrchestrator(
        repository,
        InteractionPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    with pytest.raises(PermissionError, match="eligible_for_interaction"):
        orchestrator.handle(
            two_stage_event(
                route=RuntimeRoute.INTERACTION_SUBMITTED,
                record_id="rec_interaction_001",
            )
        )

    assert repository.write_count == 0


def test_orchestrator_accepts_eligible_interaction_only_on_interaction_table() -> None:
    repository = FakeRepository(
        table=CanonicalTable.INTERACTION_RESULT,
        record_id="rec_interaction_001",
        root_question_state="eligible_for_interaction",
    )
    orchestrator = EventOrchestrator(
        repository,
        InteractionPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    result = orchestrator.handle(
        two_stage_event(
            route=RuntimeRoute.INTERACTION_SUBMITTED,
            record_id="rec_interaction_001",
        )
    )

    assert result.outcome == "written_and_read_back"
    assert repository.write_count == 1


def test_orchestrator_accepts_question_precheck_completion_on_question_table() -> None:
    repository = FakeRepository(
        table=CanonicalTable.QUESTION_PRECHECK,
        record_id="rec_question_001",
    )
    orchestrator = EventOrchestrator(
        repository,
        QuestionPrecheckPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    result = orchestrator.handle(
        two_stage_event(
            route=RuntimeRoute.QUESTION_PRECHECK_COMPLETED,
            record_id="rec_question_001",
        )
    )

    assert result.outcome == "written_and_read_back"
    assert repository.write_count == 1


def test_orchestrator_rejects_question_route_for_the_wrong_canonical_table() -> None:
    repository = FakeRepository(
        table=CanonicalTable.INTERACTION_RESULT,
        record_id="rec_question_001",
    )
    orchestrator = EventOrchestrator(
        repository,
        InteractionPlanner(),
        FakeIdempotencyStore(),
        FakeProjectionPublisher(),
    )

    with pytest.raises(StaleEventError, match="expected canonical table"):
        orchestrator.handle(
            two_stage_event(
                route=RuntimeRoute.QUESTION_CREATED,
                record_id="rec_question_001",
            )
        )

    assert repository.write_count == 0
