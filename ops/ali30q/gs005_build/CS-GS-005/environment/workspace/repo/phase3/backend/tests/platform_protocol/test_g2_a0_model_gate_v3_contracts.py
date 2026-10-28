from __future__ import annotations

import json
from dataclasses import replace

import pytest

from platform_protocol.g2_a0_model_gate import (
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    ModelGateRequestBindingV1,
    canonical_json_bytes,
)
from platform_protocol.g2_a0_model_gate_v3 import (
    MAX_COST_MICROS_CNY_V3,
    MODEL_GATE_POLICY_VERSION_V3,
    MODEL_GATE_REQUEST_VERSION_V3,
    DeepSeekModelGatePolicyV3,
    ModelGateRequestBindingV3,
    assert_v3_idempotency_replay_matches,
)

_V1_POLICY_HASH = "859f3b8795c96d60d2146887e42db6f5fd4390b58b62e45109b1aa447b11d25c"


def _request_v3(**overrides: object) -> ModelGateRequestBindingV3:
    values: dict[str, object] = {
        "contract_version": MODEL_GATE_REQUEST_VERSION_V3,
        "idempotency_key": "idem_22222222222222222222222222222222",
        "policy": DeepSeekModelGatePolicyV3.default(),
        "prompt_hash": "a" * 64,
        "fixture_hash": "b" * 64,
        "response_schema_hash": "c" * 64,
    }
    values.update(overrides)
    return ModelGateRequestBindingV3(**values)


def test_v3_policy_changes_only_version_and_exact_cost_cap() -> None:
    v1 = DeepSeekModelGatePolicyV1.default()
    v2 = DeepSeekModelGatePolicyV3.default()
    v1_document = dict(v1.to_mapping())
    v2_document = dict(v2.to_mapping())

    assert v2.contract_version == MODEL_GATE_POLICY_VERSION_V3
    assert v2.max_cost_micros_cny == MAX_COST_MICROS_CNY_V3 == 10_000_000
    v1_document.pop("contract_version")
    v2_document.pop("contract_version")
    v1_document.pop("max_cost_micros_cny")
    v2_document.pop("max_cost_micros_cny")
    assert v2_document.pop("requested_model") == "deepseek-v4-flash"
    assert v1_document.pop("requested_model") == "deepseek-v4-flash-0731"
    assert v2_document == v1_document
    assert DeepSeekModelGatePolicyV1.default().policy_hash == _V1_POLICY_HASH


@pytest.mark.parametrize("bad_cost", (9_999_999, 10_000_001, False, True))
def test_v3_cost_cap_is_fixed_and_bool_safe(bad_cost: object) -> None:
    document = dict(DeepSeekModelGatePolicyV3.default().to_mapping())
    document["max_cost_micros_cny"] = bad_cost

    with pytest.raises(ModelGateContractViolation, match="invalid_max_cost_micros_cny"):
        DeepSeekModelGatePolicyV3.from_mapping(document)


def test_v3_request_round_trip_is_canonical_and_deterministic() -> None:
    request = _request_v3()

    assert request.contract_version == MODEL_GATE_REQUEST_VERSION_V3
    assert request.request_hash == _request_v3().request_hash
    assert ModelGateRequestBindingV3.from_json_bytes(request.canonical_bytes) == request


def test_v3_rejects_v1_policy_request_and_cross_version_replay() -> None:
    with pytest.raises(ModelGateContractViolation, match="invalid_policy"):
        _request_v3(policy=DeepSeekModelGatePolicyV1.default())

    v1 = ModelGateRequestBindingV1(
        contract_version="g2-a0-model-gate-request-v1",
        idempotency_key="idem_22222222222222222222222222222222",
        policy=DeepSeekModelGatePolicyV1.default(),
        prompt_hash="a" * 64,
        fixture_hash="b" * 64,
        response_schema_hash="c" * 64,
    )
    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        assert_v3_idempotency_replay_matches(_request_v3(), v1)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "mutator",
    (
        lambda value: value.pop("fixture_hash"),
        lambda value: value.update({"runtime_authorized": True}),
        lambda value: value["policy"].update({"retry_count": 1}),
        lambda value: value.update({"contract_version": "g2-a0-model-gate-request-v1"}),
    ),
)
def test_v3_request_fails_closed_on_shape_policy_and_version(
    mutator: object,
) -> None:
    document = json.loads(_request_v3().canonical_bytes)
    mutator(document)  # type: ignore[operator]

    with pytest.raises(ModelGateContractViolation):
        ModelGateRequestBindingV3.from_json_bytes(canonical_json_bytes(document))


def test_v3_parsers_reject_duplicate_and_noncanonical_json() -> None:
    with pytest.raises(ModelGateContractViolation, match="duplicate_json_key"):
        DeepSeekModelGatePolicyV3.from_json_bytes(
            b'{"contract_version":"a","contract_version":"b"}'
        )
    with pytest.raises(ModelGateContractViolation, match="non_canonical_json"):
        ModelGateRequestBindingV3.from_json_bytes(b'{ "contract_version":"x"}')


def test_v3_changed_payload_replay_conflicts() -> None:
    existing = _request_v3()
    replay = replace(existing, prompt_hash="d" * 64)

    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        assert_v3_idempotency_replay_matches(existing, replay)
