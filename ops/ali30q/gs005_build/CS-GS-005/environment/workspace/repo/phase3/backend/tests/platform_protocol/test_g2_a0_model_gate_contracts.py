from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, replace

import pytest

from platform_protocol.g2_a0_model_gate import (
    MODEL_GATE_REASON_CODES_V1,
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    ModelGateDecisionV1,
    ModelGateRequestBindingV1,
    assert_idempotency_replay_matches,
    canonical_json_bytes,
    sha256_hex,
)


def request_binding(**overrides: object) -> ModelGateRequestBindingV1:
    values: dict[str, object] = {
        "contract_version": "g2-a0-model-gate-request-v1",
        "idempotency_key": "idem_11111111111111111111111111111111",
        "policy": DeepSeekModelGatePolicyV1.default(),
        "prompt_hash": "a" * 64,
        "fixture_hash": "b" * 64,
        "response_schema_hash": "c" * 64,
    }
    values.update(overrides)
    return ModelGateRequestBindingV1(**values)


def policy_document() -> dict[str, object]:
    return dict(DeepSeekModelGatePolicyV1.default().to_mapping())


def test_default_policy_is_exact_immutable_and_slots_based() -> None:
    policy = DeepSeekModelGatePolicyV1.default()

    assert policy.contract_version == "g2-a0-model-gate-policy-v1"
    assert policy.provider_origin == "https://api.deepseek.com"
    assert policy.balance_path == "/user/balance"
    assert policy.completion_path == "/chat/completions"
    assert policy.requested_model == "deepseek-v4-flash-0731"
    assert policy.thinking_type == "enabled"
    assert policy.reasoning_effort == "max"
    assert policy.max_input_bytes == 24_576
    assert policy.max_tokens == 4_096
    assert policy.max_provider_calls == 1
    assert policy.max_cost_micros_cny == 5_000_000
    assert policy.timeout_seconds == 120
    assert policy.retry_count == 0
    assert policy.fallback_models == ()
    assert not hasattr(policy, "__dict__")

    with pytest.raises(FrozenInstanceError):
        policy.requested_model = "deepseek-v4-flash"  # type: ignore[misc]


def test_policy_and_request_have_exact_top_level_and_nested_fields() -> None:
    binding = request_binding()
    document = json.loads(binding.canonical_bytes)

    assert set(document) == {
        "contract_version",
        "fixture_hash",
        "idempotency_key",
        "policy",
        "prompt_hash",
        "response_schema_hash",
    }
    assert set(document["policy"]) == {
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
    assert ModelGateRequestBindingV1.from_json_bytes(binding.canonical_bytes) == binding


@pytest.mark.parametrize(
    "payload",
    (
        b'{"a":1,"a":2}',
        b'{"outer":{"a":1,"a":2}}',
        b'{"items":[{"a":1,"a":2}]}',
    ),
)
def test_duplicate_json_keys_are_rejected_at_every_depth(payload: bytes) -> None:
    with pytest.raises(ModelGateContractViolation, match="duplicate_json_key"):
        canonical_json_bytes(payload)


def test_canonical_json_is_compact_utf8_stable_and_requires_canonical_input() -> None:
    value = {"z": [2, 1], "message": "雪"}
    expected = '{"message":"雪","z":[2,1]}'.encode()

    assert canonical_json_bytes(value) == expected
    assert canonical_json_bytes(expected) == expected
    assert sha256_hex(expected) == sha256_hex(canonical_json_bytes(value))

    with pytest.raises(ModelGateContractViolation, match="non_canonical_json"):
        canonical_json_bytes(b'{ "message":"snow","z":[2,1]}')


@pytest.mark.parametrize(
    "field_name",
    (
        "max_input_bytes",
        "max_tokens",
        "max_provider_calls",
        "max_cost_micros_cny",
        "timeout_seconds",
        "retry_count",
    ),
)
def test_bool_is_rejected_for_every_integer_policy_field(field_name: str) -> None:
    document = policy_document()
    document[field_name] = False

    with pytest.raises(ModelGateContractViolation, match=f"invalid_{field_name}"):
        DeepSeekModelGatePolicyV1.from_mapping(document)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("requested_model", "deepseek-v4-flash"),
        ("requested_model", "deepseek-v4-flash-0732"),
        ("thinking_type", "disabled"),
        ("thinking_type", ""),
        ("reasoning_effort", "high"),
        ("reasoning_effort", ""),
        ("retry_count", 1),
        ("fallback_models", ("deepseek-v4-flash",)),
    ),
)
def test_policy_widening_is_rejected(field_name: str, bad_value: object) -> None:
    with pytest.raises(ModelGateContractViolation, match=f"invalid_{field_name}"):
        replace(DeepSeekModelGatePolicyV1.default(), **{field_name: bad_value})


@pytest.mark.parametrize(
    "field_name",
    (
        "temperature",
        "top_p",
        "presence_penalty",
        "frequency_penalty",
        "tools",
        "tool_choice",
        "retry",
        "fallback_provider",
        "follow_redirects",
        "proxy",
        "stream",
        "embeddings_path",
    ),
)
def test_unapproved_policy_fields_are_rejected(field_name: str) -> None:
    document = policy_document()
    document[field_name] = False

    with pytest.raises(ModelGateContractViolation, match="unexpected_policy_fields"):
        DeepSeekModelGatePolicyV1.from_mapping(document)


@pytest.mark.parametrize(
    "origin",
    (
        "http://api.deepseek.com",
        "https://api.deepseek.com/",
        "https://api.deepseek.com?mode=test",
        "https://api.deepseek.com#fragment",
        "https://user@api.deepseek.com",
        "https://api.deepseek.com.evil.invalid",
        "not-a-url",
    ),
)
def test_provider_origin_is_exact_and_cannot_carry_url_ambiguity(origin: str) -> None:
    with pytest.raises(ModelGateContractViolation, match="invalid_provider_origin"):
        replace(DeepSeekModelGatePolicyV1.default(), provider_origin=origin)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("balance_path", "/user/balance?account=1"),
        ("balance_path", "https://api.deepseek.com/user/balance"),
        ("completion_path", "/chat/completions#fragment"),
        ("completion_path", "/v1/chat/completions"),
    ),
)
def test_endpoint_paths_are_exact(field_name: str, bad_value: str) -> None:
    with pytest.raises(ModelGateContractViolation, match=f"invalid_{field_name}"):
        replace(DeepSeekModelGatePolicyV1.default(), **{field_name: bad_value})


@pytest.mark.parametrize(
    "field_name",
    (
        "api_key",
        "authorization_header",
        "headers",
        "prompt",
        "response",
        "reasoning",
        "local_path",
        "command",
    ),
)
def test_serializable_request_rejects_raw_sensitive_or_executable_fields(
    field_name: str,
) -> None:
    binding = request_binding()
    document = json.loads(binding.canonical_bytes)
    document[field_name] = "prohibited-marker"

    with pytest.raises(ModelGateContractViolation, match="unexpected_request_fields"):
        ModelGateRequestBindingV1.from_json_bytes(canonical_json_bytes(document))


def test_nested_policy_extra_and_decision_extra_are_rejected() -> None:
    request_document = json.loads(request_binding().canonical_bytes)
    request_document["policy"]["temperature"] = 0
    with pytest.raises(ModelGateContractViolation, match="unexpected_policy_fields"):
        ModelGateRequestBindingV1.from_json_bytes(
            canonical_json_bytes(request_document)
        )

    decision = ModelGateDecisionV1(
        status="rejected",
        reason_codes=("policy_violation",),
        request_hash=request_binding().request_hash,
    )
    decision_document = json.loads(decision.canonical_bytes)
    decision_document["runtime_authorized"] = True
    with pytest.raises(ModelGateContractViolation, match="unexpected_decision_fields"):
        ModelGateDecisionV1.from_json_bytes(canonical_json_bytes(decision_document))


def test_request_binding_contains_only_opaque_key_hashes_and_fixed_policy() -> None:
    binding = request_binding()

    assert binding.request_hash == sha256_hex(binding.canonical_bytes)
    assert b"synthetic repair prompt" not in binding.canonical_bytes
    assert b"Authorization" not in binding.canonical_bytes
    assert b"C:\\" not in binding.canonical_bytes

    with pytest.raises(ModelGateContractViolation, match="invalid_prompt_hash"):
        request_binding(prompt_hash="raw prompt")


@pytest.mark.parametrize(
    "idempotency_key",
    (
        "human@example.com",
        "idem_sk-live-prohibited-marker",
        "idem_rm-rf-home",
        "idem_1234",
        "idem_AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA",
    ),
)
def test_idempotency_key_is_a_fixed_opaque_128_bit_identifier(
    idempotency_key: str,
) -> None:
    with pytest.raises(ModelGateContractViolation, match="invalid_idempotency_key"):
        request_binding(idempotency_key=idempotency_key)


def test_same_idempotency_key_requires_the_same_canonical_payload() -> None:
    original = request_binding()
    identical = ModelGateRequestBindingV1.from_json_bytes(original.canonical_bytes)

    assert assert_idempotency_replay_matches(original, identical) is original

    changed = request_binding(prompt_hash="d" * 64)
    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        assert_idempotency_replay_matches(original, changed)


def test_decision_uses_fixed_status_reason_vocabulary_and_canonical_order() -> None:
    request_hash = request_binding().request_hash
    admitted = ModelGateDecisionV1(
        status="admitted", reason_codes=(), request_hash=request_hash
    )
    rejected = ModelGateDecisionV1(
        status="rejected",
        reason_codes=("budget_exceeded", "policy_violation"),
        request_hash=request_hash,
    )

    assert ModelGateDecisionV1.from_json_bytes(admitted.canonical_bytes) == admitted
    assert ModelGateDecisionV1.from_json_bytes(rejected.canonical_bytes) == rejected
    assert set(MODEL_GATE_REASON_CODES_V1) >= {
        "model_identity_unproven",
        "thinking_evidence_missing",
        "structured_output_invalid",
        "usage_invalid",
        "budget_exceeded",
        "candidate_verification_failed",
        "idempotency_conflict",
        "provider_call_ambiguous",
        "policy_violation",
    }

    with pytest.raises(ModelGateContractViolation, match="invalid_decision_status"):
        ModelGateDecisionV1("approved", (), request_hash)  # type: ignore[arg-type]
    with pytest.raises(ModelGateContractViolation, match="invalid_reason_codes"):
        ModelGateDecisionV1("rejected", ("free_text",), request_hash)
    with pytest.raises(ModelGateContractViolation, match="invalid_reason_codes"):
        ModelGateDecisionV1(
            "rejected", ("policy_violation", "budget_exceeded"), request_hash
        )
    with pytest.raises(ModelGateContractViolation, match="invalid_reason_codes"):
        ModelGateDecisionV1("admitted", ("policy_violation",), request_hash)


def test_canonical_json_rejects_non_json_and_ambiguous_numeric_values() -> None:
    with pytest.raises(ModelGateContractViolation, match="invalid_json_value"):
        canonical_json_bytes({"value": 1.5})
    with pytest.raises(ModelGateContractViolation, match="invalid_json"):
        canonical_json_bytes(b"not-json")
