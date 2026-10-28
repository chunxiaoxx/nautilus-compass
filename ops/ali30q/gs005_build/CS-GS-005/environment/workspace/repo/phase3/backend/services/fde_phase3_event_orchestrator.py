"""Idempotent, Bitable-read-back event orchestration for Phase 3.

This module accepts only authenticated metadata envelopes and already-authorized
mutations. It never accepts chat text, arbitrary Bitable updates, attachments,
or buyer material.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from services.fde_phase3_feishu_runtime_contract import (
    AppRole,
    AuthorizedCanonicalMutation,
    BitableEventEnvelope,
    CanonicalTable,
    MentorProjection,
    RuntimeRoute,
)
from services.fde_phase3_question_precheck import require_eligible_question_state


_TWO_STAGE_ROUTE_TABLES = {
    RuntimeRoute.QUESTION_CREATED: CanonicalTable.QUESTION_PRECHECK,
    RuntimeRoute.QUESTION_PRECHECK_COMPLETED: CanonicalTable.QUESTION_PRECHECK,
    RuntimeRoute.INTERACTION_SUBMITTED: CanonicalTable.INTERACTION_RESULT,
}


class EventOrchestrationError(RuntimeError):
    """Base class for fail-closed runtime orchestration errors."""


class StaleEventError(EventOrchestrationError):
    """The Bitable row changed before or failed to change after the mutation."""


class EventInProgressError(EventOrchestrationError):
    """A possibly-written event cannot be replayed without recovery evidence."""


@dataclass(frozen=True)
class AuthenticatedEventEnvelope:
    """Authenticated delivery metadata from the bounded Feishu runtime route."""

    actor: AppRole
    event: BitableEventEnvelope

    def __post_init__(self) -> None:
        if not isinstance(self.actor, AppRole):
            raise ValueError("actor must be an AppRole")
        if not isinstance(self.event, BitableEventEnvelope):
            raise ValueError("event must be a BitableEventEnvelope")


@dataclass(frozen=True)
class BitableRouteReadback:
    """Minimal post-read metadata, without row fields or evidence payloads."""

    table: CanonicalTable
    record_id: str
    record_version: int
    root_question_state: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.table, CanonicalTable):
            raise ValueError("table must be a CanonicalTable")
        if not isinstance(self.record_id, str) or not self.record_id.strip():
            raise ValueError("record_id is required")
        if isinstance(self.record_version, bool) or not isinstance(self.record_version, int):
            raise ValueError("record_version must be a positive integer")
        if self.record_version < 1:
            raise ValueError("record_version must be a positive integer")
        if self.root_question_state is not None and (
            not isinstance(self.root_question_state, str)
            or not self.root_question_state.strip()
        ):
            raise ValueError("root_question_state must be a non-empty string when supplied")


@dataclass(frozen=True)
class ControlledCanonicalWrite:
    """One repository write containing one or more pre-authorized mutations."""

    envelope: BitableEventEnvelope
    mutations: tuple[AuthorizedCanonicalMutation, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.envelope, BitableEventEnvelope):
            raise ValueError("envelope must be a BitableEventEnvelope")
        if not isinstance(self.mutations, tuple) or not self.mutations:
            raise ValueError("mutations must be a non-empty tuple")
        for mutation in self.mutations:
            if not isinstance(mutation, AuthorizedCanonicalMutation):
                raise ValueError("mutations must be AuthorizedCanonicalMutation values")
            if mutation.envelope != self.envelope:
                raise PermissionError("controlled mutation does not match the event envelope")


@dataclass(frozen=True)
class EventRoutePlan:
    """Trusted route planning result that may trigger one controlled write."""

    write: ControlledCanonicalWrite
    mentor_projection: MentorProjection | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.write, ControlledCanonicalWrite):
            raise ValueError("write must be a ControlledCanonicalWrite")
        if self.mentor_projection is not None and not isinstance(
            self.mentor_projection, MentorProjection
        ):
            raise ValueError("mentor_projection must be a MentorProjection")


@dataclass(frozen=True)
class EventHandlingResult:
    """Sanitized result suitable for the runtime API and technical logs."""

    outcome: str


class BitableRouteRepository(Protocol):
    """Read/write adapter that must keep raw Bitable material outside this module."""

    def read_back(self, envelope: BitableEventEnvelope) -> BitableRouteReadback: ...

    def write_controlled(self, write: ControlledCanonicalWrite) -> None: ...


class EventRoutePlanner(Protocol):
    """Route-specific pure rules operating only after the pre-write read-back."""

    def plan(
        self,
        envelope: BitableEventEnvelope,
        readback: BitableRouteReadback,
    ) -> EventRoutePlan: ...


class EventIdempotencyStore(Protocol):
    """Durable reservation store; callers must make acquire atomic in production."""

    def acquire(self, key: str) -> str: ...

    def complete(self, key: str) -> None: ...

    def release_before_write(self, key: str) -> None: ...


class MentorProjectionPublisher(Protocol):
    """Publishes only a redacted expert-scoped projection to the Mentor app."""

    def publish(self, projection: MentorProjection) -> None: ...


class EventOrchestrator:
    """Perform the mandatory read -> controlled write -> read-back transition."""

    def __init__(
        self,
        repository: BitableRouteRepository,
        planner: EventRoutePlanner,
        idempotency: EventIdempotencyStore,
        mentor_publisher: MentorProjectionPublisher,
    ) -> None:
        self._repository = repository
        self._planner = planner
        self._idempotency = idempotency
        self._mentor_publisher = mentor_publisher

    def handle(self, authenticated: AuthenticatedEventEnvelope) -> EventHandlingResult:
        if not isinstance(authenticated, AuthenticatedEventEnvelope):
            raise ValueError("authenticated event envelope is required")
        if authenticated.actor is not AppRole.NAUTILUS:
            raise PermissionError("only Nautilus may process Phase 3 runtime events")

        envelope = authenticated.event
        reservation = self._idempotency.acquire(envelope.idempotency_key)
        if reservation == "completed":
            return EventHandlingResult(outcome="already_processed")
        if reservation != "acquired":
            raise EventInProgressError("event is already in progress or requires recovery")

        write_started = False
        try:
            before = self._repository.read_back(envelope)
            self._assert_pre_write_readback(envelope, before)
            plan = self._planner.plan(envelope, before)
            self._assert_route_plan(envelope, plan)
            write_started = True
            self._repository.write_controlled(plan.write)
            after = self._repository.read_back(envelope)
            self._assert_post_write_readback(before, after)
            if plan.mentor_projection is not None:
                self._mentor_publisher.publish(plan.mentor_projection)
            self._idempotency.complete(envelope.idempotency_key)
        except Exception:
            if not write_started:
                self._idempotency.release_before_write(envelope.idempotency_key)
            raise
        return EventHandlingResult(outcome="written_and_read_back")

    @staticmethod
    def _assert_pre_write_readback(
        envelope: BitableEventEnvelope,
        readback: BitableRouteReadback,
    ) -> None:
        if not isinstance(readback, BitableRouteReadback):
            raise StaleEventError("pre-write read-back is unavailable")
        if readback.record_id != envelope.record_id:
            raise StaleEventError("read-back record identity does not match the event")
        if readback.record_version != envelope.record_version:
            raise StaleEventError("read-back record version is stale")
        expected_table = _TWO_STAGE_ROUTE_TABLES.get(envelope.route)
        if expected_table is not None and readback.table is not expected_table:
            raise StaleEventError(
                f"route {envelope.route.value} expected canonical table {expected_table.value}"
            )
        if envelope.route is RuntimeRoute.INTERACTION_SUBMITTED:
            require_eligible_question_state(readback.root_question_state)

    @staticmethod
    def _assert_route_plan(
        envelope: BitableEventEnvelope,
        plan: EventRoutePlan,
    ) -> None:
        if not isinstance(plan, EventRoutePlan):
            raise ValueError("route planner must return an EventRoutePlan")
        if plan.write.envelope != envelope:
            raise PermissionError("route plan write does not match the event envelope")

    @staticmethod
    def _assert_post_write_readback(
        before: BitableRouteReadback,
        after: BitableRouteReadback,
    ) -> None:
        if not isinstance(after, BitableRouteReadback):
            raise StaleEventError("post-write read-back is unavailable")
        if after.record_id != before.record_id or after.table is not before.table:
            raise StaleEventError("post-write read-back no longer targets the event row")
        if after.record_version <= before.record_version:
            raise StaleEventError("post-write read-back did not advance the record version")
