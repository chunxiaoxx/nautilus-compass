"""Mentor-scoped interaction continuation without client-side record matching.

The service resolves an opaque continuation to a server-owned binding, checks
the question's current Bitable-derived eligibility, and delegates the actual
write to a controlled gateway. It never returns record identities to the
Mentor page or accepts them from an external caller.
"""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
import re
from typing import Protocol, runtime_checkable

from services.fde_phase3_interaction_contract import (
    InteractionEvidenceSubmission,
    InteractionSubmissionResult,
    MentorInteractionPage,
)
from services.fde_phase3_continuations import (
    ContinuationConsumedError,
    HmacContinuationService,
)


_EXPERT_SCOPE_PATTERN = re.compile(r"mentor_expert_[A-Za-z0-9_-]{1,80}\Z")
_QUESTION_BINDING_PATTERN = re.compile(r"question_binding_[A-Za-z0-9_-]{1,80}\Z")
_ELIGIBLE_QUESTION_STATE = "eligible_for_interaction"


@dataclass(frozen=True)
class MentorInteractionBinding:
    """Internal identity binding used before a controlled interaction creation."""

    question_binding_ref: str
    expert_scope_handle: str
    question_record_id: str
    expert_record_id: str
    question_state: str

    def __post_init__(self) -> None:
        _require_pattern(
            self.question_binding_ref,
            _QUESTION_BINDING_PATTERN,
            "question_binding_ref",
        )
        _require_pattern(
            self.expert_scope_handle,
            _EXPERT_SCOPE_PATTERN,
            "expert_scope_handle",
        )
        for label in (
            "question_record_id",
            "expert_record_id",
            "question_state",
        ):
            _require_compact(getattr(self, label), label)


@runtime_checkable
class MentorInteractionBindingResolver(Protocol):
    """Resolves only a server-issued opaque binding reference."""

    def resolve(
        self,
        *,
        question_binding_ref: str,
    ) -> MentorInteractionBinding | None: ...


@runtime_checkable
class ControlledInteractionSubmitter(Protocol):
    """Creates one Bitable interaction row after current eligibility read-back."""

    def submit(
        self,
        *,
        binding: MentorInteractionBinding,
        evidence: InteractionEvidenceSubmission,
        request_key: str,
    ) -> InteractionSubmissionResult: ...


class MentorContinuationWorkflowService:
    """Concrete implementation of the runtime's opaque continuation contract."""

    def __init__(
        self,
        *,
        continuations: HmacContinuationService,
        bindings: MentorInteractionBindingResolver,
        submitter: ControlledInteractionSubmitter,
        clock: Callable[[], datetime],
    ) -> None:
        if not isinstance(continuations, HmacContinuationService):
            raise ValueError("continuations must be an HmacContinuationService")
        if not isinstance(bindings, MentorInteractionBindingResolver):
            raise ValueError("bindings must implement MentorInteractionBindingResolver")
        if not isinstance(submitter, ControlledInteractionSubmitter):
            raise ValueError("submitter must implement ControlledInteractionSubmitter")
        if not callable(clock):
            raise ValueError("clock must be callable")
        self._continuations = continuations
        self._bindings = bindings
        self._submitter = submitter
        self._clock = clock

    def open(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
    ) -> MentorInteractionPage | None:
        continuation = self._continuations.inspect(
            continuation_reference=continuation_reference,
            expert_scope_handle=expert_scope_handle,
            now=self._now(),
        )
        binding = self._resolve_active_binding(
            question_binding_ref=continuation.question_binding_ref,
            expert_scope_handle=expert_scope_handle,
        )
        if binding is None:
            return None
        return MentorInteractionPage()

    def submit(
        self,
        *,
        expert_scope_handle: str,
        continuation_reference: str,
        evidence: InteractionEvidenceSubmission,
        request_key: str,
    ) -> InteractionSubmissionResult:
        if not isinstance(evidence, InteractionEvidenceSubmission):
            raise ValueError("evidence must be an InteractionEvidenceSubmission")
        _require_compact(request_key, "request_key")
        now = self._now()
        try:
            inspected = self._continuations.inspect(
                continuation_reference=continuation_reference,
                expert_scope_handle=expert_scope_handle,
                now=now,
            )
        except ContinuationConsumedError:
            consumed = self._continuations.consume(
                continuation_reference=continuation_reference,
                expert_scope_handle=expert_scope_handle,
                request_key=request_key,
                now=now,
            )
            binding = self._resolve_active_binding(
                question_binding_ref=consumed.question_binding_ref,
                expert_scope_handle=expert_scope_handle,
            )
        else:
            binding = self._resolve_active_binding(
                question_binding_ref=inspected.question_binding_ref,
                expert_scope_handle=expert_scope_handle,
            )
            if binding is None:
                raise PermissionError("continuation binding cannot be resolved")
            consumed = self._continuations.consume(
                continuation_reference=continuation_reference,
                expert_scope_handle=expert_scope_handle,
                request_key=request_key,
                now=now,
            )
        if binding is None:
            raise PermissionError("continuation binding cannot be resolved")
        if consumed.question_binding_ref != binding.question_binding_ref:
            raise RuntimeError("continuation binding changed during submission")
        result = self._submitter.submit(
            binding=binding,
            evidence=evidence,
            request_key=request_key,
        )
        if not isinstance(result, InteractionSubmissionResult):
            raise RuntimeError("controlled interaction submitter returned an invalid result")
        return result

    def _resolve_active_binding(
        self,
        *,
        question_binding_ref: str,
        expert_scope_handle: str,
    ) -> MentorInteractionBinding | None:
        binding = self._bindings.resolve(question_binding_ref=question_binding_ref)
        if binding is None:
            return None
        if binding.question_binding_ref != question_binding_ref:
            raise RuntimeError("binding resolver returned an inconsistent reference")
        if binding.expert_scope_handle != expert_scope_handle:
            raise PermissionError("continuation scope does not own this binding")
        if binding.question_state != _ELIGIBLE_QUESTION_STATE:
            raise PermissionError("question is not eligible for interaction")
        return binding

    def _now(self) -> datetime:
        now = self._clock()
        if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() is None:
            raise RuntimeError("continuation clock must return a timezone-aware datetime")
        return now


def _require_compact(value: object, label: str) -> None:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() or ord(character) < 32 for character in value)
    ):
        raise ValueError(f"{label} must be a non-empty compact string")


def _require_pattern(value: object, pattern: re.Pattern[str], label: str) -> None:
    if not isinstance(value, str) or pattern.fullmatch(value) is None:
        raise ValueError(f"{label} has an invalid opaque format")
