from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from platform_protocol.g2_a0_model_gate import (
    ModelGateContractViolation,
    canonical_json_bytes,
    sha256_hex,
)

MODEL_GATE_POLICY_VERSION_V6 = "g2-a0-model-gate-policy-v6"
MODEL_GATE_REQUEST_VERSION_V6 = "g2-a0-model-gate-request-v6"
MAX_COST_MICROS_CNY_V6 = 10_000_000

_SHA256_RE = re.compile(r"[0-9a-f]{64}")
_IDEMPOTENCY_KEY_RE = re.compile(r"idem_[0-9a-f]{32}")
_POLICY_FIELDS = frozenset(
    {
        "balance_path",
        "completion_path",
        "contract_version",
        "fallback_models",
        "max_cost_micros_cny",
        "max_input_bytes",
        "max_provider_calls",
        "max_tokens",
        "provider_origin",
        "reasoning_effort",
        "requested_model",
        "retry_count",
        "thinking_type",
        "timeout_seconds",
    }
)
_REQUEST_FIELDS = frozenset(
    {
        "contract_version",
        "fixture_hash",
        "idempotency_key",
        "policy",
        "prompt_hash",
        "response_schema_hash",
    }
)


def _violate(code: str) -> None:
    raise ModelGateContractViolation(code)


def _require_exact(value: object, expected: object, field_name: str) -> None:
    if value != expected or type(value) is not type(expected):
        _violate(f"invalid_{field_name}")


def _require_hash(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_fields(
    value: object,
    expected: frozenset[str],
    failure_code: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected:
        _violate(failure_code)
    return value


def _parse_object(data: bytes, failure_code: str) -> Mapping[str, Any]:
    canonical_json_bytes(data)
    value = json.loads(data)
    if not isinstance(value, Mapping):
        _violate(failure_code)
    return value


@dataclass(frozen=True, slots=True)
class DeepSeekModelGatePolicyV6:
    contract_version: str
    provider_origin: str
    balance_path: str
    completion_path: str
    requested_model: str
    thinking_type: str
    reasoning_effort: str
    max_input_bytes: int
    max_tokens: int
    max_provider_calls: int
    max_cost_micros_cny: int
    timeout_seconds: int
    retry_count: int
    fallback_models: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_exact(
            self.contract_version,
            MODEL_GATE_POLICY_VERSION_V6,
            "contract_version",
        )
        _require_exact(
            self.provider_origin,
            "https://api.deepseek.com",
            "provider_origin",
        )
        _require_exact(self.balance_path, "/user/balance", "balance_path")
        _require_exact(self.completion_path, "/chat/completions", "completion_path")
        _require_exact(
            self.requested_model,
            "deepseek-v4-flash",
            "requested_model",
        )
        _require_exact(self.thinking_type, "enabled", "thinking_type")
        _require_exact(self.reasoning_effort, "max", "reasoning_effort")
        _require_exact(self.max_input_bytes, 24_576, "max_input_bytes")
        _require_exact(self.max_tokens, 8_192, "max_tokens")
        _require_exact(self.max_provider_calls, 1, "max_provider_calls")
        _require_exact(
            self.max_cost_micros_cny,
            MAX_COST_MICROS_CNY_V6,
            "max_cost_micros_cny",
        )
        _require_exact(self.timeout_seconds, 120, "timeout_seconds")
        _require_exact(self.retry_count, 0, "retry_count")
        _require_exact(self.fallback_models, (), "fallback_models")

    @classmethod
    def default(cls) -> DeepSeekModelGatePolicyV6:
        return cls(
            contract_version=MODEL_GATE_POLICY_VERSION_V6,
            provider_origin="https://api.deepseek.com",
            balance_path="/user/balance",
            completion_path="/chat/completions",
            requested_model="deepseek-v4-flash",
            thinking_type="enabled",
            reasoning_effort="max",
            max_input_bytes=24_576,
            max_tokens=8_192,
            max_provider_calls=1,
            max_cost_micros_cny=MAX_COST_MICROS_CNY_V6,
            timeout_seconds=120,
            retry_count=0,
            fallback_models=(),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DeepSeekModelGatePolicyV6:
        document = _require_fields(
            value,
            _POLICY_FIELDS,
            "unexpected_policy_fields",
        )
        fallback_models = document["fallback_models"]
        if not isinstance(fallback_models, (list, tuple)):
            _violate("invalid_fallback_models")
        return cls(
            contract_version=document["contract_version"],
            provider_origin=document["provider_origin"],
            balance_path=document["balance_path"],
            completion_path=document["completion_path"],
            requested_model=document["requested_model"],
            thinking_type=document["thinking_type"],
            reasoning_effort=document["reasoning_effort"],
            max_input_bytes=document["max_input_bytes"],
            max_tokens=document["max_tokens"],
            max_provider_calls=document["max_provider_calls"],
            max_cost_micros_cny=document["max_cost_micros_cny"],
            timeout_seconds=document["timeout_seconds"],
            retry_count=document["retry_count"],
            fallback_models=tuple(fallback_models),
        )

    @classmethod
    def from_json_bytes(cls, data: bytes) -> DeepSeekModelGatePolicyV6:
        return cls.from_mapping(_parse_object(data, "invalid_policy"))

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "balance_path": self.balance_path,
            "completion_path": self.completion_path,
            "contract_version": self.contract_version,
            "fallback_models": list(self.fallback_models),
            "max_cost_micros_cny": self.max_cost_micros_cny,
            "max_input_bytes": self.max_input_bytes,
            "max_provider_calls": self.max_provider_calls,
            "max_tokens": self.max_tokens,
            "provider_origin": self.provider_origin,
            "reasoning_effort": self.reasoning_effort,
            "requested_model": self.requested_model,
            "retry_count": self.retry_count,
            "thinking_type": self.thinking_type,
            "timeout_seconds": self.timeout_seconds,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_mapping())

    @property
    def policy_hash(self) -> str:
        return sha256_hex(self.canonical_bytes)


@dataclass(frozen=True, slots=True)
class ModelGateRequestBindingV6:
    contract_version: str
    idempotency_key: str
    policy: DeepSeekModelGatePolicyV6
    prompt_hash: str
    fixture_hash: str
    response_schema_hash: str

    def __post_init__(self) -> None:
        _require_exact(
            self.contract_version,
            MODEL_GATE_REQUEST_VERSION_V6,
            "contract_version",
        )
        if (
            not isinstance(self.idempotency_key, str)
            or _IDEMPOTENCY_KEY_RE.fullmatch(self.idempotency_key) is None
        ):
            _violate("invalid_idempotency_key")
        if type(self.policy) is not DeepSeekModelGatePolicyV6:
            _violate("invalid_policy")
        _require_hash(self.prompt_hash, "prompt_hash")
        _require_hash(self.fixture_hash, "fixture_hash")
        _require_hash(self.response_schema_hash, "response_schema_hash")

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ModelGateRequestBindingV6:
        document = _require_fields(
            _parse_object(data, "invalid_request"),
            _REQUEST_FIELDS,
            "unexpected_request_fields",
        )
        policy = document["policy"]
        if not isinstance(policy, Mapping):
            _violate("invalid_policy")
        return cls(
            contract_version=document["contract_version"],
            idempotency_key=document["idempotency_key"],
            policy=DeepSeekModelGatePolicyV6.from_mapping(policy),
            prompt_hash=document["prompt_hash"],
            fixture_hash=document["fixture_hash"],
            response_schema_hash=document["response_schema_hash"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "contract_version": self.contract_version,
            "fixture_hash": self.fixture_hash,
            "idempotency_key": self.idempotency_key,
            "policy": self.policy.to_mapping(),
            "prompt_hash": self.prompt_hash,
            "response_schema_hash": self.response_schema_hash,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_mapping())

    @property
    def request_hash(self) -> str:
        return sha256_hex(self.canonical_bytes)


def assert_v6_idempotency_replay_matches(
    existing: ModelGateRequestBindingV6,
    replay: ModelGateRequestBindingV6,
) -> ModelGateRequestBindingV6:
    if (
        type(existing) is not ModelGateRequestBindingV6
        or type(replay) is not ModelGateRequestBindingV6
        or existing.idempotency_key != replay.idempotency_key
        or existing.canonical_bytes != replay.canonical_bytes
    ):
        _violate("idempotency_conflict")
    return existing
