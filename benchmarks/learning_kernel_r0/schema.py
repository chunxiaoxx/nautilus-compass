"""Strict immutable contracts for the Compass Learning Kernel R0 benchmark."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from typing import Any


SELECTORS = (
    "flat",
    "semantic",
    "distilled",
    "contextual_utility",
    "current_poi",
    "governed",
)
INTERVENTIONS = (
    "no_memory",
    "raw",
    "distilled",
    "shuffled",
    "stale",
    "contradictory",
    "poisoned",
)

REPRESENTATIONS = frozenset({"raw", "distilled"})
VERIFICATION_STATES = frozenset({"blocked", "local_only", "independent_verified"})
VERDICTS = frozenset({"success", "failure", "partial", "inconclusive"})
LIFECYCLE_STATES = frozenset({"active", "cooling", "archived"})

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_ID_PATTERN = re.compile(r"lkr0_(?:manifest|view|run|task)_[a-z0-9_]{1,64}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")
_UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?:^|[^a-z])sk-[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"(?:password|passwd|secret|api[_-]?key)\s*[:=]", re.IGNORECASE),
    re.compile(r"[A-Za-z]:[\\/]"),
    re.compile(r"(?:https?|file)://", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class LearningKernelManifest:
    schema_version: str
    manifest_id: str
    selector: str
    intervention: str
    task_hashes: tuple[str, ...]
    experience_hashes: tuple[str, ...]
    protected_query_classes: tuple[str, ...]
    runtime_recommendation: str
    improvement_claim: bool


@dataclass(frozen=True, slots=True)
class MemoryView:
    view_id: str
    source_packet_hash: str
    route_key: str
    query_class: str
    action_kind: str
    representation: str
    rendered_text: str
    semantic_score: float
    verification_state: str
    verdict: str | None
    lifecycle_state: str
    expires_at: str | None = None


@dataclass(frozen=True, slots=True)
class LearningRunResult:
    run_id: str
    task_id: str
    task_hash: str
    query_class: str
    selector: str
    intervention: str
    replica: int
    selected_view_ids: tuple[str, ...]
    success: bool
    first_pass_success: bool
    verifier_code: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float
    result_hash: str


def manifest_from_mapping(raw: Mapping[str, Any]) -> LearningKernelManifest:
    values = _exact_mapping("LearningKernelManifest", raw, LearningKernelManifest)
    _require_literal(
        "schema_version",
        values["schema_version"],
        "compass.learning_kernel.manifest.v1",
    )
    _validate_id("manifest_id", values["manifest_id"], "lkr0_manifest_")
    _validate_enum("selector", values["selector"], frozenset(SELECTORS))
    _validate_enum("intervention", values["intervention"], frozenset(INTERVENTIONS))
    task_hashes = _hash_sequence("task_hashes", values["task_hashes"])
    experience_hashes = _hash_sequence("experience_hashes", values["experience_hashes"])
    protected_query_classes = _token_sequence(
        "protected_query_classes",
        values["protected_query_classes"],
    )
    _require_literal("runtime_recommendation", values["runtime_recommendation"], "flat")
    if values["improvement_claim"] is not False:
        raise ValueError("improvement_claim must be false")
    return LearningKernelManifest(
        schema_version=values["schema_version"],
        manifest_id=values["manifest_id"],
        selector=values["selector"],
        intervention=values["intervention"],
        task_hashes=task_hashes,
        experience_hashes=experience_hashes,
        protected_query_classes=protected_query_classes,
        runtime_recommendation=values["runtime_recommendation"],
        improvement_claim=False,
    )


def memory_view_from_mapping(raw: Mapping[str, Any]) -> MemoryView:
    values = _exact_mapping("MemoryView", raw, MemoryView)
    _validate_id("view_id", values["view_id"], "lkr0_view_")
    _validate_hash("source_packet_hash", values["source_packet_hash"])
    _validate_route("route_key", values["route_key"])
    _validate_token("query_class", values["query_class"])
    _validate_token("action_kind", values["action_kind"])
    _validate_enum("representation", values["representation"], REPRESENTATIONS)
    _validate_safe_text("rendered_text", values["rendered_text"])
    semantic_score = _finite_number("semantic_score", values["semantic_score"])
    _validate_enum(
        "verification_state",
        values["verification_state"],
        VERIFICATION_STATES,
    )
    if values["verdict"] is not None:
        _validate_enum("verdict", values["verdict"], VERDICTS)
    _validate_enum("lifecycle_state", values["lifecycle_state"], LIFECYCLE_STATES)
    if values["expires_at"] is not None:
        _validate_normalized_string("expires_at", values["expires_at"])
    return MemoryView(
        view_id=values["view_id"],
        source_packet_hash=values["source_packet_hash"],
        route_key=values["route_key"],
        query_class=values["query_class"],
        action_kind=values["action_kind"],
        representation=values["representation"],
        rendered_text=values["rendered_text"],
        semantic_score=semantic_score,
        verification_state=values["verification_state"],
        verdict=values["verdict"],
        lifecycle_state=values["lifecycle_state"],
        expires_at=values["expires_at"],
    )


def run_result_from_mapping(raw: Mapping[str, Any]) -> LearningRunResult:
    values = _exact_mapping("LearningRunResult", raw, LearningRunResult)
    _validate_id("run_id", values["run_id"], "lkr0_run_")
    _validate_id("task_id", values["task_id"], "lkr0_task_")
    _validate_hash("task_hash", values["task_hash"])
    _validate_token("query_class", values["query_class"])
    _validate_enum("selector", values["selector"], frozenset(SELECTORS))
    _validate_enum("intervention", values["intervention"], frozenset(INTERVENTIONS))
    replica = _nonnegative_int("replica", values["replica"])
    selected_view_ids = _id_sequence(
        "selected_view_ids",
        values["selected_view_ids"],
        "lkr0_view_",
    )
    success = _strict_bool("success", values["success"])
    first_pass_success = _strict_bool(
        "first_pass_success",
        values["first_pass_success"],
    )
    _validate_token("verifier_code", values["verifier_code"])
    latency_ms = _nonnegative_int("latency_ms", values["latency_ms"])
    input_tokens = _nonnegative_int("input_tokens", values["input_tokens"])
    output_tokens = _nonnegative_int("output_tokens", values["output_tokens"])
    estimated_cost_usd = _finite_number(
        "estimated_cost_usd",
        values["estimated_cost_usd"],
    )
    if estimated_cost_usd < 0:
        raise ValueError("estimated_cost_usd must be non-negative")
    _validate_hash("result_hash", values["result_hash"])
    return LearningRunResult(
        run_id=values["run_id"],
        task_id=values["task_id"],
        task_hash=values["task_hash"],
        query_class=values["query_class"],
        selector=values["selector"],
        intervention=values["intervention"],
        replica=replica,
        selected_view_ids=selected_view_ids,
        success=success,
        first_pass_success=first_pass_success,
        verifier_code=values["verifier_code"],
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        estimated_cost_usd=estimated_cost_usd,
        result_hash=values["result_hash"],
    )


def _exact_mapping(label: str, raw: Mapping[str, Any], schema: type) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be a mapping")
    if any(not isinstance(key, str) for key in raw):
        raise TypeError(f"{label} field names must be strings")
    expected = tuple(field.name for field in fields(schema))
    unknown = set(raw) - set(expected)
    missing = set(expected) - set(raw)
    if unknown:
        raise TypeError(f"unknown {label} fields: {', '.join(sorted(unknown))}")
    if missing:
        raise TypeError(f"missing {label} fields: {', '.join(sorted(missing))}")
    return {name: raw[name] for name in expected}


def _require_literal(name: str, value: Any, expected: str) -> None:
    if value != expected:
        raise ValueError(f"{name} must be {expected}")


def _validate_id(name: str, value: Any, prefix: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError(f"{name} must be a stable {prefix} identifier")
    if _ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a stable {prefix} identifier")


def _validate_enum(name: str, value: Any, allowed: frozenset[str]) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} is unsupported")


def _validate_hash(name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be sha256 followed by 64 lowercase hex characters")


def _validate_token(name: str, value: Any) -> None:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe token")


def _validate_route(name: str, value: Any) -> None:
    if not isinstance(value, str) or _ROUTE_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe route")


def _validate_safe_text(name: str, value: Any) -> None:
    _validate_normalized_string(name, value)
    if any(pattern.search(value) for pattern in _UNSAFE_TEXT_PATTERNS):
        raise ValueError(f"{name} contains unsafe credential, URL, or path material")


def _validate_normalized_string(name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a non-blank normalized string")


def _finite_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite number")
    result = float(value)
    if not math.isfinite(result):
        raise ValueError(f"{name} must be finite")
    return result


def _nonnegative_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")
    return value


def _strict_bool(name: str, value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")
    return value


def _sequence(name: str, raw: Any) -> tuple[Any, ...]:
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes, bytearray)):
        raise TypeError(f"{name} must be a sequence")
    values = tuple(raw)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must not contain duplicates")
    return values


def _hash_sequence(name: str, raw: Any) -> tuple[str, ...]:
    values = _sequence(name, raw)
    if not values:
        raise ValueError(f"{name} must not be empty")
    for value in values:
        _validate_hash(name, value)
    return values


def _token_sequence(name: str, raw: Any) -> tuple[str, ...]:
    values = _sequence(name, raw)
    if not values:
        raise ValueError(f"{name} must not be empty")
    for value in values:
        _validate_token(name, value)
    return values


def _id_sequence(name: str, raw: Any, prefix: str) -> tuple[str, ...]:
    values = _sequence(name, raw)
    for value in values:
        _validate_id(name, value, prefix)
    return values


__all__ = [
    "INTERVENTIONS",
    "SELECTORS",
    "LearningKernelManifest",
    "LearningRunResult",
    "MemoryView",
    "manifest_from_mapping",
    "memory_view_from_mapping",
    "run_result_from_mapping",
]
