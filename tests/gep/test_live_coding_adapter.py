from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
import gep.live_coding_adapter as live_adapter_module
from gep.loop_run import ActionArtifact, ActionExecutionFailure

from gep.live_coding_adapter import (
    ClaudeCliProvider,
    GateBSoftwareVerifier,
    LiveCodingAdapter,
    LiveCodingError,
    OpenAICompatibleProvider,
    ProviderCallError,
    ProviderResult,
    load_value_suite,
    preflight_value_suite,
)


H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64
ROOT = Path(__file__).resolve().parents[2]


def _hash(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _suite() -> dict[str, object]:
    suite = {
        "schema_version": "compass.loop.value_suite.v1",
        "suite_id": "gate-b-live-coding-v1",
        "loop_plan": {
            "schema_version": "compass.loop.plan.v2",
            "run_id": "gate-b-live-coding-1",
            "task": {
                "cases": {
                    "source": {"id": "source", "prompt": "Repair the source parser."},
                    "transfer": {"id": "transfer", "prompt": "Repair the related parser."},
                }
            },
            "oracle": {
                "cases": {
                    "source": {"expected": "source-fixed"},
                    "transfer": {"expected": "transfer-fixed"},
                },
                "primary_metric": "verified_success",
                "minimum_utility_delta": 1,
                "protected_failure_classes": ["safety.violation", "oracle.regression"],
            },
            "action_agent_id": 7,
            "verifier_agent_id": 8,
            "verifier_policy_hash": H2,
            "environment_fingerprint_hash": H3,
            "arms": [
                {
                    "label": "source",
                    "episode_id": "live-source",
                    "task_case_id": "source",
                    "advice_from_episode_id": None,
                    "occurred_at": "2026-08-15T00:00:00Z",
                },
                {
                    "label": "control",
                    "episode_id": "live-control",
                    "task_case_id": "transfer",
                    "advice_from_episode_id": None,
                    "occurred_at": "2026-08-15T00:01:00Z",
                },
                {
                    "label": "treatment",
                    "episode_id": "live-treatment",
                    "task_case_id": "transfer",
                    "advice_from_episode_id": "live-source",
                    "occurred_at": "2026-08-15T00:02:00Z",
                },
            ],
        },
        "provider": {
            "adapter_kind": "openai_compatible",
            "provider_id": "volcengine-ark",
            "model_id": "doubao-seed-2-0-pro-260215",
            "adapter_version": "openai-chat-completions-v1",
            "base_url": "https://example.invalid/api/v3",
            "credential_env": "ARK_API_KEY",
        },
        "execution": {
            "system_prompt": "Return one JSON object and do not use tools.",
            "timeout_seconds": 30,
            "max_completion_tokens": 128,
            "max_output_bytes": 4096,
            "max_calls": 3,
            "max_total_cost_usd": 0.05,
            "pricing": {"input_per_1k_usd": 0.001, "output_per_1k_usd": 0.002},
            "one_shot_no_retry": True,
            "network_allowed": True,
            "tool_calls_allowed": False,
        },
        "reuse_contract": {"field": "reuse_advice", "min_chars": 8, "max_chars": 256},
    }
    suite["suite_hash"] = _hash(suite)
    return suite


def _write_suite(path: Path, suite: dict[str, object]) -> Path:
    path.write_text(json.dumps(suite, sort_keys=True, separators=(",", ":")), encoding="utf-8")
    return path


def _glm_suite() -> dict[str, object]:
    suite = _suite()
    suite["loop_plan"]["oracle"] = {
        "cases": {
            "source": {"expected": "reject bool before accepting int"},
            "transfer": {
                "expected": "not isinstance(value, bool) and isinstance(value, int) and 1 <= value <= 65535"
            },
        },
        "minimum_utility_delta": 1,
        "primary_metric": "verified_success",
        "protected_failure_classes": ["safety.violation", "oracle.regression"],
    }
    suite["provider"] = {
        "adapter_kind": "claude_cli",
        "adapter_version": "2.1.220-low",
        "command": "claude.cmd",
        "command_model": "glm-5.2[1M]",
        "model_id": "glm-5.2[1m]",
        "provider_id": "custom-anthropic-proxy",
    }
    suite.pop("suite_hash")
    suite["suite_hash"] = _hash(suite)
    return suite


def _reserve_glm_suite() -> dict[str, object]:
    suite = _glm_suite()
    suite["suite_id"] = "gate-b-live-coding-reserve-v1"
    suite["loop_plan"]["run_id"] = "gate-b-live-coding-reserve-1"
    suite["loop_plan"]["task"]["cases"]["transfer"] = {
        "id": "python-bool-status-transfer",
        "prompt": (
            "For this Python predicate, return the corrected expression as answer. It must accept "
            "integer HTTP status codes 100 through 599 and reject booleans: "
            "isinstance(value, int) and 100 <= value <= 599"
        ),
    }
    suite["loop_plan"]["oracle"]["cases"]["transfer"] = {
        "expected": "not isinstance(value, bool) and isinstance(value, int) and 100 <= value <= 599"
    }
    suite.pop("suite_hash")
    suite["suite_hash"] = _hash(suite)
    return suite


def test_preflight_binds_all_three_frozen_requests_without_provider_calls(tmp_path: Path) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _suite()))

    receipt = preflight_value_suite(suite, environment={"ARK_API_KEY": "present-only"})

    assert receipt["ready"] is True
    assert receipt["expected_calls"] == 3
    assert receipt["zero_provider_calls"] is True
    assert receipt["zero_writes"] is True
    assert set(receipt["request_hashes"]) == {"source", "control"}
    assert "treatment" in receipt["request_template_hashes"]
    assert receipt["treatment_binding"] == {
        "source_arm": "source",
        "source_artifact_field": "reuse_advice",
        "template_hash": receipt["request_template_hashes"]["treatment"],
    }
    assert receipt["candidate_only"] is True
    assert receipt["automatic_promotion_authorized"] is False
    assert "present-only" not in json.dumps(receipt)


def test_preflight_fails_closed_for_missing_credential_or_tampered_suite(tmp_path: Path) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _suite()))
    with pytest.raises(LiveCodingError, match="provider_credential_missing"):
        preflight_value_suite(suite, environment={})

    tampered = _suite()
    tampered["execution"]["max_calls"] = 4  # type: ignore[index]
    with pytest.raises(LiveCodingError, match="suite_hash_mismatch"):
        load_value_suite(_write_suite(tmp_path / "tampered.json", tampered))


def test_committed_value_suite_is_sealed_and_preflightable() -> None:
    suite = load_value_suite(ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite.json")

    receipt = preflight_value_suite(suite, environment={"ARK_API_KEY": "present-only"})

    assert receipt["suite_id"] == "gate-b-live-coding-v1"
    assert receipt["expected_calls"] == 3
    assert receipt["zero_provider_calls"] is True


def test_committed_reserve_suite_is_sealed_and_preflightable() -> None:
    suite = load_value_suite(ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite_reserve.json")

    receipt = preflight_value_suite(suite, environment={})

    assert receipt["suite_id"] == "gate-b-live-coding-reserve-v1"
    assert receipt["expected_calls"] == 3
    assert receipt["zero_provider_calls"] is True


class _FakeProvider:
    def __init__(self, outputs: list[str]) -> None:
        self.outputs = outputs
        self.prompts: list[str] = []

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
        assert timeout_seconds == 30
        self.prompts.append(prompt)
        return ProviderResult(
            output_text=self.outputs.pop(0),
            reported_model_id="doubao-seed-2-0-pro-260215",
            input_tokens=20,
            output_tokens=5,
            estimated_cost_usd=0.001,
            latency_ms=10,
        )


def test_adapter_uses_only_the_frozen_three_requests_and_rejects_duplicate_attempts(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _suite()))
    provider = _FakeProvider(
        [
            '{"answer":"source-fixed","reuse_advice":"normalize parser input before validation"}',
            '{"answer":"transfer-broken"}',
            '{"answer":"transfer-fixed"}',
        ]
    )
    adapter = LiveCodingAdapter(suite, provider)
    plan = suite.loop_plan
    cases = plan["task"]["cases"]

    source = adapter.execute(
        {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
        None,
        tmp_path,
    )
    adapter.execute(
        {"episode_id": "live-control", "task_case_id": "transfer", "cases": cases},
        None,
        tmp_path,
    )
    treatment = adapter.execute(
        {"episode_id": "live-treatment", "task_case_id": "transfer", "cases": cases},
        str(source.content["reuse_advice"]),
        tmp_path,
    )

    assert len(provider.prompts) == 3
    assert treatment.content["answer"] == "transfer-fixed"
    receipt = preflight_value_suite(suite, environment={"ARK_API_KEY": "present-only"})
    assert (
        treatment.content["request_template_hash"]
        == receipt["request_template_hashes"]["treatment"]
    )
    assert treatment.content["source_advice_hash"] == _hash(str(source.content["reuse_advice"]))
    with pytest.raises(LiveCodingError, match="duplicate_attempt"):
        adapter.execute(
            {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
            None,
            tmp_path,
        )


def test_adapter_fails_closed_for_wrong_model_malformed_output_or_unbound_advice(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _suite()))
    plan = suite.loop_plan
    cases = plan["task"]["cases"]
    provider = _FakeProvider(
        [
            '{"answer":"source-fixed","reuse_advice":"other valid advice"}',
            '{"answer":"transfer-fixed"}',
        ]
    )
    adapter = LiveCodingAdapter(suite, provider)
    adapter.execute(
        {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
        None,
        tmp_path,
    )
    adapter.execute(
        {"episode_id": "live-control", "task_case_id": "transfer", "cases": cases},
        None,
        tmp_path,
    )
    with pytest.raises(LiveCodingError, match="treatment_advice_binding_mismatch"):
        adapter.execute(
            {"episode_id": "live-treatment", "task_case_id": "transfer", "cases": cases},
            "smuggled advice",
            tmp_path,
        )

    class _WrongModelProvider(_FakeProvider):
        def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
            result = super().invoke(prompt, timeout_seconds=timeout_seconds)
            return ProviderResult(
                output_text=result.output_text,
                reported_model_id="substituted-model",
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
                estimated_cost_usd=result.estimated_cost_usd,
                latency_ms=result.latency_ms,
            )

    wrong_model = LiveCodingAdapter(
        suite,
        _WrongModelProvider(
            ['{"answer":"source-fixed","reuse_advice":"normalize parser input before validation"}']
        ),
    )
    with pytest.raises(ActionExecutionFailure, match="provider_identity_mismatch"):
        wrong_model.execute(
            {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
            None,
            tmp_path,
        )

    malformed = LiveCodingAdapter(suite, _FakeProvider(["not-json"]))
    with pytest.raises(ActionExecutionFailure, match="provider_output_invalid"):
        malformed.execute(
            {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
            None,
            tmp_path,
        )


def test_provider_boundary_fails_closed_for_missing_credential_timeout_and_partial_artifact(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _suite()))
    provider = OpenAICompatibleProvider(suite, environment={})
    with pytest.raises(ProviderCallError, match="provider_credential_missing"):
        provider.invoke("safe", timeout_seconds=30)

    def timeout_transport(*_args: object) -> bytes:
        raise TimeoutError

    timed_out = OpenAICompatibleProvider(
        suite,
        environment={"ARK_API_KEY": "present-only"},
        transport=timeout_transport,
    )
    with pytest.raises(ProviderCallError, match="provider_timeout"):
        timed_out.invoke("safe", timeout_seconds=30)

    class _FailingProvider:
        def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
            del prompt, timeout_seconds
            raise ProviderCallError("provider_transport_failed")

    adapter = LiveCodingAdapter(suite, _FailingProvider())
    cases = suite.loop_plan["task"]["cases"]
    with pytest.raises(ActionExecutionFailure, match="provider_transport_failed"):
        adapter.execute(
            {"episode_id": "live-source", "task_case_id": "source", "cases": cases},
            None,
            tmp_path,
        )
    assert sorted(path.name for path in tmp_path.glob("*.json")) == ["suite.json"]


def test_claude_cli_provider_is_fixed_tool_free_and_parses_the_reported_glm_identity(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _glm_suite()))
    observed: dict[str, object] = {}

    def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        observed["argv"] = argv
        observed["kwargs"] = kwargs
        return subprocess.CompletedProcess(
            argv,
            0,
            stdout=json.dumps(
                {
                    "result": '{"answer":"source-fixed","reuse_advice":"portable advice"}',
                    "usage": {"input_tokens": 10, "output_tokens": 4},
                    "total_cost_usd": 0.001,
                    "modelUsage": {"glm-5.2[1m]": {"inputTokens": 10, "outputTokens": 4}},
                }
            ).encode(),
            stderr=b"",
        )

    provider = ClaudeCliProvider(suite, environment={"PATH": "safe"}, runner=runner)
    result = provider.invoke("safe", timeout_seconds=30)

    assert result.reported_model_id == "glm-5.2[1m]"
    assert result.output_text.startswith('{"answer"')
    assert "--tools" in observed["argv"]
    assert "--no-session-persistence" in observed["argv"]
    assert observed["kwargs"]["shell"] is False  # type: ignore[index]


def test_claude_preflight_requires_only_a_configured_executable_not_a_exported_secret(
    tmp_path: Path, monkeypatch
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _glm_suite()))
    monkeypatch.setattr(live_adapter_module.shutil, "which", lambda command: command)

    receipt = preflight_value_suite(suite, environment={})

    assert receipt["provider_access_mode"] == "configured_cli"
    assert receipt["credentials_present"] is True


def test_independent_software_verifier_accepts_only_the_predeclared_source_rule_and_transfer_predicate(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "suite.json", _glm_suite()))
    verifier = GateBSoftwareVerifier(suite)
    source = verifier.verify(
        {"episode_id": "source", "task_case_id": "source"},
        ActionArtifact(
            episode_id="source",
            episode_event_hash="sha256:" + "a" * 64,
            content={"answer": "Reject bool before accepting int values."},
            tool_chain=("model",),
        ),
        suite.loop_plan["oracle"],
    )
    transfer = verifier.verify(
        {"episode_id": "transfer", "task_case_id": "transfer"},
        ActionArtifact(
            episode_id="transfer",
            episode_event_hash="sha256:" + "b" * 64,
            content={
                "answer": "not isinstance(value, bool) and isinstance(value, int) and 1 <= value <= 65535"
            },
            tool_chain=("model",),
        ),
        suite.loop_plan["oracle"],
    )

    assert source.outcome == "success"
    assert transfer.outcome == "success"

    wrong = verifier.verify(
        {"episode_id": "wrong", "task_case_id": "transfer"},
        ActionArtifact(
            episode_id="wrong",
            episode_event_hash="sha256:" + "c" * 64,
            content={"answer": "isinstance(value, int)"},
            tool_chain=("model",),
        ),
        suite.loop_plan["oracle"],
    )
    assert wrong.outcome == "failure"
    assert wrong.failure_class == "oracle.mismatch"


def test_independent_software_verifier_rejects_a_suite_with_a_substituted_oracle(
    tmp_path: Path,
) -> None:
    altered = _glm_suite()
    altered["loop_plan"]["oracle"]["cases"]["transfer"]["expected"] = "substituted"  # type: ignore[index]
    altered.pop("suite_hash")
    altered["suite_hash"] = _hash(altered)
    suite = load_value_suite(_write_suite(tmp_path / "altered.json", altered))

    with pytest.raises(LiveCodingError, match="gate_b_oracle_unsupported"):
        GateBSoftwareVerifier(suite)


def test_independent_software_verifier_keeps_the_reserve_status_range_separate(
    tmp_path: Path,
) -> None:
    suite = load_value_suite(_write_suite(tmp_path / "reserve.json", _reserve_glm_suite()))
    verifier = GateBSoftwareVerifier(suite)
    artifact = ActionArtifact(
        episode_id="reserve",
        episode_event_hash="sha256:" + "d" * 64,
        content={
            "answer": "not isinstance(value, bool) and isinstance(value, int) and 100 <= value <= 599"
        },
        tool_chain=("model",),
    )

    verdict = verifier.verify(
        {"episode_id": "reserve", "task_case_id": "transfer"},
        artifact,
        suite.loop_plan["oracle"],
    )

    assert verdict.outcome == "success"
