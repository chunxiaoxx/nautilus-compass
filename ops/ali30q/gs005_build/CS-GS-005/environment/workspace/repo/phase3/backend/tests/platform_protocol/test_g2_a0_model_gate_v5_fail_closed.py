from __future__ import annotations

import json
import socket
from pathlib import Path

import httpx
import pytest
from g2_a0_model_gate_cli import (
    _RUNTIME_SOURCE_PATHS,
    G2_A0_PAID_RUN_AUTHORIZATION,
    ModelGateEvidenceV1,
    ModelGateRunnerViolation,
    _offline_evidence,
)
from g2_a0_model_gate_v5_cli import (
    _RUNTIME_SOURCE_PATHS_V5,
    G2_A0_PAID_RUN_AUTHORIZATION_V5,
    ModelGateEvidenceV5,
    OfflineModelGateRunnerV5,
    _verify_runtime_source_v5,
    execute_live_probe_v5,
)

from platform_protocol.g2_a0_model_gate import (
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    ModelGateRequestBindingV1,
    canonical_json_bytes,
)

_COMMIT = "4" * 40
_API_KEY = "test-process-placeholder"
_IDEMPOTENCY_KEY = "idem_44444444444444444444444444444444"
_VALID_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,4 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool) or not isinstance(value, int):
+        raise TypeError("value must be an integer")
+    return max(0, min(100, value))
"""


def _v1_request() -> ModelGateRequestBindingV1:
    return ModelGateRequestBindingV1(
        contract_version="g2-a0-model-gate-request-v1",
        idempotency_key=_IDEMPOTENCY_KEY,
        policy=DeepSeekModelGatePolicyV1.default(),
        prompt_hash="a" * 64,
        fixture_hash="b" * 64,
        response_schema_hash="c" * 64,
    )


def test_v5_runtime_source_binding_includes_v1_and_exact_v5_files(
    tmp_path: Path,
) -> None:
    assert _RUNTIME_SOURCE_PATHS_V5 == (
        *_RUNTIME_SOURCE_PATHS,
        "phase3/backend/platform_protocol/g2_a0_model_gate_v5.py",
        "phase3/backend/tests/platform_protocol/g2_a0_model_gate_v5_cli.py",
    )
    blobs: dict[str, bytes] = {}
    reads: list[str] = []
    for relative_path in _RUNTIME_SOURCE_PATHS_V5:
        payload = f"committed:{relative_path}\n".encode()
        blobs[relative_path] = payload
        path = tmp_path / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)

    def read_blob(repository: Path, commit: str, relative_path: str) -> bytes:
        assert repository == tmp_path
        assert commit == _COMMIT
        reads.append(relative_path)
        return blobs[relative_path]

    _verify_runtime_source_v5(
        _COMMIT,
        repository=tmp_path,
        blob_reader=read_blob,
    )
    assert reads == list(_RUNTIME_SOURCE_PATHS_V5)

    (tmp_path / _RUNTIME_SOURCE_PATHS_V5[-1]).write_bytes(b"tampered\n")
    with pytest.raises(ModelGateRunnerViolation, match="source_binding_mismatch"):
        _verify_runtime_source_v5(
            _COMMIT,
            repository=tmp_path,
            blob_reader=read_blob,
        )


def test_v1_and_v5_requests_and_evidence_are_not_interchangeable() -> None:
    runner = OfflineModelGateRunnerV5(
        implementation_commit=_COMMIT,
        balance_reader=lambda: 0,
        completion=lambda request, key: None,  # type: ignore[arg-type,return-value]
        verifier=lambda candidate: None,  # type: ignore[arg-type,return-value]
    )
    with pytest.raises(ModelGateRunnerViolation, match="invalid_request"):
        runner.run(
            request=_v1_request(),  # type: ignore[arg-type]
            canonical_request=b"{}",
            api_key=_API_KEY,
        )

    v1_document = {
        "balance_delta_micros_cny": 0,
        "balance_delta_status": "known",
        "balance_read_count": 2,
        "cache_hit_input_tokens": 0,
        "cache_miss_input_tokens": 0,
        "calculated_cost_micros_cny": 0,
        "candidate_sha256": None,
        "child_process_count": 0,
        "contract_version": "g2-a0-model-gate-evidence-v1",
        "decision_status": "rejected",
        "fixture_cleanup_count": 0,
        "fixture_hash": "a" * 64,
        "hidden_case_count": 0,
        "implementation_commit": _COMMIT,
        "input_tokens": 0,
        "network_call_count": 0,
        "oracle_output_sha256": None,
        "output_tokens": 0,
        "patched_sha256": None,
        "policy_hash": "b" * 64,
        "provider_call_count": 1,
        "public_case_count": 0,
        "reason_codes": ["policy_violation"],
        "reasoning_sha256": None,
        "replay_count": 1,
        "replay_provider_call_growth": 0,
        "request_hash": "c" * 64,
        "response_content_sha256": None,
        "response_schema_hash": "d" * 64,
        "returned_model": None,
        "source_sha256": None,
        "source_write_count": 0,
        "state_trace": [
            "NEW",
            "BALANCE_READ",
            "CALLING",
            "REJECTED",
            "REPLAYED",
            "COMPLETE",
        ],
        "system_fingerprint_sha256": None,
    }
    v1_bytes = canonical_json_bytes(v1_document)
    v2_document = dict(v1_document)
    v2_document["contract_version"] = "g2-a0-model-gate-evidence-v5"
    v2_bytes = canonical_json_bytes(v2_document)

    with pytest.raises(ModelGateRunnerViolation, match="invalid_contract_version"):
        ModelGateEvidenceV5.from_json_bytes(v1_bytes)
    with pytest.raises(ModelGateRunnerViolation, match="invalid_contract_version"):
        ModelGateEvidenceV1.from_json_bytes(v2_bytes)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("provider_call_count", False),
        ("calculated_cost_micros_cny", True),
        ("balance_delta_micros_cny", False),
        ("replay_count", True),
    ),
)
def test_v5_evidence_rejects_bool_counters_and_costs(
    field_name: str,
    bad_value: bool,
) -> None:
    document = json.loads(
        canonical_json_bytes(
            {
                **json.loads(
                    ModelGateEvidenceV1(
                        contract_version="g2-a0-model-gate-evidence-v1",
                        implementation_commit=_COMMIT,
                        request_hash="a" * 64,
                        policy_hash="b" * 64,
                        fixture_hash="c" * 64,
                        response_schema_hash="d" * 64,
                        decision_status="rejected",
                        reason_codes=("policy_violation",),
                        returned_model=None,
                        response_content_sha256=None,
                        reasoning_sha256=None,
                        system_fingerprint_sha256=None,
                        candidate_sha256=None,
                        source_sha256=None,
                        patched_sha256=None,
                        oracle_output_sha256=None,
                        input_tokens=0,
                        output_tokens=0,
                        cache_hit_input_tokens=0,
                        cache_miss_input_tokens=0,
                        calculated_cost_micros_cny=0,
                        balance_delta_micros_cny=0,
                        balance_delta_status="known",
                        provider_call_count=1,
                        balance_read_count=2,
                        replay_count=1,
                        replay_provider_call_growth=0,
                        public_case_count=0,
                        hidden_case_count=0,
                        source_write_count=0,
                        network_call_count=0,
                        child_process_count=0,
                        fixture_cleanup_count=0,
                        state_trace=(
                            "NEW",
                            "BALANCE_READ",
                            "CALLING",
                            "REJECTED",
                            "REPLAYED",
                            "COMPLETE",
                        ),
                    ).canonical_bytes
                ),
                "contract_version": "g2-a0-model-gate-evidence-v5",
            }
        )
    )
    document[field_name] = bad_value

    with pytest.raises(ModelGateRunnerViolation, match=f"invalid_{field_name}"):
        ModelGateEvidenceV5.from_json_bytes(canonical_json_bytes(document))


def test_v5_evidence_rejects_duplicate_and_extra_fields() -> None:
    with pytest.raises(ModelGateContractViolation, match="duplicate_json_key"):
        ModelGateEvidenceV5.from_json_bytes(b'{"a":1,"a":2}')
    with pytest.raises(ModelGateRunnerViolation, match="unexpected_evidence_fields"):
        ModelGateEvidenceV5.from_json_bytes(canonical_json_bytes({"extra": True}))


@pytest.mark.parametrize(
    ("calculated_cost", "balance_delta"),
    (
        (10_000_001, 1),
        (1, 10_000_001),
    ),
)
def test_v5_evidence_rejects_admitted_cost_over_cny_10(
    calculated_cost: int,
    balance_delta: int,
) -> None:
    document = json.loads(_offline_evidence(_COMMIT))
    document["returned_model"] = "deepseek-v4-flash"
    document["contract_version"] = "g2-a0-model-gate-evidence-v5"
    document["calculated_cost_micros_cny"] = calculated_cost
    document["balance_delta_micros_cny"] = balance_delta

    with pytest.raises(ModelGateRunnerViolation, match="budget_evidence_mismatch"):
        ModelGateEvidenceV5.from_json_bytes(canonical_json_bytes(document))


def test_v5_budget_rejection_requires_an_actual_over_limit_cost() -> None:
    document = json.loads(_offline_evidence(_COMMIT))
    document["returned_model"] = "deepseek-v4-flash"
    document["contract_version"] = "g2-a0-model-gate-evidence-v5"
    document["decision_status"] = "rejected"
    document["reason_codes"] = ["budget_exceeded"]
    document["state_trace"] = [
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "REJECTED",
        "REPLAYED",
        "COMPLETE",
    ]
    document["calculated_cost_micros_cny"] = 10_000_000
    document["balance_delta_micros_cny"] = 10_000_000

    with pytest.raises(ModelGateRunnerViolation, match="budget_evidence_mismatch"):
        ModelGateEvidenceV5.from_json_bytes(canonical_json_bytes(document))


def test_every_byte_bound_v5_runtime_file_has_permanent_lf_policy() -> None:
    repository = Path(__file__).resolve().parents[4]
    production_attributes = (
        repository / "phase3/backend/platform_protocol/.gitattributes"
    ).read_text(encoding="utf-8")
    test_attributes = (
        repository / "phase3/backend/tests/platform_protocol/.gitattributes"
    ).read_text(encoding="utf-8")

    assert "g2_a0_model_gate_v5.py text eol=lf" in production_attributes.splitlines()
    assert "g2_a0_model_gate_v5_cli.py text eol=lf" in test_attributes.splitlines()


def test_v5_live_probe_uses_only_mock_transport_and_exact_three_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths: list[str] = []
    balances = iter(("20.000000", "10.000000"))

    def deny_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("real network is prohibited")

    monkeypatch.setattr(socket, "socket", deny_socket)

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.headers["authorization"] == f"Bearer {_API_KEY}"
        if request.url.path == "/user/balance":
            total = next(balances)
            return httpx.Response(
                200,
                json={
                    "balance_infos": [
                        {
                            "currency": "CNY",
                            "granted_balance": "0.000000",
                            "topped_up_balance": total,
                            "total_balance": total,
                        }
                    ],
                    "is_available": True,
                },
                headers={"content-type": "application/json"},
            )
        content = json.dumps(
            {
                "artifact_version": "g2-a0-candidate-v1",
                "claimed_test_scope": ["public_behavior"],
                "language": "python",
                "summary_code": "bounded_repair",
                "unified_diff": _VALID_PATCH,
            },
            separators=(",", ":"),
            sort_keys=True,
        )
        return httpx.Response(
            200,
            json={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "index": 0,
                        "message": {
                            "content": content,
                            "reasoning_content": "synthetic-reasoning-marker",
                            "role": "assistant",
                        },
                    }
                ],
                "created": 1_786_646_400,
                "id": "chatcmpl_synthetic_v5",
                "model": "deepseek-v4-flash",
                "object": "chat.completion",
                "system_fingerprint": "fp_synthetic_0731",
                "usage": {
                    "completion_tokens": 5,
                    "prompt_cache_hit_tokens": 4,
                    "prompt_cache_miss_tokens": 6,
                    "prompt_tokens": 10,
                    "total_tokens": 15,
                },
            },
            headers={"content-type": "application/json"},
        )

    evidence = execute_live_probe_v5(
        api_key=_API_KEY,
        authorization_marker=G2_A0_PAID_RUN_AUTHORIZATION_V5,
        idempotency_key=_IDEMPOTENCY_KEY,
        implementation_commit=_COMMIT,
        transport_factory=lambda: httpx.MockTransport(handler),
        source_binding_checker=lambda commit: None,
    )
    document = json.loads(evidence)

    assert paths == ["/user/balance", "/chat/completions", "/user/balance"]
    assert document["contract_version"] == "g2-a0-model-gate-evidence-v5"
    assert document["decision_status"] == "admitted"
    assert document["provider_call_count"] == 1
    assert document["balance_delta_micros_cny"] == 10_000_000
    assert _API_KEY.encode() not in evidence
    assert G2_A0_PAID_RUN_AUTHORIZATION.encode() not in evidence
