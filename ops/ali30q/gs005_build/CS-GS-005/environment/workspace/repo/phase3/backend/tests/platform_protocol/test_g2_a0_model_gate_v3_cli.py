from __future__ import annotations

from dataclasses import replace

import pytest
from g2_a0_deepseek_client import (
    CandidateArtifactV1,
    DeepSeekClientViolation,
    DeepSeekCompletionResultV1,
)
from g2_a0_model_gate_cli import (
    _VALID_PATCH,
    G2_A0_PAID_RUN_AUTHORIZATION,
    ModelGateRunnerViolation,
)
from g2_a0_model_gate_v3_cli import (
    G2_A0_PAID_RUN_AUTHORIZATION_V3,
    MODEL_GATE_EVIDENCE_VERSION_V3,
    ModelGateEvidenceV3,
    OfflineModelGateRunnerV3,
    build_request_v3,
    execute_probe_v3,
)
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1
from g2_a0_synthetic_verifier import verify_candidate_patch

from platform_protocol.g2_a0_model_gate import ModelGateContractViolation
from platform_protocol.g2_a0_model_gate_v3 import DeepSeekModelGatePolicyV3

_COMMIT = "1" * 40
_IDEMPOTENCY_KEY = "idem_33333333333333333333333333333333"


def _completion(cost: int) -> DeepSeekCompletionResultV1:
    return DeepSeekCompletionResultV1(
        returned_model="deepseek-v4-flash",
        response_content_sha256="1" * 64,
        reasoning_sha256="2" * 64,
        system_fingerprint_sha256="3" * 64,
        input_tokens=10,
        output_tokens=5,
        cache_hit_input_tokens=4,
        cache_miss_input_tokens=6,
        calculated_cost_micros_cny=cost,
        provider_call_count=1,
        candidate=CandidateArtifactV1(
            artifact_version="g2-a0-candidate-v1",
            claimed_test_scope=("public_behavior",),
            language="python",
            summary_code="bounded_repair",
            unified_diff=_VALID_PATCH,
        ),
    )


def _runner(
    *,
    tmp_path: object,
    balances: tuple[int, ...],
    completion_cost: int,
    completion_calls: list[int],
) -> OfflineModelGateRunnerV3:
    balance_values = iter(balances)

    def complete_once(
        canonical_request: bytes,
        api_key: str,
    ) -> DeepSeekCompletionResultV1:
        assert canonical_request
        assert api_key == "test-process-placeholder"
        completion_calls.append(1)
        return _completion(completion_cost)

    return OfflineModelGateRunnerV3(
        implementation_commit=_COMMIT,
        balance_reader=lambda: next(balance_values),
        completion=complete_once,
        verifier=lambda candidate: verify_candidate_patch(
            fixture=SyntheticRepairFixtureV1.default(),
            candidate=candidate,
            temp_root=tmp_path,  # type: ignore[arg-type]
        ),
    )


def test_v3_runner_accepts_exact_cny_10_and_emits_v3_evidence(tmp_path: object) -> None:
    request, canonical_request = build_request_v3(
        fixture=SyntheticRepairFixtureV1.default(),
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    completion_calls: list[int] = []
    runner = _runner(
        tmp_path=tmp_path,
        balances=(20_000_000, 10_000_000),
        completion_cost=10_000_000,
        completion_calls=completion_calls,
    )

    result = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )
    evidence = ModelGateEvidenceV3.from_json_bytes(result.evidence_bytes)

    assert result.decision.status == "admitted"
    assert evidence.contract_version == MODEL_GATE_EVIDENCE_VERSION_V3
    assert evidence.calculated_cost_micros_cny == 10_000_000
    assert evidence.balance_delta_micros_cny == 10_000_000
    assert evidence.provider_call_count == 1
    assert completion_calls == [1]


@pytest.mark.parametrize(
    ("balances", "completion_cost"),
    (
        ((20_000_001, 10_000_000), 1),
        ((20_000_000, 20_000_000), 10_000_001),
    ),
)
def test_v3_runner_rejects_either_cost_over_cny_10(
    tmp_path: object,
    balances: tuple[int, int],
    completion_cost: int,
) -> None:
    request, canonical_request = build_request_v3(
        fixture=SyntheticRepairFixtureV1.default(),
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    runner = _runner(
        tmp_path=tmp_path,
        balances=balances,
        completion_cost=completion_cost,
        completion_calls=[],
    )

    result = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )

    assert result.decision.status == "rejected"
    assert result.decision.reason_codes == ("budget_exceeded",)


def test_v3_exact_replay_has_zero_provider_growth(tmp_path: object) -> None:
    request, canonical_request = build_request_v3(
        fixture=SyntheticRepairFixtureV1.default(),
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    completion_calls: list[int] = []
    runner = _runner(
        tmp_path=tmp_path,
        balances=(100, 99),
        completion_cost=1,
        completion_calls=completion_calls,
    )
    first = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )

    replay = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )

    assert replay is first
    assert completion_calls == [1]


def test_v3_changed_replay_conflicts_before_balance_or_completion(
    tmp_path: object,
) -> None:
    request, canonical_request = build_request_v3(
        fixture=SyntheticRepairFixtureV1.default(),
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    completion_calls: list[int] = []
    runner = _runner(
        tmp_path=tmp_path,
        balances=(100, 99),
        completion_cost=1,
        completion_calls=completion_calls,
    )
    runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )

    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        runner.run(
            request=replace(request, prompt_hash="d" * 64),
            canonical_request=canonical_request,
            api_key="test-process-placeholder",
        )
    assert completion_calls == [1]


def test_transport_budget_error_is_replay_safe_inconclusive() -> None:
    request, canonical_request = build_request_v3(
        fixture=SyntheticRepairFixtureV1.default(),
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    balances = iter((100, 99))
    completion_calls: list[int] = []

    def reject_without_exact_cost(
        canonical_request: bytes,
        api_key: str,
    ) -> DeepSeekCompletionResultV1:
        assert canonical_request
        assert api_key == "test-process-placeholder"
        completion_calls.append(1)
        raise DeepSeekClientViolation("budget_exceeded")

    runner = OfflineModelGateRunnerV3(
        implementation_commit=_COMMIT,
        balance_reader=lambda: next(balances),
        completion=reject_without_exact_cost,
        verifier=lambda candidate: pytest.fail("verifier must not run"),
    )

    first = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )
    replay = runner.run(
        request=request,
        canonical_request=canonical_request,
        api_key="test-process-placeholder",
    )
    evidence = ModelGateEvidenceV3.from_json_bytes(first.evidence_bytes)

    assert first is replay
    assert first.decision.status == "inconclusive"
    assert first.decision.reason_codes == ("provider_call_ambiguous",)
    assert evidence.calculated_cost_micros_cny == 0
    assert evidence.provider_call_count == 1
    assert completion_calls == [1]


def test_v3_execution_requires_exact_v3_marker_before_dependencies() -> None:
    calls: list[str] = []

    for marker in (G2_A0_PAID_RUN_AUTHORIZATION, "near-miss", ""):
        with pytest.raises(
            ModelGateRunnerViolation, match="live_authorization_required"
        ):
            execute_probe_v3(
                api_key="test-process-placeholder",
                authorization_marker=marker,
                idempotency_key=_IDEMPOTENCY_KEY,
                implementation_commit=_COMMIT,
                balance_reader=lambda: calls.append("balance"),  # type: ignore[arg-type,func-returns-value]
                completion=lambda request, key: calls.append("completion"),  # type: ignore[arg-type,func-returns-value]
                verifier=lambda candidate: calls.append("verifier"),  # type: ignore[arg-type,func-returns-value]
            )
    assert calls == []


def test_v3_execution_uses_injected_dependencies_only(tmp_path: object) -> None:
    balances = iter((100, 99))
    completion_calls: list[int] = []

    evidence_bytes = execute_probe_v3(
        api_key="test-process-placeholder",
        authorization_marker=G2_A0_PAID_RUN_AUTHORIZATION_V3,
        idempotency_key=_IDEMPOTENCY_KEY,
        implementation_commit=_COMMIT,
        balance_reader=lambda: next(balances),
        completion=lambda request, key: completion_calls.append(1) or _completion(1),
        verifier=lambda candidate: verify_candidate_patch(
            fixture=SyntheticRepairFixtureV1.default(),
            candidate=candidate,
            temp_root=tmp_path,  # type: ignore[arg-type]
        ),
        source_binding_checker=lambda commit: None,
    )

    evidence = ModelGateEvidenceV3.from_json_bytes(evidence_bytes)
    assert evidence.decision_status == "admitted"
    assert completion_calls == [1]
