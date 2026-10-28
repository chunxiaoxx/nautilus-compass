from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

import httpx

from platform_protocol.g2_a0_model_gate import (
    MODEL_GATE_REASON_CODES_V1,
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    canonical_json_bytes,
)

RESPONSE_EXAMPLE_JSON = (
    '{"artifact_version":"g2-a0-candidate-v1",'
    '"claimed_test_scope":["public_behavior"],'
    '"language":"python","summary_code":"bounded_repair",'
    '"unified_diff":"<unified diff>"}'
)

_REQUEST_FIELDS = frozenset(
    {
        "max_tokens",
        "messages",
        "model",
        "reasoning_effort",
        "response_format",
        "stream",
        "thinking",
    }
)
_PROVIDER_FIELDS = frozenset(
    {
        "choices",
        "created",
        "id",
        "model",
        "object",
        "system_fingerprint",
        "usage",
    }
)
_CHOICE_FIELDS = frozenset({"finish_reason", "index", "message"})
_MESSAGE_FIELDS = frozenset({"content", "reasoning_content", "role"})
_USAGE_FIELDS = frozenset(
    {
        "completion_tokens",
        "prompt_cache_hit_tokens",
        "prompt_cache_miss_tokens",
        "prompt_tokens",
        "total_tokens",
    }
)
_CANDIDATE_FIELDS = frozenset(
    {
        "artifact_version",
        "claimed_test_scope",
        "language",
        "summary_code",
        "unified_diff",
    }
)
_SUMMARY_CODE_RE = re.compile(r"[a-z][a-z0-9_]{1,63}")

_CACHE_HIT_MICROS_CNY_PER_MILLION = 20_000
_CACHE_MISS_MICROS_CNY_PER_MILLION = 1_000_000
_OUTPUT_MICROS_CNY_PER_MILLION = 2_000_000
_MICROS_PRICE_DENOMINATOR = 1_000_000


class DeepSeekClientViolation(ValueError):
    """A redacted, fixed G2-A0 gate reason code."""

    def __init__(self, code: str) -> None:
        if code not in MODEL_GATE_REASON_CODES_V1:
            code = "policy_violation"
        self.code = code
        super().__init__(code)


class _DuplicateJsonKey(ValueError):
    pass


def _violate(code: str) -> None:
    raise DeepSeekClientViolation(code)


def _reject_duplicate_keys(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateJsonKey
        result[key] = value
    return result


def _parse_json_object(data: bytes, failure_code: str) -> Mapping[str, Any]:
    if not isinstance(data, bytes):
        _violate(failure_code)
    try:
        value = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=_reject_duplicate_keys,
        )
    except (UnicodeDecodeError, ValueError, RecursionError):
        _violate(failure_code)
    if not isinstance(value, dict):
        _violate(failure_code)
    return value


def _exact_mapping(
    value: object,
    expected_fields: frozenset[str],
    failure_code: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict) or set(value) != expected_fields:
        _violate(failure_code)
    return value


def _require_nonempty_text(
    value: object,
    failure_code: str,
    *,
    max_bytes: int,
) -> str:
    if not isinstance(value, str) or not value.strip():
        _violate(failure_code)
    try:
        encoded = value.encode("utf-8")
    except UnicodeEncodeError:
        _violate(failure_code)
    if len(encoded) > max_bytes:
        _violate(failure_code)
    return value


def _require_usage_int(value: object) -> int:
    if type(value) is not int or value < 0:
        _violate("usage_invalid")
    return value


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _upper_bound_cost_micros_cny(
    *,
    cache_hit_tokens: int,
    cache_miss_tokens: int,
    output_tokens: int,
) -> int:
    numerator = (
        cache_hit_tokens * _CACHE_HIT_MICROS_CNY_PER_MILLION
        + cache_miss_tokens * _CACHE_MISS_MICROS_CNY_PER_MILLION
        + output_tokens * _OUTPUT_MICROS_CNY_PER_MILLION
    )
    return (numerator + _MICROS_PRICE_DENOMINATOR - 1) // _MICROS_PRICE_DENOMINATOR


@dataclass(frozen=True, slots=True)
class CandidateArtifactV1:
    artifact_version: str
    claimed_test_scope: tuple[str, ...]
    language: str
    summary_code: str
    unified_diff: str


@dataclass(frozen=True, slots=True)
class DeepSeekCompletionResultV1:
    returned_model: str
    response_content_sha256: str
    reasoning_sha256: str
    system_fingerprint_sha256: str
    input_tokens: int
    output_tokens: int
    cache_hit_input_tokens: int
    cache_miss_input_tokens: int
    calculated_cost_micros_cny: int
    provider_call_count: int
    candidate: CandidateArtifactV1


@dataclass(frozen=True, slots=True)
class DeepSeekTransportClientV1:
    policy: DeepSeekModelGatePolicyV1
    transport: httpx.BaseTransport

    def __post_init__(self) -> None:
        if not isinstance(self.policy, DeepSeekModelGatePolicyV1):
            _violate("policy_violation")
        if not isinstance(self.transport, httpx.BaseTransport):
            _violate("policy_violation")

    def complete_once(
        self,
        *,
        canonical_request: bytes,
        api_key: str,
    ) -> DeepSeekCompletionResultV1:
        self._validate_request(canonical_request)
        self._validate_api_key(api_key)
        try:
            with httpx.Client(
                base_url=self.policy.provider_origin,
                transport=self.transport,
                timeout=httpx.Timeout(self.policy.timeout_seconds),
                follow_redirects=False,
                trust_env=False,
            ) as http:
                response = http.post(
                    self.policy.completion_path,
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                    },
                    content=canonical_request,
                )
        except Exception:  # noqa: BLE001
            # Redact every ordinary failure crossing the provider boundary.
            raise DeepSeekClientViolation("provider_call_ambiguous") from None

        if response.status_code != 200:
            _violate("policy_violation")
        content_type = response.headers.get("content-type", "").split(";", 1)[0]
        if content_type.strip().lower() != "application/json":
            _violate("structured_output_invalid")
        return self._parse_provider_response(response.content)

    def _validate_request(self, canonical_request: bytes) -> None:
        try:
            canonical_json_bytes(canonical_request)
        except (ModelGateContractViolation, ValueError, RecursionError):
            _violate("policy_violation")
        body = _exact_mapping(
            _parse_json_object(canonical_request, "policy_violation"),
            _REQUEST_FIELDS,
            "policy_violation",
        )
        if body["model"] != self.policy.requested_model:
            _violate("policy_violation")
        if body["reasoning_effort"] != self.policy.reasoning_effort:
            _violate("policy_violation")
        if body["thinking"] != {"type": self.policy.thinking_type}:
            _violate("policy_violation")
        if body["response_format"] != {"type": "json_object"}:
            _violate("policy_violation")
        if body["stream"] is not False:
            _violate("policy_violation")
        if (
            type(body["max_tokens"]) is not int
            or body["max_tokens"] != self.policy.max_tokens
        ):
            _violate("policy_violation")

        messages = body["messages"]
        if not isinstance(messages, list) or len(messages) != 1:
            _violate("policy_violation")
        message = _exact_mapping(
            messages[0], frozenset({"content", "role"}), "policy_violation"
        )
        if message["role"] != "user":
            _violate("policy_violation")
        prompt = _require_nonempty_text(
            message["content"],
            "policy_violation",
            max_bytes=self.policy.max_input_bytes,
        )
        if "json" not in prompt.lower() or RESPONSE_EXAMPLE_JSON not in prompt:
            _violate("policy_violation")

    @staticmethod
    def _validate_api_key(api_key: object) -> None:
        if (
            not isinstance(api_key, str)
            or not api_key
            or len(api_key) > 512
            or not api_key.isascii()
            or any(character.isspace() for character in api_key)
        ):
            _violate("policy_violation")

    def _parse_provider_response(
        self,
        data: bytes,
    ) -> DeepSeekCompletionResultV1:
        parsed = _parse_json_object(data, "structured_output_invalid")
        if "model" not in parsed or "system_fingerprint" not in parsed:
            _violate("model_identity_unproven")
        if "usage" not in parsed:
            _violate("usage_invalid")
        document = _exact_mapping(
            parsed,
            _PROVIDER_FIELDS,
            "structured_output_invalid",
        )
        if document["model"] != self.policy.requested_model:
            _violate("model_identity_unproven")
        if document["object"] != "chat.completion":
            _violate("structured_output_invalid")
        if (
            type(document["created"]) is not int
            or document["created"] < 0
            or not isinstance(document["id"], str)
            or not document["id"]
        ):
            _violate("structured_output_invalid")
        fingerprint = _require_nonempty_text(
            document["system_fingerprint"],
            "model_identity_unproven",
            max_bytes=256,
        )

        content, reasoning = self._parse_choice(document["choices"])
        candidate = self._parse_candidate(content)
        usage = self._parse_usage(document["usage"])
        calculated_cost = _upper_bound_cost_micros_cny(
            cache_hit_tokens=usage["prompt_cache_hit_tokens"],
            cache_miss_tokens=usage["prompt_cache_miss_tokens"],
            output_tokens=usage["completion_tokens"],
        )
        if calculated_cost > self.policy.max_cost_micros_cny:
            _violate("budget_exceeded")

        return DeepSeekCompletionResultV1(
            returned_model=self.policy.requested_model,
            response_content_sha256=_sha256_text(content),
            reasoning_sha256=_sha256_text(reasoning),
            system_fingerprint_sha256=_sha256_text(fingerprint),
            input_tokens=usage["prompt_tokens"],
            output_tokens=usage["completion_tokens"],
            cache_hit_input_tokens=usage["prompt_cache_hit_tokens"],
            cache_miss_input_tokens=usage["prompt_cache_miss_tokens"],
            calculated_cost_micros_cny=calculated_cost,
            provider_call_count=1,
            candidate=candidate,
        )

    @staticmethod
    def _parse_choice(value: object) -> tuple[str, str]:
        if not isinstance(value, list) or len(value) != 1:
            _violate("structured_output_invalid")
        choice = _exact_mapping(value[0], _CHOICE_FIELDS, "structured_output_invalid")
        if type(choice["index"]) is not int or choice["index"] != 0:
            _violate("structured_output_invalid")
        if choice["finish_reason"] != "stop":
            _violate("structured_output_invalid")
        message_value = choice["message"]
        if isinstance(message_value, dict) and "reasoning_content" not in message_value:
            _violate("thinking_evidence_missing")
        message = _exact_mapping(
            message_value, _MESSAGE_FIELDS, "structured_output_invalid"
        )
        if message["role"] != "assistant":
            _violate("structured_output_invalid")
        content = _require_nonempty_text(
            message["content"],
            "structured_output_invalid",
            max_bytes=131_072,
        )
        reasoning = _require_nonempty_text(
            message["reasoning_content"],
            "thinking_evidence_missing",
            max_bytes=1_048_576,
        )
        return content, reasoning

    @staticmethod
    def _parse_candidate(content: str) -> CandidateArtifactV1:
        document = _exact_mapping(
            _parse_json_object(content.encode("utf-8"), "structured_output_invalid"),
            _CANDIDATE_FIELDS,
            "structured_output_invalid",
        )
        if document["artifact_version"] != "g2-a0-candidate-v1":
            _violate("structured_output_invalid")
        if document["language"] != "python":
            _violate("structured_output_invalid")
        summary_code = _require_nonempty_text(
            document["summary_code"],
            "structured_output_invalid",
            max_bytes=64,
        )
        if _SUMMARY_CODE_RE.fullmatch(summary_code) is None:
            _violate("structured_output_invalid")
        unified_diff = _require_nonempty_text(
            document["unified_diff"],
            "structured_output_invalid",
            max_bytes=65_536,
        )
        claimed_scope = document["claimed_test_scope"]
        if claimed_scope != ["public_behavior"]:
            _violate("structured_output_invalid")
        return CandidateArtifactV1(
            artifact_version="g2-a0-candidate-v1",
            claimed_test_scope=("public_behavior",),
            language="python",
            summary_code=summary_code,
            unified_diff=unified_diff,
        )

    def _parse_usage(self, value: object) -> Mapping[str, int]:
        document = _exact_mapping(value, _USAGE_FIELDS, "usage_invalid")
        usage = {
            field_name: _require_usage_int(document[field_name])
            for field_name in _USAGE_FIELDS
        }
        if usage["prompt_tokens"] <= 0 or usage["completion_tokens"] <= 0:
            _violate("usage_invalid")
        if (
            usage["prompt_cache_hit_tokens"] + usage["prompt_cache_miss_tokens"]
            != usage["prompt_tokens"]
        ):
            _violate("usage_invalid")
        if usage["prompt_tokens"] + usage["completion_tokens"] != usage["total_tokens"]:
            _violate("usage_invalid")
        if usage["completion_tokens"] > self.policy.max_tokens:
            _violate("usage_invalid")
        return usage
