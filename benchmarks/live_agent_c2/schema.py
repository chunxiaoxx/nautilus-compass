"""Strict immutable contracts for the Compass C2 live-agent experiment."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from datetime import datetime, timezone
from typing import Any, Optional

from benchmarks.poi_gate2.canonical import hash_json


QUERY_CLASSES = (
    "conflict_resolution",
    "episodic_lookup",
    "procedural_route",
    "protected_noop",
)
ARMS = ("flat", "governed")
VERIFIER_KINDS = ("exact_text", "ordered_steps", "exact_set")
ADAPTER_KINDS = ("cli", "openai_compatible")

_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_ID_PATTERN = re.compile(r"c2_(?:task|attempt|pair)_[a-z0-9_]{1,96}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")
_UTC_RFC3339_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)
_UNSAFE_TEXT_PATTERNS = (
    re.compile(r"(?:^|[^a-z])sk-[A-Za-z0-9_-]+", re.IGNORECASE),
    re.compile(r"(?:password|passwd|secret|api[_-]?key)\s*[:=]", re.IGNORECASE),
    re.compile(r"(?:uid|user[_-]?id|account[_-]?id)\s*[:=]", re.IGNORECASE),
    re.compile(r"[A-Za-z]:[\\/]"),
    re.compile(r"(?:https?|file)://", re.IGNORECASE),
    re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE),
)


@dataclass(frozen=True, slots=True)
class LiveTask:
    task_id: str
    query_class: str
    route_key: str
    action_kind: str
    prompt: str
    memory_text: Optional[str]
    expected_answer: str
    verifier_kind: str
    protected: bool
    prompt_hash: str = field(init=False)
    verifier_policy_hash: str = field(init=False)
    task_hash: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_id("task_id", self.task_id, "c2_task_")
        _validate_enum("query_class", self.query_class, frozenset(QUERY_CLASSES))
        _validate_route("route_key", self.route_key)
        _validate_token("action_kind", self.action_kind)
        _validate_safe_text("prompt", self.prompt)
        _validate_safe_text("expected_answer", self.expected_answer)
        _validate_enum("verifier_kind", self.verifier_kind, frozenset(VERIFIER_KINDS))
        _validate_protected_task(self)
        prompt_hash = hash_json(
            {"domain": "compass.live_agent_c2.prompt.v1", "prompt": self.prompt}
        )
        verifier_policy_hash = hash_json(
            {
                "domain": "compass.live_agent_c2.verifier_policy.v1",
                "expected_answer": self.expected_answer,
                "verifier_kind": self.verifier_kind,
            }
        )
        object.__setattr__(self, "prompt_hash", prompt_hash)
        object.__setattr__(self, "verifier_policy_hash", verifier_policy_hash)
        object.__setattr__(
            self,
            "task_hash",
            hash_json(
                {
                    "domain": "compass.live_agent_c2.task.v1",
                    "task": task_to_mapping(self),
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class ProviderIdentity:
    provider_id: str
    model_id: str
    adapter_kind: str
    adapter_version: str

    def __post_init__(self) -> None:
        _validate_token("provider_id", self.provider_id)
        _validate_route("model_id", self.model_id)
        _validate_enum("adapter_kind", self.adapter_kind, frozenset(ADAPTER_KINDS))
        _validate_token("adapter_version", self.adapter_version)

    @property
    def provider_key(self) -> str:
        return f"{self.provider_id}/{self.model_id}"


@dataclass(frozen=True, slots=True)
class AttemptEvidence:
    attempt_id: str
    pair_id: str
    task_id: str
    arm: str
    order_index: int
    provider_identity: ProviderIdentity
    prompt_hash: str
    response_hash: Optional[str]
    started_at: str
    latency_ms: int
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: Optional[float]
    valid: bool
    error_code: Optional[str]
    attempt_hash: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_id("attempt_id", self.attempt_id, "c2_attempt_")
        _validate_id("pair_id", self.pair_id, "c2_pair_")
        _validate_id("task_id", self.task_id, "c2_task_")
        _validate_enum("arm", self.arm, frozenset(ARMS))
        if self.order_index not in (0, 1) or isinstance(self.order_index, bool):
            raise ValueError("order_index must be 0 or 1")
        if not isinstance(self.provider_identity, ProviderIdentity):
            raise TypeError("provider_identity must be a ProviderIdentity")
        _validate_hash("prompt_hash", self.prompt_hash)
        _validate_timestamp("started_at", self.started_at)
        _validate_nonnegative_int("latency_ms", self.latency_ms)
        _validate_nonnegative_int("input_tokens", self.input_tokens)
        _validate_nonnegative_int("output_tokens", self.output_tokens)
        if self.estimated_cost_usd is not None:
            normalized_cost = _validate_nonnegative_number(
                "estimated_cost_usd", self.estimated_cost_usd
            )
            object.__setattr__(self, "estimated_cost_usd", normalized_cost)
        _validate_attempt_state(self)
        object.__setattr__(self, "attempt_hash", hash_json(attempt_to_mapping(self)))


@dataclass(frozen=True, slots=True)
class PairedEpisode:
    pair_id: str
    task_id: str
    provider_identity: ProviderIdentity
    replica: int
    first_arm: str
    flat_attempt_id: str
    governed_attempt_id: str
    task_pack_hash: str
    pair_hash: str = field(init=False)

    def __post_init__(self) -> None:
        _validate_id("pair_id", self.pair_id, "c2_pair_")
        _validate_id("task_id", self.task_id, "c2_task_")
        if not isinstance(self.provider_identity, ProviderIdentity):
            raise TypeError("provider_identity must be a ProviderIdentity")
        _validate_nonnegative_int("replica", self.replica)
        _validate_enum("first_arm", self.first_arm, frozenset(ARMS))
        _validate_id("flat_attempt_id", self.flat_attempt_id, "c2_attempt_")
        _validate_id("governed_attempt_id", self.governed_attempt_id, "c2_attempt_")
        if self.flat_attempt_id == self.governed_attempt_id:
            raise ValueError("flat and governed attempt_id values must be distinct")
        _validate_hash("task_pack_hash", self.task_pack_hash)
        object.__setattr__(self, "pair_hash", hash_json(pair_to_mapping(self)))


def task_from_mapping(raw: Mapping[str, Any]) -> LiveTask:
    values = _exact_mapping("LiveTask", raw, LiveTask)
    return LiveTask(**values)


def provider_from_mapping(raw: Mapping[str, Any]) -> ProviderIdentity:
    values = _exact_mapping("ProviderIdentity", raw, ProviderIdentity)
    return ProviderIdentity(**values)


def attempt_from_mapping(raw: Mapping[str, Any]) -> AttemptEvidence:
    values = _exact_mapping("AttemptEvidence", raw, AttemptEvidence)
    values["provider_identity"] = provider_from_mapping(values["provider_identity"])
    return AttemptEvidence(**values)


def pair_from_mapping(raw: Mapping[str, Any]) -> PairedEpisode:
    values = _exact_mapping("PairedEpisode", raw, PairedEpisode)
    values["provider_identity"] = provider_from_mapping(values["provider_identity"])
    return PairedEpisode(**values)


def task_to_mapping(task: LiveTask) -> dict[str, Any]:
    if not isinstance(task, LiveTask):
        raise TypeError("task must be a LiveTask")
    return {
        "task_id": task.task_id,
        "query_class": task.query_class,
        "route_key": task.route_key,
        "action_kind": task.action_kind,
        "prompt": task.prompt,
        "memory_text": task.memory_text,
        "expected_answer": task.expected_answer,
        "verifier_kind": task.verifier_kind,
        "protected": task.protected,
    }


def provider_to_mapping(provider: ProviderIdentity) -> dict[str, Any]:
    if not isinstance(provider, ProviderIdentity):
        raise TypeError("provider must be a ProviderIdentity")
    return {
        "provider_id": provider.provider_id,
        "model_id": provider.model_id,
        "adapter_kind": provider.adapter_kind,
        "adapter_version": provider.adapter_version,
    }


def attempt_to_mapping(attempt: AttemptEvidence) -> dict[str, Any]:
    if not isinstance(attempt, AttemptEvidence):
        raise TypeError("attempt must be AttemptEvidence")
    return {
        "attempt_id": attempt.attempt_id,
        "pair_id": attempt.pair_id,
        "task_id": attempt.task_id,
        "arm": attempt.arm,
        "order_index": attempt.order_index,
        "provider_identity": provider_to_mapping(attempt.provider_identity),
        "prompt_hash": attempt.prompt_hash,
        "response_hash": attempt.response_hash,
        "started_at": attempt.started_at,
        "latency_ms": attempt.latency_ms,
        "input_tokens": attempt.input_tokens,
        "output_tokens": attempt.output_tokens,
        "estimated_cost_usd": attempt.estimated_cost_usd,
        "valid": attempt.valid,
        "error_code": attempt.error_code,
    }


def pair_to_mapping(pair: PairedEpisode) -> dict[str, Any]:
    if not isinstance(pair, PairedEpisode):
        raise TypeError("pair must be a PairedEpisode")
    return {
        "pair_id": pair.pair_id,
        "task_id": pair.task_id,
        "provider_identity": provider_to_mapping(pair.provider_identity),
        "replica": pair.replica,
        "first_arm": pair.first_arm,
        "flat_attempt_id": pair.flat_attempt_id,
        "governed_attempt_id": pair.governed_attempt_id,
        "task_pack_hash": pair.task_pack_hash,
    }


def _exact_mapping(label: str, raw: Mapping[str, Any], schema: type) -> dict[str, Any]:
    if not isinstance(raw, Mapping):
        raise TypeError(f"{label} must be a mapping")
    if any(not isinstance(key, str) for key in raw):
        raise TypeError(f"{label} field names must be strings")
    expected = tuple(item.name for item in fields(schema) if item.init)
    unknown = set(raw) - set(expected)
    missing = set(expected) - set(raw)
    if unknown:
        raise TypeError(f"unknown {label} fields: {', '.join(sorted(unknown))}")
    if missing:
        raise TypeError(f"missing {label} fields: {', '.join(sorted(missing))}")
    return {name: raw[name] for name in expected}


def _validate_protected_task(task: LiveTask) -> None:
    if not isinstance(task.protected, bool):
        raise TypeError("protected must be a boolean")
    expected_protected = task.query_class == "protected_noop"
    if task.protected is not expected_protected:
        raise ValueError("protected must be true only for protected_noop tasks")
    if task.protected:
        if task.memory_text is not None:
            raise ValueError("protected_noop memory_text must be null")
        return
    if task.memory_text is None:
        raise ValueError("non-protected memory_text must be present")
    _validate_safe_text("memory_text", task.memory_text)


def _validate_attempt_state(attempt: AttemptEvidence) -> None:
    if not isinstance(attempt.valid, bool):
        raise TypeError("valid must be a boolean")
    if attempt.valid:
        if attempt.response_hash is None or attempt.error_code is not None:
            raise ValueError("valid attempt requires response_hash and no error_code")
        _validate_hash("response_hash", attempt.response_hash)
        return
    if attempt.response_hash is not None or attempt.error_code is None:
        raise ValueError("invalid attempt requires error_code and no response_hash")
    _validate_token("error_code", attempt.error_code)


def _validate_id(name: str, value: Any, prefix: str) -> None:
    if not isinstance(value, str) or not value.startswith(prefix):
        raise ValueError(f"{name} must be a stable {prefix} identifier")
    if _ID_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a stable {prefix} identifier")


def _validate_token(name: str, value: Any) -> None:
    if not isinstance(value, str) or _TOKEN_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe token")


def _validate_route(name: str, value: Any) -> None:
    if not isinstance(value, str) or _ROUTE_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be a safe route")


def _validate_enum(name: str, value: Any, allowed: frozenset[str]) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if value not in allowed:
        raise ValueError(f"{name} is unsupported")


def _validate_safe_text(name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{name} must be a string")
    if not value or value != value.strip():
        raise ValueError(f"{name} must be a non-blank normalized string")
    if any(pattern.search(value) for pattern in _UNSAFE_TEXT_PATTERNS):
        raise ValueError(f"{name} contains unsafe credential, identity, URL, or path material")


def _validate_hash(name: str, value: Any) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be sha256 followed by 64 lowercase hex characters")


def _validate_timestamp(name: str, value: Any) -> None:
    if not isinstance(value, str) or _UTC_RFC3339_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be an RFC3339 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError(f"{name} must be a valid RFC3339 timestamp") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError(f"{name} must be UTC")


def _validate_nonnegative_int(name: str, value: Any) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_nonnegative_number(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{name} must be a finite non-negative number")
    normalized = float(value)
    if not math.isfinite(normalized) or normalized < 0:
        raise ValueError(f"{name} must be a finite non-negative number")
    return normalized


__all__ = [
    "ADAPTER_KINDS",
    "ARMS",
    "QUERY_CLASSES",
    "VERIFIER_KINDS",
    "AttemptEvidence",
    "LiveTask",
    "PairedEpisode",
    "ProviderIdentity",
    "attempt_from_mapping",
    "attempt_to_mapping",
    "pair_from_mapping",
    "pair_to_mapping",
    "provider_from_mapping",
    "provider_to_mapping",
    "task_from_mapping",
    "task_to_mapping",
]
