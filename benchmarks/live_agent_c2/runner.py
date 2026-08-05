"""Deterministic paired scheduling and execution for Compass C2."""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Protocol

from benchmarks.learning_kernel_r0.schema import MemoryView, memory_view_from_mapping
from benchmarks.learning_kernel_r0.selectors import select_views
from benchmarks.poi_gate2.canonical import hash_json

from .providers import ProviderCallError, ProviderCallResult
from .schema import (
    ARMS,
    AttemptEvidence,
    LiveTask,
    PairedEpisode,
    ProviderIdentity,
    attempt_from_mapping,
    pair_from_mapping,
)
from .task_pack import C2TaskPack
from .verifier import response_hash


Clock = Callable[[], datetime]


class ProviderAdapter(Protocol):
    identity: ProviderIdentity

    def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult: ...


@dataclass(frozen=True, slots=True)
class PairAssignment:
    pair_id: str
    task_id: str
    task_pack_hash: str
    provider_identity: ProviderIdentity
    replica: int
    first_arm: str

    @property
    def arm_order(self) -> tuple[str, str]:
        other = "governed" if self.first_arm == "flat" else "flat"
        return self.first_arm, other


@dataclass(frozen=True, slots=True)
class ExecutedArm:
    arm: str
    attempt: AttemptEvidence
    selected_view_ids: tuple[str, ...]
    retry_count: int
    output_text: Optional[str] = field(repr=False)


@dataclass(frozen=True, slots=True)
class PairExecution:
    assignment: PairAssignment
    flat: ExecutedArm
    governed: ExecutedArm
    pair: Optional[PairedEpisode]
    invalid_attempts: tuple[AttemptEvidence, ...]


def schedule_pairs(
    pack: C2TaskPack,
    providers: tuple[ProviderIdentity, ...],
    *,
    replicas: int,
) -> tuple[PairAssignment, ...]:
    _validate_schedule_inputs(pack, providers, replicas)
    assignments: list[PairAssignment] = []
    for provider in sorted(providers, key=lambda item: item.provider_key):
        coordinates = [(task.task_id, replica) for task in pack.tasks for replica in range(replicas)]
        seed = int(
            hash_json(
                {
                    "domain": "compass.live_agent_c2.assignment_seed.v1",
                    "pack_seed": pack.seed,
                    "provider_key": provider.provider_key,
                }
            ).removeprefix("sha256:")[:16],
            16,
        )
        random.Random(seed).shuffle(coordinates)
        for position, (task_id, replica) in enumerate(coordinates):
            first_arm = ARMS[position % len(ARMS)]
            pair_id = _stable_id(
                "c2_pair_",
                {
                    "domain": "compass.live_agent_c2.pair_id.v1",
                    "pack_hash": pack.pack_hash,
                    "provider": provider.provider_key,
                    "replica": replica,
                    "task_id": task_id,
                },
            )
            assignments.append(
                PairAssignment(
                    pair_id,
                    task_id,
                    pack.pack_hash,
                    provider,
                    replica,
                    first_arm,
                )
            )
    return tuple(assignments)


def task_memory_view(task: LiveTask) -> MemoryView:
    if not isinstance(task, LiveTask) or task.protected or task.memory_text is None:
        raise ValueError("task must have a non-protected frozen memory view")
    digest = hash_json(
        {"domain": "compass.live_agent_c2.memory_view.v1", "task_hash": task.task_hash}
    )
    return memory_view_from_mapping(
        {
            "view_id": f"lkr0_view_c2_{digest.removeprefix('sha256:')[:20]}",
            "source_packet_hash": hash_json(
                {
                    "domain": "compass.live_agent_c2.frozen_memory_source.v1",
                    "task_hash": task.task_hash,
                }
            ),
            "route_key": task.route_key,
            "query_class": task.query_class,
            "action_kind": task.action_kind,
            "representation": "distilled",
            "rendered_text": task.memory_text,
            "semantic_score": 1.0,
            "verification_state": "independent_verified",
            "verdict": "success",
            "lifecycle_state": "active",
            "expires_at": None,
        }
    )


def select_task_views(
    task: LiveTask,
    arm: str,
    *,
    candidate_views: Optional[tuple[MemoryView, ...]] = None,
) -> tuple[MemoryView, ...]:
    if not isinstance(task, LiveTask):
        raise TypeError("task must be a LiveTask")
    if arm not in ARMS:
        raise ValueError("arm is unsupported")
    if arm == "flat" or task.protected:
        return ()
    views = (task_memory_view(task),) if candidate_views is None else candidate_views
    if not isinstance(views, tuple):
        raise TypeError("candidate_views must be a tuple")
    context_key = (task.route_key, task.query_class, task.action_kind)
    utility_scores = {(*context_key, view.view_id): 1.0 for view in views}
    selected = select_views(
        "governed",
        views,
        context_key=context_key,
        utility_scores=utility_scores,
        protected_query_classes=frozenset({"protected_noop"}),
        limit=1,
    )
    if len(selected) > 1:
        raise ValueError("governed arm may select at most one view")
    return selected


def build_arm_prompt(task: LiveTask, selected_views: tuple[MemoryView, ...]) -> str:
    if not isinstance(task, LiveTask):
        raise TypeError("task must be a LiveTask")
    if not isinstance(selected_views, tuple) or len(selected_views) > 1:
        raise TypeError("selected_views must be a tuple containing at most one view")
    if any(not isinstance(view, MemoryView) for view in selected_views):
        raise TypeError("selected_views must contain MemoryView values")
    sections = ["Answer with only the requested value. Do not explain or call tools."]
    if selected_views:
        sections.append(f"Verified context:\n{selected_views[0].rendered_text}")
    sections.append(f"Task:\n{task.prompt}")
    return "\n\n".join(sections)


def run_pair(
    assignment: PairAssignment,
    task: LiveTask,
    adapter: ProviderAdapter,
    *,
    timeout_seconds: float,
    max_retries: int,
    clock: Clock = lambda: datetime.now(timezone.utc),
) -> PairExecution:
    _validate_run_inputs(assignment, task, adapter, max_retries, clock)
    arms: dict[str, ExecutedArm] = {}
    invalid_attempts: list[AttemptEvidence] = []
    for order_index, arm in enumerate(assignment.arm_order):
        executed, invalid = _run_arm(
            assignment,
            task,
            adapter,
            arm=arm,
            order_index=order_index,
            timeout_seconds=timeout_seconds,
            max_retries=max_retries,
            clock=clock,
        )
        arms[arm] = executed
        invalid_attempts.extend(invalid)
    pair = _completed_pair(assignment, arms)
    return PairExecution(
        assignment=assignment,
        flat=arms["flat"],
        governed=arms["governed"],
        pair=pair,
        invalid_attempts=tuple(invalid_attempts),
    )


def _run_arm(
    assignment: PairAssignment,
    task: LiveTask,
    adapter: ProviderAdapter,
    *,
    arm: str,
    order_index: int,
    timeout_seconds: float,
    max_retries: int,
    clock: Clock,
) -> tuple[ExecutedArm, tuple[AttemptEvidence, ...]]:
    selected_views = select_task_views(task, arm)
    prompt = build_arm_prompt(task, selected_views)
    prompt_hash = hash_json(
        {"domain": "compass.live_agent_c2.arm_prompt.v1", "prompt": prompt}
    )
    invalid: list[AttemptEvidence] = []
    for retry in range(max_retries + 1):
        attempt_id = _attempt_id(assignment, arm, retry)
        started_at = _timestamp(clock())
        try:
            result = adapter.invoke(prompt, timeout_seconds=timeout_seconds)
            if result.provider_identity != assignment.provider_identity:
                raise ProviderCallError("provider_identity_mismatch")
        except ProviderCallError as error:
            failed = _attempt(
                assignment,
                attempt_id=attempt_id,
                arm=arm,
                order_index=order_index,
                prompt_hash=prompt_hash,
                started_at=started_at,
                result=None,
                error_code=error.reason_code,
            )
            invalid.append(failed)
            continue
        completed = _attempt(
            assignment,
            attempt_id=attempt_id,
            arm=arm,
            order_index=order_index,
            prompt_hash=prompt_hash,
            started_at=started_at,
            result=result,
            error_code=None,
        )
        return (
            ExecutedArm(
                arm=arm,
                attempt=completed,
                selected_view_ids=tuple(view.view_id for view in selected_views),
                retry_count=retry,
                output_text=result.output_text,
            ),
            tuple(invalid),
        )
    final = invalid[-1]
    return (
        ExecutedArm(
            arm=arm,
            attempt=final,
            selected_view_ids=tuple(view.view_id for view in selected_views),
            retry_count=max_retries,
            output_text=None,
        ),
        tuple(invalid),
    )


def _attempt(
    assignment: PairAssignment,
    *,
    attempt_id: str,
    arm: str,
    order_index: int,
    prompt_hash: str,
    started_at: str,
    result: Optional[ProviderCallResult],
    error_code: Optional[str],
) -> AttemptEvidence:
    return attempt_from_mapping(
        {
            "attempt_id": attempt_id,
            "pair_id": assignment.pair_id,
            "task_id": assignment.task_id,
            "arm": arm,
            "order_index": order_index,
            "provider_identity": {
                "provider_id": assignment.provider_identity.provider_id,
                "model_id": assignment.provider_identity.model_id,
                "adapter_kind": assignment.provider_identity.adapter_kind,
                "adapter_version": assignment.provider_identity.adapter_version,
            },
            "prompt_hash": prompt_hash,
            "response_hash": (
                None if result is None else response_hash(result.output_text)
            ),
            "started_at": started_at,
            "latency_ms": 0 if result is None else result.latency_ms,
            "input_tokens": 0 if result is None else result.input_tokens,
            "output_tokens": 0 if result is None else result.output_tokens,
            "estimated_cost_usd": None if result is None else result.estimated_cost_usd,
            "valid": result is not None,
            "error_code": error_code,
        }
    )


def _completed_pair(
    assignment: PairAssignment,
    arms: dict[str, ExecutedArm],
) -> Optional[PairedEpisode]:
    if any(not arms[arm].attempt.valid for arm in ARMS):
        return None
    return pair_from_mapping(
        {
            "pair_id": assignment.pair_id,
            "task_id": assignment.task_id,
            "provider_identity": {
                "provider_id": assignment.provider_identity.provider_id,
                "model_id": assignment.provider_identity.model_id,
                "adapter_kind": assignment.provider_identity.adapter_kind,
                "adapter_version": assignment.provider_identity.adapter_version,
            },
            "replica": assignment.replica,
            "first_arm": assignment.first_arm,
            "flat_attempt_id": arms["flat"].attempt.attempt_id,
            "governed_attempt_id": arms["governed"].attempt.attempt_id,
            "task_pack_hash": assignment.task_pack_hash,
        }
    )


def _attempt_id(assignment: PairAssignment, arm: str, retry: int) -> str:
    return _stable_id(
        "c2_attempt_",
        {
            "arm": arm,
            "domain": "compass.live_agent_c2.attempt_id.v1",
            "pair_id": assignment.pair_id,
            "retry": retry,
        },
    )


def _stable_id(prefix: str, value: object) -> str:
    return prefix + hash_json(value).removeprefix("sha256:")[:24]


def _timestamp(value: datetime) -> str:
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise ValueError("clock must return a timezone-aware datetime")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _validate_schedule_inputs(
    pack: C2TaskPack,
    providers: tuple[ProviderIdentity, ...],
    replicas: int,
) -> None:
    if not isinstance(pack, C2TaskPack):
        raise TypeError("pack must be a C2TaskPack")
    if not isinstance(providers, tuple) or not providers:
        raise ValueError("providers must be a non-empty tuple")
    if any(not isinstance(provider, ProviderIdentity) for provider in providers):
        raise TypeError("providers must contain ProviderIdentity values")
    keys = tuple(provider.provider_key for provider in providers)
    if len(keys) != len(set(keys)):
        raise ValueError("providers must be unique")
    if isinstance(replicas, bool) or not isinstance(replicas, int) or replicas <= 0:
        raise ValueError("replicas must be a positive integer")


def _validate_run_inputs(
    assignment: PairAssignment,
    task: LiveTask,
    adapter: ProviderAdapter,
    max_retries: int,
    clock: Clock,
) -> None:
    if not isinstance(assignment, PairAssignment):
        raise TypeError("assignment must be a PairAssignment")
    if not isinstance(task, LiveTask) or task.task_id != assignment.task_id:
        raise ValueError("task must match assignment task_id")
    if getattr(adapter, "identity", None) != assignment.provider_identity:
        raise ValueError("adapter identity must match assignment provider")
    if isinstance(max_retries, bool) or not isinstance(max_retries, int):
        raise TypeError("max_retries must be zero or one")
    if max_retries not in (0, 1):
        raise ValueError("max_retries must be zero or one")
    if not callable(clock):
        raise TypeError("clock must be callable")


__all__ = [
    "ExecutedArm",
    "PairAssignment",
    "PairExecution",
    "build_arm_prompt",
    "run_pair",
    "schedule_pairs",
    "select_task_views",
    "task_memory_view",
]
