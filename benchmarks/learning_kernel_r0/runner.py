"""Deterministic, provider-free mechanism runner for Learning Kernel R0."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json

from .schema import (
    INTERVENTIONS,
    SELECTORS,
    LearningRunResult,
    MemoryView,
    run_result_from_mapping,
)
from .selectors import PoiScore, select_views
from .utility import UtilityKey


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")
_TASK_ID_PATTERN = re.compile(r"lkr0_task_[a-z0-9_]{1,64}")


@dataclass(frozen=True, slots=True)
class EvaluationTask:
    task_id: str
    task_hash: str
    route_key: str
    action_kind: str

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or _TASK_ID_PATTERN.fullmatch(self.task_id) is None:
            raise ValueError("task_id must be a stable lkr0_task_ identifier")
        _validate_hash("task_hash", self.task_hash)
        if not isinstance(self.route_key, str) or _ROUTE_PATTERN.fullmatch(self.route_key) is None:
            raise ValueError("route_key must be a safe route")
        _validate_token("action_kind", self.action_kind)


@dataclass(frozen=True, slots=True)
class ExecutionRequest:
    task: EvaluationTask
    query_class: str
    selector: str
    intervention: str
    replica: int
    selected_views: tuple[MemoryView, ...]


@dataclass(frozen=True, slots=True)
class ExecutionObservation:
    output_text: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float

    def __post_init__(self) -> None:
        if not isinstance(self.output_text, str) or not self.output_text:
            raise ValueError("output_text must be a non-empty string")
        _nonnegative_int("latency_ms", self.latency_ms)
        _nonnegative_int("input_tokens", self.input_tokens)
        _nonnegative_int("output_tokens", self.output_tokens)
        _nonnegative_number("estimated_cost_usd", self.estimated_cost_usd)


@dataclass(frozen=True, slots=True)
class VerificationObservation:
    success: bool
    first_pass_success: bool
    verifier_code: str

    def __post_init__(self) -> None:
        if not isinstance(self.success, bool):
            raise TypeError("success must be a boolean")
        if not isinstance(self.first_pass_success, bool):
            raise TypeError("first_pass_success must be a boolean")
        _validate_token("verifier_code", self.verifier_code)


ViewProvider = Callable[[EvaluationTask, str, str], tuple[MemoryView, ...]]
Executor = Callable[[ExecutionRequest], ExecutionObservation]
Verifier = Callable[[EvaluationTask, str, ExecutionObservation], VerificationObservation]


def run_mechanism_matrix(
    *,
    tasks: tuple[EvaluationTask, ...],
    query_classes: tuple[str, ...],
    selectors: tuple[str, ...],
    interventions: tuple[str, ...],
    replicas: int,
    view_provider: ViewProvider,
    executor: Executor,
    verifier: Verifier,
    utility_scores: Mapping[UtilityKey, float] | None = None,
    poi_scores: Mapping[str, PoiScore] | None = None,
    protected_query_classes: frozenset[str] = frozenset(),
    selection_limit: int = 1,
) -> tuple[LearningRunResult, ...]:
    """Execute the frozen Cartesian product without shells or provider clients."""

    _validate_axis("tasks", tasks, EvaluationTask, lambda task: task.task_id)
    _validate_axis("query_classes", query_classes, str, lambda value: value)
    _validate_axis("selectors", selectors, str, lambda value: value)
    _validate_axis("interventions", interventions, str, lambda value: value)
    for query_class in query_classes:
        _validate_token("query_class", query_class)
    if any(selector not in SELECTORS for selector in selectors):
        raise ValueError("selectors contains an unsupported selector")
    if any(intervention not in INTERVENTIONS for intervention in interventions):
        raise ValueError("interventions contains an unsupported intervention")
    _positive_int("replicas", replicas)
    _positive_int("selection_limit", selection_limit)
    if not callable(view_provider) or not callable(executor) or not callable(verifier):
        raise TypeError("view_provider, executor, and verifier must be callables")

    results = []
    for task in tasks:
        for query_class in query_classes:
            context_key = (task.route_key, query_class, task.action_kind)
            for selector in selectors:
                for intervention in interventions:
                    views = view_provider(task, query_class, intervention)
                    if not isinstance(views, tuple) or any(
                        not isinstance(view, MemoryView) for view in views
                    ):
                        raise TypeError("view_provider must return a tuple of MemoryView values")
                    selected = select_views(
                        selector,
                        views,
                        context_key=context_key,
                        utility_scores=utility_scores,
                        poi_scores=poi_scores,
                        protected_query_classes=protected_query_classes,
                        limit=selection_limit,
                    )
                    for replica in range(replicas):
                        request = ExecutionRequest(
                            task=task,
                            query_class=query_class,
                            selector=selector,
                            intervention=intervention,
                            replica=replica,
                            selected_views=selected,
                        )
                        observation = executor(request)
                        if not isinstance(observation, ExecutionObservation):
                            raise TypeError("executor must return an ExecutionObservation")
                        verdict = verifier(task, query_class, observation)
                        if not isinstance(verdict, VerificationObservation):
                            raise TypeError("verifier must return a VerificationObservation")
                        results.append(
                            build_run_result(
                                task_id=task.task_id,
                                task_hash=task.task_hash,
                                query_class=query_class,
                                selector=selector,
                                intervention=intervention,
                                replica=replica,
                                selected_view_ids=tuple(view.view_id for view in selected),
                                success=verdict.success,
                                first_pass_success=verdict.first_pass_success,
                                verifier_code=verdict.verifier_code,
                                latency_ms=observation.latency_ms,
                                input_tokens=observation.input_tokens,
                                output_tokens=observation.output_tokens,
                                estimated_cost_usd=observation.estimated_cost_usd,
                            )
                        )
    ordered = tuple(sorted(results, key=lambda row: row.run_id))
    if len({row.run_id for row in ordered}) != len(ordered):
        raise ValueError("matrix produced duplicate run_id values")
    return ordered


def build_run_result(
    *,
    task_id: str,
    task_hash: str,
    query_class: str,
    selector: str,
    intervention: str,
    replica: int,
    selected_view_ids: tuple[str, ...],
    success: bool,
    first_pass_success: bool,
    verifier_code: str,
    latency_ms: int,
    input_tokens: int,
    output_tokens: int,
    estimated_cost_usd: float,
) -> LearningRunResult:
    identity = {
        "task_id": task_id,
        "task_hash": task_hash,
        "query_class": query_class,
        "selector": selector,
        "intervention": intervention,
        "replica": replica,
    }
    run_digest = hash_json(identity).removeprefix("sha256:")[:24]
    preimage = {
        "run_id": f"lkr0_run_{run_digest}",
        **identity,
        "selected_view_ids": selected_view_ids,
        "success": success,
        "first_pass_success": first_pass_success,
        "verifier_code": verifier_code,
        "latency_ms": latency_ms,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "estimated_cost_usd": estimated_cost_usd,
    }
    return run_result_from_mapping({**preimage, "result_hash": hash_json(preimage)})


def result_to_mapping(result: LearningRunResult) -> dict[str, object]:
    if not isinstance(result, LearningRunResult):
        raise TypeError("result must be a LearningRunResult")
    return {
        "run_id": result.run_id,
        "task_id": result.task_id,
        "task_hash": result.task_hash,
        "query_class": result.query_class,
        "selector": result.selector,
        "intervention": result.intervention,
        "replica": result.replica,
        "selected_view_ids": result.selected_view_ids,
        "success": result.success,
        "first_pass_success": result.first_pass_success,
        "verifier_code": result.verifier_code,
        "latency_ms": result.latency_ms,
        "input_tokens": result.input_tokens,
        "output_tokens": result.output_tokens,
        "estimated_cost_usd": result.estimated_cost_usd,
        "result_hash": result.result_hash,
    }


def validate_result_hash(result: LearningRunResult) -> None:
    mapping = result_to_mapping(result)
    supplied = mapping.pop("result_hash")
    if supplied != hash_json(mapping):
        raise ValueError("result_hash does not match the canonical preimage")


def write_result_journal(
    output_dir: Path,
    results: tuple[LearningRunResult, ...],
) -> Path:
    output_dir = Path(output_dir)
    _validate_results(results)
    path = output_dir / "results.jsonl"
    if output_dir.exists() and not output_dir.is_dir():
        raise ValueError("output_dir must be a directory")
    if output_dir.exists():
        unexpected = tuple(item for item in output_dir.iterdir() if item.name != path.name)
        if unexpected:
            raise ValueError("output_dir must be isolated")
    if path.exists():
        existing = read_result_journal(output_dir)
        if existing == results:
            return path
        existing_by_id = {row.run_id: row for row in existing}
        if any(
            row.run_id in existing_by_id and existing_by_id[row.run_id] != row
            for row in results
        ):
            raise ValueError("conflicting run_id already exists in result journal")
        raise ValueError("result journal already contains a different matrix")

    output_dir.mkdir(parents=True, exist_ok=True)
    payload = b"".join(
        canonical_json_bytes(result_to_mapping(row)) + b"\n" for row in results
    )
    with path.open("xb") as stream:
        stream.write(payload)
    return path


def read_result_journal(output_dir: Path) -> tuple[LearningRunResult, ...]:
    path = Path(output_dir) / "results.jsonl"
    if not path.is_file():
        raise FileNotFoundError(path)
    results = []
    for line_number, line in enumerate(path.read_bytes().splitlines(), start=1):
        if not line:
            raise ValueError(f"blank result journal line {line_number}")
        raw = json.loads(line)
        if canonical_json_bytes(raw) != line:
            raise ValueError(f"non-canonical result journal line {line_number}")
        result = run_result_from_mapping(raw)
        validate_result_hash(result)
        results.append(result)
    normalized = tuple(results)
    _validate_results(normalized)
    if tuple(sorted(normalized, key=lambda row: row.run_id)) != normalized:
        raise ValueError("result journal must be sorted by run_id")
    return normalized


def _validate_results(results: tuple[LearningRunResult, ...]) -> None:
    if not isinstance(results, tuple) or not results:
        raise ValueError("results must be a non-empty tuple")
    if any(not isinstance(row, LearningRunResult) for row in results):
        raise TypeError("results must contain LearningRunResult values")
    for result in results:
        validate_result_hash(result)
    run_ids = tuple(row.run_id for row in results)
    if len(set(run_ids)) != len(run_ids):
        raise ValueError("results must contain unique run_id values")
    if tuple(sorted(run_ids)) != run_ids:
        raise ValueError("results must be sorted by run_id")


def _validate_axis(name, values, expected_type, identity) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    if any(not isinstance(value, expected_type) for value in values):
        raise TypeError(f"{name} contains an invalid value")
    identities = tuple(identity(value) for value in values)
    if len(set(identities)) != len(identities):
        raise ValueError(f"{name} must not contain duplicates")


def _validate_hash(name: str, value: object) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a lowercase SHA-256 value")


def _validate_token(name: str, value: object) -> None:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe token")


def _positive_int(name: str, value: object) -> int:
    normalized = _nonnegative_int(name, value)
    if normalized == 0:
        raise ValueError(f"{name} must be positive")
    return normalized


def _nonnegative_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _nonnegative_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a non-negative finite number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{name} must be non-negative and finite")
    return normalized


__all__ = [
    "EvaluationTask",
    "ExecutionObservation",
    "ExecutionRequest",
    "VerificationObservation",
    "build_run_result",
    "read_result_journal",
    "result_to_mapping",
    "run_mechanism_matrix",
    "validate_result_hash",
    "write_result_journal",
]
