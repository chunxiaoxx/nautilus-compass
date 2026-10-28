from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Literal, Mapping

MODEL_GATE_POLICY_VERSION = "g2-a0-model-gate-policy-v1"
MODEL_GATE_REQUEST_VERSION = "g2-a0-model-gate-request-v1"
MODEL_GATE_REASON_CODES_V1 = (
    "model_identity_unproven",
    "thinking_evidence_missing",
    "structured_output_invalid",
    "usage_invalid",
    "budget_exceeded",
    "candidate_verification_failed",
    "idempotency_conflict",
    "provider_call_ambiguous",
    "policy_violation",
)

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
_DECISION_FIELDS = frozenset({"reason_codes", "request_hash", "status"})


class ModelGateContractViolation(ValueError):
    """A fail-closed G2-A0 contract validation reason."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _violate(code: str) -> None:
    raise ModelGateContractViolation(code)


def _validate_json_value(value: object) -> None:
    if value is None or type(value) in {str, int, bool}:
        return
    if isinstance(value, (list, tuple)):
        for item in value:
            _validate_json_value(item)
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                _violate("invalid_json_value")
            _validate_json_value(item)
        return
    _violate("invalid_json_value")


def _dump_canonical_json(value: object) -> bytes:
    _validate_json_value(value)
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            _violate("duplicate_json_key")
        result[key] = value
    return result


def _parse_canonical_json(data: bytes) -> object:
    if not isinstance(data, bytes):
        _violate("invalid_json")
    try:
        decoded = data.decode("utf-8")
        value = json.loads(decoded, object_pairs_hook=_reject_duplicate_keys)
    except ModelGateContractViolation:
        raise
    except (UnicodeDecodeError, json.JSONDecodeError):
        _violate("invalid_json")
    canonical = _dump_canonical_json(value)
    if canonical != data:
        _violate("non_canonical_json")
    return value


def canonical_json_bytes(value: Mapping[str, Any] | bytes) -> bytes:
    """Emit canonical JSON or validate that supplied bytes are already canonical."""

    if isinstance(value, bytes):
        parsed = _parse_canonical_json(value)
        return _dump_canonical_json(parsed)
    if not isinstance(value, Mapping):
        _violate("invalid_json_value")
    return _dump_canonical_json(value)


def sha256_hex(value: bytes) -> str:
    if not isinstance(value, bytes):
        _violate("invalid_hash_input")
    return hashlib.sha256(value).hexdigest()


def _require_exact(value: object, expected: object, field_name: str) -> None:
    if value != expected or type(value) is not type(expected):
        _violate(f"invalid_{field_name}")


def _require_fixed_int(value: object, expected: int, field_name: str) -> None:
    if type(value) is not int or value != expected:
        _violate(f"invalid_{field_name}")


def _require_sha256(value: object, field_name: str) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate(f"invalid_{field_name}")


def _require_exact_fields(
    value: object,
    expected_fields: frozenset[str],
    failure_code: str,
) -> Mapping[str, Any]:
    if not isinstance(value, Mapping) or set(value) != expected_fields:
        _violate(failure_code)
    return value


@dataclass(frozen=True, slots=True)
class DeepSeekModelGatePolicyV1:
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
            self.contract_version, MODEL_GATE_POLICY_VERSION, "contract_version"
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
            "deepseek-v4-flash-0731",
            "requested_model",
        )
        _require_exact(self.thinking_type, "enabled", "thinking_type")
        _require_exact(self.reasoning_effort, "max", "reasoning_effort")
        _require_fixed_int(self.max_input_bytes, 24_576, "max_input_bytes")
        _require_fixed_int(self.max_tokens, 4_096, "max_tokens")
        _require_fixed_int(self.max_provider_calls, 1, "max_provider_calls")
        _require_fixed_int(self.max_cost_micros_cny, 5_000_000, "max_cost_micros_cny")
        _require_fixed_int(self.timeout_seconds, 120, "timeout_seconds")
        _require_fixed_int(self.retry_count, 0, "retry_count")
        _require_exact(self.fallback_models, (), "fallback_models")

    @classmethod
    def default(cls) -> DeepSeekModelGatePolicyV1:
        return cls(
            contract_version=MODEL_GATE_POLICY_VERSION,
            provider_origin="https://api.deepseek.com",
            balance_path="/user/balance",
            completion_path="/chat/completions",
            requested_model="deepseek-v4-flash-0731",
            thinking_type="enabled",
            reasoning_effort="max",
            max_input_bytes=24_576,
            max_tokens=4_096,
            max_provider_calls=1,
            max_cost_micros_cny=5_000_000,
            timeout_seconds=120,
            retry_count=0,
            fallback_models=(),
        )

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> DeepSeekModelGatePolicyV1:
        document = _require_exact_fields(
            value, _POLICY_FIELDS, "unexpected_policy_fields"
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
    def from_json_bytes(cls, data: bytes) -> DeepSeekModelGatePolicyV1:
        value = _parse_canonical_json(data)
        if not isinstance(value, Mapping):
            _violate("invalid_policy")
        return cls.from_mapping(value)

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
class ModelGateRequestBindingV1:
    """Opaque hashes and fixed policy that define one idempotent model-gate request."""

    contract_version: str
    idempotency_key: str
    policy: DeepSeekModelGatePolicyV1
    prompt_hash: str
    fixture_hash: str
    response_schema_hash: str

    def __post_init__(self) -> None:
        _require_exact(
            self.contract_version, MODEL_GATE_REQUEST_VERSION, "contract_version"
        )
        if (
            not isinstance(self.idempotency_key, str)
            or _IDEMPOTENCY_KEY_RE.fullmatch(self.idempotency_key) is None
        ):
            _violate("invalid_idempotency_key")
        if not isinstance(self.policy, DeepSeekModelGatePolicyV1):
            _violate("invalid_policy")
        _require_sha256(self.prompt_hash, "prompt_hash")
        _require_sha256(self.fixture_hash, "fixture_hash")
        _require_sha256(self.response_schema_hash, "response_schema_hash")

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ModelGateRequestBindingV1:
        value = _parse_canonical_json(data)
        document = _require_exact_fields(
            value, _REQUEST_FIELDS, "unexpected_request_fields"
        )
        policy_value = document["policy"]
        if not isinstance(policy_value, Mapping):
            _violate("invalid_policy")
        return cls(
            contract_version=document["contract_version"],
            idempotency_key=document["idempotency_key"],
            policy=DeepSeekModelGatePolicyV1.from_mapping(policy_value),
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


def assert_idempotency_replay_matches(
    existing: ModelGateRequestBindingV1,
    replay: ModelGateRequestBindingV1,
) -> ModelGateRequestBindingV1:
    if not isinstance(existing, ModelGateRequestBindingV1) or not isinstance(
        replay, ModelGateRequestBindingV1
    ):
        _violate("idempotency_conflict")
    if (
        existing.idempotency_key != replay.idempotency_key
        or existing.canonical_bytes != replay.canonical_bytes
    ):
        _violate("idempotency_conflict")
    return existing


@dataclass(frozen=True, slots=True)
class ModelGateDecisionV1:
    status: Literal["admitted", "rejected", "inconclusive"]
    reason_codes: tuple[str, ...]
    request_hash: str

    def __post_init__(self) -> None:
        if self.status not in {"admitted", "rejected", "inconclusive"}:
            _violate("invalid_decision_status")
        if not isinstance(self.reason_codes, tuple):
            _violate("invalid_reason_codes")
        if any(
            reason not in MODEL_GATE_REASON_CODES_V1 for reason in self.reason_codes
        ):
            _violate("invalid_reason_codes")
        positions = tuple(
            MODEL_GATE_REASON_CODES_V1.index(reason) for reason in self.reason_codes
        )
        if len(set(self.reason_codes)) != len(self.reason_codes) or positions != tuple(
            sorted(positions)
        ):
            _violate("invalid_reason_codes")
        if (self.status == "admitted") != (self.reason_codes == ()):
            _violate("invalid_reason_codes")
        _require_sha256(self.request_hash, "request_hash")

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ModelGateDecisionV1:
        value = _parse_canonical_json(data)
        document = _require_exact_fields(
            value, _DECISION_FIELDS, "unexpected_decision_fields"
        )
        reason_codes = document["reason_codes"]
        if not isinstance(reason_codes, list):
            _violate("invalid_reason_codes")
        return cls(
            status=document["status"],
            reason_codes=tuple(reason_codes),
            request_hash=document["request_hash"],
        )

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "reason_codes": list(self.reason_codes),
            "request_hash": self.request_hash,
            "status": self.status,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_mapping())
