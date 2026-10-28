from __future__ import annotations

import hashlib
import io
import json
import socket
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path

import httpx
import pytest
from g2_a0_deepseek_client import (
    RESPONSE_EXAMPLE_JSON,
    CandidateArtifactV1,
    DeepSeekClientViolation,
    DeepSeekCompletionResultV1,
)
from g2_a0_model_gate_cli import (
    _RUNTIME_SOURCE_PATHS,
    G2_A0_PAID_RUN_AUTHORIZATION,
    ModelGateRunnerViolation,
    OfflineModelGateRunnerV1,
    _verify_runtime_source,
    execute_live_probe,
    main,
)
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1
from g2_a0_synthetic_verifier import (
    SyntheticVerificationResultV1,
    verify_candidate_patch,
)

from platform_protocol.g2_a0_model_gate import (
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    ModelGateRequestBindingV1,
    canonical_json_bytes,
)

IMPLEMENTATION_COMMIT = "d" * 40
API_KEY = "test-process-placeholder"
VALID_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,4 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool) or not isinstance(value, int):
+        raise TypeError("value must be an integer")
+    return max(0, min(100, value))
"""
PROMPT = (
    "Return json only. Repair the fixed synthetic fixture without tools. "
    f"Use this exact response shape: {RESPONSE_EXAMPLE_JSON}"
)
CANONICAL_REQUEST = canonical_json_bytes(
    {
        "max_tokens": 4_096,
        "messages": [{"content": PROMPT, "role": "user"}],
        "model": "deepseek-v4-flash-0731",
        "reasoning_effort": "max",
        "response_format": {"type": "json_object"},
        "stream": False,
        "thinking": {"type": "enabled"},
    }
)
_FIXTURE = SyntheticRepairFixtureV1.default()
FIXTURE_HASH = hashlib.sha256(
    canonical_json_bytes(
        {
            "fixture_version": _FIXTURE.fixture_version,
            "hidden_case_count": _FIXTURE.hidden_case_count,
            "public_case_count": _FIXTURE.public_case_count,
            "source_sha256": hashlib.sha256(_FIXTURE.source_bytes).hexdigest(),
        }
    )
).hexdigest()
SCHEMA_HASH = hashlib.sha256(RESPONSE_EXAMPLE_JSON.encode()).hexdigest()


def request_binding(**overrides: object) -> ModelGateRequestBindingV1:
    values: dict[str, object] = {
        "contract_version": "g2-a0-model-gate-request-v1",
        "idempotency_key": "idem_44444444444444444444444444444444",
        "policy": DeepSeekModelGatePolicyV1.default(),
        "prompt_hash": hashlib.sha256(PROMPT.encode()).hexdigest(),
        "fixture_hash": FIXTURE_HASH,
        "response_schema_hash": SCHEMA_HASH,
    }
    values.update(overrides)
    return ModelGateRequestBindingV1(**values)


def candidate() -> CandidateArtifactV1:
    return CandidateArtifactV1(
        artifact_version="g2-a0-candidate-v1",
        claimed_test_scope=("public_behavior",),
        language="python",
        summary_code="bounded_repair",
        unified_diff=VALID_PATCH,
    )


def completion_result() -> DeepSeekCompletionResultV1:
    return DeepSeekCompletionResultV1(
        returned_model="deepseek-v4-flash-0731",
        response_content_sha256="1" * 64,
        reasoning_sha256="2" * 64,
        system_fingerprint_sha256="3" * 64,
        input_tokens=10,
        output_tokens=5,
        cache_hit_input_tokens=4,
        cache_miss_input_tokens=6,
        calculated_cost_micros_cny=17,
        provider_call_count=1,
        candidate=candidate(),
    )


class BalanceReader:
    def __init__(self, values: tuple[int, ...] = (9_000_000, 8_999_983)) -> None:
        self._values = iter(values)
        self.calls = 0

    def __call__(self) -> int:
        self.calls += 1
        return next(self._values)


class Completion:
    def __init__(
        self,
        result: DeepSeekCompletionResultV1 | Exception | None = None,
    ) -> None:
        self.result = result or completion_result()
        self.calls = 0

    def __call__(
        self, canonical_request: bytes, api_key: str
    ) -> DeepSeekCompletionResultV1:
        assert canonical_request == CANONICAL_REQUEST
        assert api_key == API_KEY
        self.calls += 1
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class Verifier:
    def __init__(self, temp_root: Path, *, force_rejection: bool = False) -> None:
        self.temp_root = temp_root
        self.force_rejection = force_rejection
        self.calls = 0

    def __call__(self, value: CandidateArtifactV1) -> SyntheticVerificationResultV1:
        self.calls += 1
        result = verify_candidate_patch(
            fixture=SyntheticRepairFixtureV1.default(),
            candidate=value,
            temp_root=self.temp_root,
        )
        if not self.force_rejection:
            return result
        return replace(result, status="rejected", reason_code="oracle_failed")


def make_runner(
    tmp_path: Path,
    *,
    balances: BalanceReader | None = None,
    completion: Completion | None = None,
    verifier: Callable[[CandidateArtifactV1], SyntheticVerificationResultV1]
    | None = None,
) -> tuple[OfflineModelGateRunnerV1, BalanceReader, Completion, object]:
    balance_reader = balances or BalanceReader()
    completion_call = completion or Completion()
    verifier_call = verifier or Verifier(tmp_path)
    runner = OfflineModelGateRunnerV1(
        implementation_commit=IMPLEMENTATION_COMMIT,
        balance_reader=balance_reader,
        completion=completion_call,
        verifier=verifier_call,
    )
    return runner, balance_reader, completion_call, verifier_call


def test_one_request_runs_exact_state_machine_and_one_provider_call(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)

    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert result.decision.status == "admitted"
    assert result.decision.reason_codes == ()
    assert result.state_trace == (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "VALIDATED",
        "VERIFIED",
        "REPLAYED",
        "COMPLETE",
    )
    assert completion.calls == 1
    assert balances.calls == 2
    assert verifier.calls == 1
    assert (
        runner.validate_evidence_bytes(
            request=request_binding(),
            data=result.evidence_bytes,
        ).canonical_bytes
        == result.evidence_bytes
    )


def test_exact_replay_returns_original_result_without_call_growth(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)
    first = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    replay = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert replay is first
    assert completion.calls == 1
    assert balances.calls == 2
    assert verifier.calls == 1


def test_changed_replay_conflicts_before_balance_completion_or_verifier(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)
    original = request_binding()
    runner.run(
        request=original,
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    before = (balances.calls, completion.calls, verifier.calls)

    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        runner.run(
            request=replace(original, prompt_hash="f" * 64),
            canonical_request=CANONICAL_REQUEST,
            api_key=API_KEY,
        )

    assert (balances.calls, completion.calls, verifier.calls) == before


def test_changed_provider_request_bytes_conflict_before_any_call(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)
    request = request_binding()
    runner.run(
        request=request,
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    before = (balances.calls, completion.calls, verifier.calls)
    changed = json.loads(CANONICAL_REQUEST)
    changed["messages"][0]["content"] = f"{PROMPT} changed"

    with pytest.raises(ModelGateContractViolation, match="idempotency_conflict"):
        runner.run(
            request=request,
            canonical_request=canonical_json_bytes(changed),
            api_key=API_KEY,
        )

    assert (balances.calls, completion.calls, verifier.calls) == before


def test_first_request_must_bind_the_actual_prompt_before_any_call(
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)

    with pytest.raises(ModelGateRunnerViolation, match="prompt_binding_mismatch"):
        runner.run(
            request=replace(request_binding(), prompt_hash="f" * 64),
            canonical_request=CANONICAL_REQUEST,
            api_key=API_KEY,
        )

    assert (balances.calls, completion.calls, verifier.calls) == (0, 0, 0)


@pytest.mark.parametrize(
    ("case", "bad_value"),
    (
        ("model", "deepseek-v4-flash"),
        ("reasoning_effort", "high"),
        ("max_tokens", 4_095),
        ("thinking", {"type": "disabled"}),
        ("response_format", {"type": "text"}),
        ("stream", True),
        ("extra", "not-allowed"),
    ),
)
def test_runner_rejects_provider_request_policy_widening_before_any_call(
    case: str,
    bad_value: object,
    tmp_path: Path,
) -> None:
    runner, balances, completion, verifier = make_runner(tmp_path)
    document = json.loads(CANONICAL_REQUEST)
    document[case] = bad_value

    with pytest.raises(ModelGateRunnerViolation, match="provider_request_mismatch"):
        runner.run(
            request=request_binding(),
            canonical_request=canonical_json_bytes(document),
            api_key=API_KEY,
        )

    assert (balances.calls, completion.calls, verifier.calls) == (0, 0, 0)


def test_provider_ambiguity_is_inconclusive_and_never_repeated(tmp_path: Path) -> None:
    provider = Completion(RuntimeError("raw provider detail must not escape"))
    runner, balances, _, verifier = make_runner(tmp_path, completion=provider)

    first = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    replay = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert first is replay
    assert first.decision.status == "inconclusive"
    assert first.decision.reason_codes == ("provider_call_ambiguous",)
    assert first.state_trace == (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "INCONCLUSIVE",
        "REPLAYED",
        "COMPLETE",
    )
    assert balances.calls == 2
    assert provider.calls == 1
    assert verifier.calls == 0
    assert b"raw provider detail" not in first.evidence_bytes


@pytest.mark.parametrize("failure", ("provider", "verifier"))
def test_rejected_completion_or_verifier_cannot_admit(
    failure: str,
    tmp_path: Path,
) -> None:
    completion = Completion(DeepSeekClientViolation("structured_output_invalid"))
    verifier = Verifier(tmp_path, force_rejection=True)
    runner, _, _, _ = make_runner(
        tmp_path,
        completion=completion if failure == "provider" else None,
        verifier=verifier,
    )

    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )

    assert result.decision.status == "rejected"
    assert result.decision.reason_codes == (
        "structured_output_invalid"
        if failure == "provider"
        else "candidate_verification_failed",
    )
    assert b'"status":"admitted"' not in result.evidence_bytes


def test_evidence_is_redacted_and_contains_only_delta_not_raw_balances(
    tmp_path: Path,
) -> None:
    runner, _, _, _ = make_runner(tmp_path)
    result = runner.run(
        request=request_binding(),
        canonical_request=CANONICAL_REQUEST,
        api_key=API_KEY,
    )
    document = json.loads(result.evidence_bytes)

    assert document["balance_delta_micros_cny"] == 17
    assert document["balance_delta_status"] == "known"
    assert document["provider_call_count"] == 1
    assert document["balance_read_count"] == 2
    assert document["replay_provider_call_growth"] == 0
    assert document["fixture_hash"] == FIXTURE_HASH
    assert document["response_schema_hash"] == SCHEMA_HASH
    prohibited = (
        API_KEY,
        "9000000",
        "8999983",
        "synthetic_target.py",
        "value must be an integer",
        "raw provider",
        "Authorization",
    )
    assert all(marker.encode() not in result.evidence_bytes for marker in prohibited)


def test_offline_cli_is_byte_stable_and_live_refuses_before_environment_read() -> None:
    first = io.BytesIO()
    second = io.BytesIO()

    assert (
        main(
            ["--offline-fixture"],
            output=first,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=lambda commit: None,
        )
        == 0
    )
    assert (
        main(
            ["--offline-fixture"],
            output=second,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=lambda commit: None,
        )
        == 0
    )
    assert first.getvalue() == second.getvalue()
    assert first.getvalue().count(b"\n") == 1

    class DenyEnvironment(dict[str, str]):
        def get(self, key: str, default: object = None) -> str | None:
            raise AssertionError("environment must not be read before authorization")

    denied = io.BytesIO()
    assert (
        main(
            [
                "--live",
                "--authorization-marker",
                "wrong",
                "--implementation-commit",
                IMPLEMENTATION_COMMIT,
                "--idempotency-key",
                request_binding().idempotency_key,
            ],
            environment=DenyEnvironment(),
            output=denied,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
        )
        == 2
    )
    assert denied.getvalue() == (
        b'{"reason_code":"live_authorization_required","status":"rejected"}\n'
    )
    assert G2_A0_PAID_RUN_AUTHORIZATION.encode() not in denied.getvalue()


def test_offline_fixture_refuses_dirty_runtime_source_before_evidence() -> None:
    source_checks = 0

    def reject_source(commit: str) -> None:
        nonlocal source_checks
        source_checks += 1
        assert commit == IMPLEMENTATION_COMMIT
        raise ModelGateRunnerViolation("source_binding_mismatch")

    output = io.BytesIO()
    assert (
        main(
            ["--offline-fixture"],
            output=output,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=reject_source,
        )
        == 2
    )
    assert source_checks == 1
    assert output.getvalue() == (
        b'{"reason_code":"source_binding_mismatch","status":"rejected"}\n'
    )


def test_live_preflight_requires_exact_source_and_nonempty_process_key() -> None:
    execute_calls = 0

    def execute_live(**kwargs: object) -> bytes:
        nonlocal execute_calls
        execute_calls += 1
        return canonical_json_bytes({"status": "admitted"})

    arguments = [
        "--live",
        "--authorization-marker",
        G2_A0_PAID_RUN_AUTHORIZATION,
        "--implementation-commit",
        IMPLEMENTATION_COMMIT,
        "--idempotency-key",
        request_binding().idempotency_key,
    ]
    wrong_source = io.BytesIO()
    assert (
        main(
            arguments,
            environment={"DEEPSEEK_API_KEY": API_KEY},
            output=wrong_source,
            source_commit_reader=lambda: "e" * 40,
            live_execute=execute_live,
        )
        == 2
    )
    assert execute_calls == 0

    missing_key = io.BytesIO()
    assert (
        main(
            arguments,
            environment={},
            output=missing_key,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=lambda commit: None,
            live_execute=execute_live,
        )
        == 2
    )
    assert execute_calls == 0

    malformed_key = io.BytesIO()
    assert (
        main(
            arguments,
            environment={"DEEPSEEK_API_KEY": "contains whitespace"},
            output=malformed_key,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=lambda commit: None,
            live_execute=execute_live,
        )
        == 2
    )
    assert execute_calls == 0

    malformed = io.BytesIO()
    assert (
        main(
            arguments,
            environment={"DEEPSEEK_API_KEY": API_KEY},
            output=malformed,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=lambda commit: None,
            live_execute=execute_live,
        )
        == 2
    )
    assert execute_calls == 1
    assert malformed.getvalue() == (
        b'{"reason_code":"live_execution_failed","status":"rejected"}\n'
    )
    assert API_KEY.encode() not in malformed.getvalue()


def test_live_source_blob_mismatch_stops_before_environment_or_executor() -> None:
    execute_calls = 0
    source_checks = 0

    class DenyEnvironment(dict[str, str]):
        def get(self, key: str, default: object = None) -> str | None:
            raise AssertionError("key must not be read after source mismatch")

    def reject_source(commit: str) -> None:
        nonlocal source_checks
        source_checks += 1
        assert commit == IMPLEMENTATION_COMMIT
        raise ModelGateRunnerViolation("source_binding_mismatch")

    def execute_live(**kwargs: object) -> bytes:
        nonlocal execute_calls
        execute_calls += 1
        raise AssertionError("executor must not run after source mismatch")

    output = io.BytesIO()
    assert (
        main(
            [
                "--live",
                "--authorization-marker",
                G2_A0_PAID_RUN_AUTHORIZATION,
                "--implementation-commit",
                IMPLEMENTATION_COMMIT,
                "--idempotency-key",
                request_binding().idempotency_key,
            ],
            environment=DenyEnvironment(),
            output=output,
            source_commit_reader=lambda: IMPLEMENTATION_COMMIT,
            source_binding_checker=reject_source,
            live_execute=execute_live,
        )
        == 2
    )
    assert source_checks == 1
    assert execute_calls == 0
    assert output.getvalue() == (
        b'{"reason_code":"source_binding_mismatch","status":"rejected"}\n'
    )


def test_runtime_source_binding_compares_every_file_byte_for_byte(
    tmp_path: Path,
) -> None:
    expected_blobs: dict[str, bytes] = {}
    read_paths: list[str] = []
    for relative_path in _RUNTIME_SOURCE_PATHS:
        payload = f"committed:{relative_path}\n".encode()
        expected_blobs[relative_path] = payload
        current_path = tmp_path / relative_path
        current_path.parent.mkdir(parents=True, exist_ok=True)
        current_path.write_bytes(payload)

    def read_blob(repository: Path, commit: str, path: str) -> bytes:
        assert repository == tmp_path
        assert commit == IMPLEMENTATION_COMMIT
        read_paths.append(path)
        return expected_blobs[path]

    _verify_runtime_source(
        IMPLEMENTATION_COMMIT,
        repository=tmp_path,
        blob_reader=read_blob,
    )
    assert read_paths == list(_RUNTIME_SOURCE_PATHS)

    (tmp_path / _RUNTIME_SOURCE_PATHS[0]).write_bytes(b"dirty runtime bytes\n")
    with pytest.raises(ModelGateRunnerViolation, match="source_binding_mismatch"):
        _verify_runtime_source(
            IMPLEMENTATION_COMMIT,
            repository=tmp_path,
            blob_reader=read_blob,
        )


def test_live_probe_uses_mocked_balance_completion_balance_and_one_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    paths: list[str] = []
    balances = iter(("9.000000", "8.999983"))

    def deny_socket(*args: object, **kwargs: object) -> socket.socket:
        raise AssertionError("real network is prohibited")

    monkeypatch.setattr(socket, "socket", deny_socket)

    def handler(request: httpx.Request) -> httpx.Response:
        paths.append(request.url.path)
        assert request.headers["authorization"] == f"Bearer {API_KEY}"
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
        assert request.url.path == "/chat/completions"
        content = json.dumps(
            {
                "artifact_version": "g2-a0-candidate-v1",
                "claimed_test_scope": ["public_behavior"],
                "language": "python",
                "summary_code": "bounded_repair",
                "unified_diff": VALID_PATCH,
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
                "id": "chatcmpl_synthetic_01",
                "model": "deepseek-v4-flash-0731",
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

    evidence = execute_live_probe(
        api_key=API_KEY,
        authorization_marker=G2_A0_PAID_RUN_AUTHORIZATION,
        idempotency_key=request_binding().idempotency_key,
        implementation_commit=IMPLEMENTATION_COMMIT,
        transport_factory=lambda: httpx.MockTransport(handler),
    )
    document = json.loads(evidence)

    assert paths == ["/user/balance", "/chat/completions", "/user/balance"]
    assert document["decision_status"] == "admitted"
    assert document["provider_call_count"] == 1
    assert document["balance_read_count"] == 2
    assert document["replay_count"] == 1
    assert document["replay_provider_call_growth"] == 0
    assert document["balance_delta_micros_cny"] == 17
    assert document["balance_delta_status"] == "known"
    assert API_KEY.encode() not in evidence


def test_fixture_hash_is_not_a_hash_of_raw_source_only() -> None:
    fixture = SyntheticRepairFixtureV1.default()
    assert (
        request_binding().fixture_hash
        != hashlib.sha256(fixture.source_bytes).hexdigest()
    )
