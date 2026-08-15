"""Bounded, fail-closed live coding action boundary for Compass Gate B.

This module intentionally owns neither verification nor promotion.  It turns one
sealed three-arm value suite into exactly three provider requests.  The first
request may emit reusable advice, but the adapter only permits that advice on
the third request when it matches the advice hash frozen before any call.
"""

from __future__ import annotations

import ast
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from urllib.parse import urlparse

from gep.loop_run import ActionArtifact, ActionExecutionFailure
from gep.verdict_packet import VerdictPacket


VALUE_SUITE_SCHEMA = "compass.loop.value_suite.v1"
_HASH_PREFIX = "sha256:"
_SUITE_KEYS = frozenset(
    {
        "schema_version",
        "suite_id",
        "loop_plan",
        "provider",
        "execution",
        "reuse_contract",
        "suite_hash",
    }
)
_OPENAI_PROVIDER_KEYS = frozenset(
    {
        "adapter_kind",
        "provider_id",
        "model_id",
        "adapter_version",
        "base_url",
        "credential_env",
    }
)
_CLAUDE_PROVIDER_KEYS = frozenset(
    {
        "adapter_kind",
        "provider_id",
        "model_id",
        "adapter_version",
        "command",
        "command_model",
    }
)
_EXECUTION_KEYS = frozenset(
    {
        "system_prompt",
        "timeout_seconds",
        "max_completion_tokens",
        "max_output_bytes",
        "max_calls",
        "max_total_cost_usd",
        "pricing",
        "one_shot_no_retry",
        "network_allowed",
        "tool_calls_allowed",
    }
)
_PRICING_KEYS = frozenset({"input_per_1k_usd", "output_per_1k_usd"})
_REUSE_CONTRACT_KEYS = frozenset({"field", "min_chars", "max_chars"})
_EXPECTED_ARM_ORDER = ("source", "control", "treatment")
_EXPECTED_CASES = {"source": "source", "control": "transfer", "treatment": "transfer"}
_GATE_B_ORACLE = {
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


class LiveCodingError(ValueError):
    """A sealed Gate B request cannot safely execute."""


class ProviderCallError(RuntimeError):
    """A redacted provider problem with a stable reason code."""


@dataclass(frozen=True)
class ProviderResult:
    """Metered output returned by one provider call; no credential is retained."""

    output_text: str
    reported_model_id: str
    input_tokens: int
    output_tokens: int
    estimated_cost_usd: float | None
    latency_ms: int

    def __post_init__(self) -> None:
        if not isinstance(self.output_text, str) or not self.output_text.strip():
            raise ProviderCallError("provider_output_missing")
        if not isinstance(self.reported_model_id, str) or not self.reported_model_id.strip():
            raise ProviderCallError("provider_identity_missing")
        for name in ("input_tokens", "output_tokens", "latency_ms"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ProviderCallError("provider_usage_invalid")
        if self.estimated_cost_usd is not None:
            _nonnegative_finite(self.estimated_cost_usd, "provider_cost_invalid")


class ProviderClient(Protocol):
    """The only capability needed by ``LiveCodingAdapter``."""

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult: ...


@dataclass(frozen=True)
class ValueSuite:
    """Parsed immutable input to the bounded live action."""

    raw: dict[str, object]
    suite_id: str
    suite_hash: str
    loop_plan: dict[str, object]
    provider: dict[str, object]
    execution: dict[str, object]
    reuse_contract: dict[str, object]


class OpenAICompatibleProvider:
    """One fixed HTTPS chat-completions client, used only after preflight."""

    def __init__(
        self,
        suite: ValueSuite,
        *,
        environment: Mapping[str, str] | None = None,
        transport: Callable[[str, Mapping[str, str], bytes, int, int], bytes] | None = None,
    ) -> None:
        if suite.provider.get("adapter_kind") != "openai_compatible":
            raise LiveCodingError("provider_adapter_kind_invalid")
        self._suite = suite
        self._environment = os.environ if environment is None else environment
        self._transport = _urllib_post if transport is None else transport
        base_url = str(suite.provider["base_url"])
        parsed = urlparse(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.username
            or parsed.password
            or parsed.query
            or parsed.fragment
        ):
            raise LiveCodingError("provider_base_url_invalid")
        self._base_url = base_url.rstrip("/")

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
        if timeout_seconds != self._suite.execution["timeout_seconds"]:
            raise ProviderCallError("provider_timeout_mismatch")
        credential = self._environment.get(str(self._suite.provider["credential_env"]))
        if not credential:
            raise ProviderCallError("provider_credential_missing")
        body = json.dumps(
            {
                "model": self._suite.provider["model_id"],
                "messages": [
                    {"role": "system", "content": self._suite.execution["system_prompt"]},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0,
                "max_completion_tokens": self._suite.execution["max_completion_tokens"],
                "stream": False,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        started = time.perf_counter()
        try:
            raw = self._transport(
                self._base_url + "/chat/completions",
                {"Authorization": f"Bearer {credential}", "Content-Type": "application/json"},
                body,
                timeout_seconds,
                int(self._suite.execution["max_output_bytes"]),
            )
        except ProviderCallError:
            raise
        except TimeoutError as exc:
            raise ProviderCallError("provider_timeout") from exc
        except Exception as exc:
            raise ProviderCallError("provider_transport_failed") from exc
        latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        return _parse_openai_response(raw, latency_ms)


class ClaudeCliProvider:
    """Run one configured GLM-backed Claude CLI turn without tools or persistence."""

    def __init__(
        self,
        suite: ValueSuite,
        *,
        environment: Mapping[str, str] | None = None,
        runner: Callable[..., subprocess.CompletedProcess[bytes]] | None = None,
    ) -> None:
        if suite.provider.get("adapter_kind") != "claude_cli":
            raise LiveCodingError("provider_adapter_kind_invalid")
        self._suite = suite
        self._environment = os.environ if environment is None else environment
        self._runner = subprocess.run if runner is None else runner

    def invoke(self, prompt: str, *, timeout_seconds: int) -> ProviderResult:
        if timeout_seconds != self._suite.execution["timeout_seconds"]:
            raise ProviderCallError("provider_timeout_mismatch")
        command = str(self._suite.provider["command"])
        if shutil.which(command) is None and not Path(command).is_file():
            raise ProviderCallError("provider_executable_missing")
        argv = _claude_command(self._suite)
        try:
            with tempfile.TemporaryDirectory(prefix="compass-gate-b-") as workspace:
                started = time.perf_counter()
                completed = self._runner(
                    argv,
                    cwd=workspace,
                    input=prompt.encode("utf-8"),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=False,
                    env=_claude_environment(self._environment),
                    timeout=timeout_seconds,
                    check=False,
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
                latency_ms = max(0, int(round((time.perf_counter() - started) * 1000)))
        except subprocess.TimeoutExpired as exc:
            raise ProviderCallError("provider_timeout") from exc
        except FileNotFoundError as exc:
            raise ProviderCallError("provider_executable_missing") from exc
        except OSError as exc:
            raise ProviderCallError("provider_launch_failed") from exc
        stdout = completed.stdout or b""
        stderr = completed.stderr or b""
        if len(stdout) + len(stderr) > self._suite.execution["max_output_bytes"]:
            raise ProviderCallError("provider_output_too_large")
        if completed.returncode != 0:
            raise ProviderCallError("provider_nonzero_exit")
        return _parse_claude_response(stdout, latency_ms)


def load_value_suite(path: str | Path) -> ValueSuite:
    """Load exact canonical JSON and reject any widened or tampered suite."""

    try:
        raw_bytes = Path(path).read_bytes()
        decoded = json.loads(raw_bytes)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LiveCodingError("value_suite_unreadable") from exc
    return _parse_value_suite(decoded)


def preflight_value_suite(
    suite: ValueSuite,
    *,
    environment: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Bind all requests without contacting a provider or creating evidence files."""

    if not isinstance(suite, ValueSuite):
        raise TypeError("suite must be a ValueSuite")
    env = os.environ if environment is None else environment
    adapter_kind = suite.provider["adapter_kind"]
    if adapter_kind == "openai_compatible":
        if not env.get(str(suite.provider["credential_env"])):
            raise LiveCodingError("provider_credential_missing")
        access_mode = "environment_credential"
    else:
        command = str(suite.provider["command"])
        if shutil.which(command) is None and not Path(command).is_file():
            raise LiveCodingError("provider_executable_missing")
        access_mode = "configured_cli"
    request_hashes = _exact_request_hashes(suite)
    treatment_template_hash = _treatment_template_hash(suite)
    receipt: dict[str, object] = {
        "schema_version": "compass.loop.value_preflight.v1",
        "suite_id": suite.suite_id,
        "suite_hash": suite.suite_hash,
        "loop_plan_hash": _hash_json(suite.loop_plan),
        "provider_identity": {
            "provider_id": suite.provider["provider_id"],
            "model_id": suite.provider["model_id"],
            "adapter_version": suite.provider["adapter_version"],
            "adapter_kind": suite.provider["adapter_kind"],
        },
        "request_hashes": request_hashes,
        "request_template_hashes": {"treatment": treatment_template_hash},
        "treatment_binding": {
            "source_arm": "source",
            "source_artifact_field": suite.reuse_contract["field"],
            "template_hash": treatment_template_hash,
        },
        "expected_calls": suite.execution["max_calls"],
        "credentials_present": True,
        "provider_access_mode": access_mode,
        "zero_provider_calls": True,
        "zero_writes": True,
        "candidate_only": True,
        "automatic_promotion_authorized": False,
        "capsule_distilled": False,
        "poi_updated": False,
        "recall_updated": False,
        "policy_updated": False,
        "source_write": False,
        "ready": True,
    }
    receipt["receipt_hash"] = _hash_json(receipt)
    return receipt


class LiveCodingAdapter:
    """A three-call actor with no retry, promotion, journal, or verifier authority."""

    def __init__(self, suite: ValueSuite, provider: ProviderClient) -> None:
        if not isinstance(suite, ValueSuite):
            raise TypeError("suite must be a ValueSuite")
        if not callable(getattr(provider, "invoke", None)):
            raise TypeError("provider must implement invoke")
        self._suite = suite
        self._provider = provider
        self._request_hashes = _exact_request_hashes(suite)
        self._treatment_template_hash = _treatment_template_hash(suite)
        self._expected_episodes = _expected_episodes(suite.loop_plan)
        self._next_ordinal = 0
        self._spent_cost_usd = 0.0
        self._source_advice_hash: str | None = None
        self._source_response_hash: str | None = None

    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact:
        del work_dir
        label, expected_episode_id = self._next_expected_arm()
        episode_id = task.get("episode_id")
        if episode_id != expected_episode_id:
            if episode_id in self._expected_episodes.values():
                raise LiveCodingError("duplicate_attempt")
            raise LiveCodingError("attempt_episode_mismatch")
        expected_case_id = _EXPECTED_CASES[label]
        if task.get("task_case_id") != expected_case_id:
            raise LiveCodingError("attempt_case_mismatch")
        if label != "treatment" and advice is not None:
            raise LiveCodingError("attempt_advice_mismatch")
        if label == "treatment":
            self._validate_treatment_advice(advice)
        prompt = _prompt_for(label, self._suite, advice)
        request_hash = _hash_json(_request_payload(self._suite, prompt))
        if label != "treatment" and request_hash != self._request_hashes[label]:
            raise LiveCodingError("request_hash_mismatch")
        try:
            result = self._provider.invoke(
                prompt,
                timeout_seconds=int(self._suite.execution["timeout_seconds"]),
            )
            if result.reported_model_id != self._suite.provider["model_id"]:
                raise ProviderCallError("provider_identity_mismatch")
            if result.output_tokens > self._suite.execution["max_completion_tokens"]:
                raise ProviderCallError("provider_token_budget_exceeded")
            cost = _computed_cost(result, self._suite.execution["pricing"])
            if self._spent_cost_usd + cost > self._suite.execution["max_total_cost_usd"]:
                raise ProviderCallError("provider_cost_budget_exceeded")
            content = _structured_content(label, result.output_text)
            response_hash = _hash_json(result.output_text)
            if label == "source":
                self._capture_source_advice(content, response_hash)
        except (LiveCodingError, ProviderCallError) as exc:
            raise ActionExecutionFailure(str(exc)) from exc
        self._spent_cost_usd += cost
        self._next_ordinal += 1
        bindings: dict[str, object] = {}
        if label == "treatment":
            bindings = {
                "request_template_hash": self._treatment_template_hash,
                "source_advice_hash": self._source_advice_hash,
                "source_response_hash": self._source_response_hash,
            }
        return ActionArtifact(
            episode_id=expected_episode_id,
            content={
                **content,
                "request_hash": request_hash,
                "response_hash": response_hash,
                **bindings,
                "provider_id": self._suite.provider["provider_id"],
                "reported_model_id": result.reported_model_id,
                "input_tokens": result.input_tokens,
                "output_tokens": result.output_tokens,
                "computed_cost_usd": cost,
                "latency_ms": result.latency_ms,
            },
            tool_chain=("openai_chat_completion", "structured_output"),
        )

    def _next_expected_arm(self) -> tuple[str, str]:
        if self._next_ordinal >= len(_EXPECTED_ARM_ORDER):
            raise LiveCodingError("duplicate_attempt")
        label = _EXPECTED_ARM_ORDER[self._next_ordinal]
        return label, self._expected_episodes[label]

    def _capture_source_advice(self, content: Mapping[str, object], response_hash: str) -> None:
        field = str(self._suite.reuse_contract["field"])
        advice = content.get(field)
        if not isinstance(advice, str):
            raise LiveCodingError("source_reuse_advice_missing")
        minimum = int(self._suite.reuse_contract["min_chars"])
        maximum = int(self._suite.reuse_contract["max_chars"])
        if not minimum <= len(advice) <= maximum:
            raise LiveCodingError("source_reuse_advice_out_of_bounds")
        self._source_advice_hash = _hash_json(advice)
        self._source_response_hash = response_hash

    def _validate_treatment_advice(self, advice: str | None) -> None:
        if self._source_advice_hash is None or self._source_response_hash is None:
            raise LiveCodingError("treatment_source_not_bound")
        if not isinstance(advice, str) or _hash_json(advice) != self._source_advice_hash:
            raise LiveCodingError("treatment_advice_binding_mismatch")


class GateBSoftwareVerifier:
    """A separate deterministic oracle for the fixed source/transfer coding suite."""

    def __init__(self, suite: ValueSuite) -> None:
        if not isinstance(suite, ValueSuite):
            raise TypeError("suite must be a ValueSuite")
        self._suite = suite
        self._oracle = suite.loop_plan["oracle"]
        if self._oracle != _GATE_B_ORACLE:
            raise LiveCodingError("gate_b_oracle_unsupported")
        self._policy_hash = suite.loop_plan["verifier_policy_hash"]
        self._environment_hash = suite.loop_plan["environment_fingerprint_hash"]

    def verify(
        self,
        task: dict[str, object],
        artifact: ActionArtifact,
        oracle: dict[str, object],
    ) -> VerdictPacket:
        if _hash_json(oracle) != _hash_json(self._oracle):
            raise LiveCodingError("oracle_binding_mismatch")
        case_id = task.get("task_case_id")
        if case_id not in {"source", "transfer"} or task.get("episode_id") != artifact.episode_id:
            raise LiveCodingError("verifier_task_binding_mismatch")
        failure_reason = artifact.content.get("failure_reason")
        if isinstance(failure_reason, str):
            return self._packet(artifact, "failure", failure_reason)
        answer = artifact.content.get("answer")
        success = (
            _valid_source_rule(answer) if case_id == "source" else _valid_transfer_predicate(answer)
        )
        return self._packet(
            artifact, "success" if success else "failure", None if success else "oracle.mismatch"
        )

    def _packet(
        self,
        artifact: ActionArtifact,
        outcome: str,
        failure_class: str | None,
    ) -> VerdictPacket:
        return VerdictPacket(
            episode_id=artifact.episode_id,
            episode_event_hash=artifact.episode_event_hash or "",
            outcome=outcome,
            verifier_kind="software_test",
            verifier_version="compass-gate-b-software-oracle-v1",
            verifier_policy_hash=str(self._policy_hash),
            evidence_hash=artifact.evidence_hash,
            environment_fingerprint_hash=str(self._environment_hash),
            failure_class=failure_class,
        )


def _parse_value_suite(value: object) -> ValueSuite:
    if not isinstance(value, Mapping) or frozenset(value) != _SUITE_KEYS:
        raise LiveCodingError("value_suite_fields_invalid")
    raw = _json_mapping(value, "value suite")
    if raw["schema_version"] != VALUE_SUITE_SCHEMA:
        raise LiveCodingError("value_suite_schema_unsupported")
    supplied_hash = _require_hash(raw["suite_hash"], "suite_hash")
    expected_hash = _hash_json({key: item for key, item in raw.items() if key != "suite_hash"})
    if supplied_hash != expected_hash:
        raise LiveCodingError("suite_hash_mismatch")
    suite_id = _require_id(raw["suite_id"], "suite_id")
    loop_plan = _json_mapping(raw["loop_plan"], "loop_plan")
    _validate_loop_plan(loop_plan)
    provider = _json_mapping(raw["provider"], "provider")
    _validate_provider(provider)
    execution = _json_mapping(raw["execution"], "execution")
    _validate_execution(execution)
    reuse_contract = _json_mapping(raw["reuse_contract"], "reuse_contract")
    _validate_reuse_contract(reuse_contract)
    return ValueSuite(
        raw=raw,
        suite_id=suite_id,
        suite_hash=supplied_hash,
        loop_plan=loop_plan,
        provider=provider,
        execution=execution,
        reuse_contract=reuse_contract,
    )


def _validate_loop_plan(plan: Mapping[str, object]) -> None:
    if plan.get("schema_version") != "compass.loop.plan.v2":
        raise LiveCodingError("value_suite_requires_gate_b_plan")
    arms = plan.get("arms")
    if not isinstance(arms, list) or [
        arm.get("label") for arm in arms if isinstance(arm, Mapping)
    ] != list(_EXPECTED_ARM_ORDER):
        raise LiveCodingError("value_suite_arm_order_invalid")
    if len(arms) != len(_EXPECTED_ARM_ORDER):
        raise LiveCodingError("value_suite_arm_order_invalid")
    _expected_episodes(plan)


def _validate_provider(provider: Mapping[str, object]) -> None:
    adapter_kind = provider.get("adapter_kind")
    if adapter_kind not in {"openai_compatible", "claude_cli"}:
        raise LiveCodingError("provider_adapter_kind_invalid")
    expected_keys = (
        _OPENAI_PROVIDER_KEYS if adapter_kind == "openai_compatible" else _CLAUDE_PROVIDER_KEYS
    )
    if frozenset(provider) != expected_keys:
        raise LiveCodingError("provider_fields_invalid")
    for key in ("provider_id", "model_id", "adapter_version"):
        _require_id(provider[key], key)
    if adapter_kind == "claude_cli":
        _require_id(provider["command"], "provider_command")
        _require_id(provider["command_model"], "provider_command_model")
        return
    credential_env = provider["credential_env"]
    if not isinstance(credential_env, str) or not credential_env.isidentifier():
        raise LiveCodingError("provider_credential_env_invalid")
    base_url = provider["base_url"]
    if not isinstance(base_url, str):
        raise LiveCodingError("provider_base_url_invalid")
    parsed = urlparse(base_url)
    if (
        parsed.scheme != "https"
        or not parsed.netloc
        or parsed.username
        or parsed.password
        or parsed.query
        or parsed.fragment
    ):
        raise LiveCodingError("provider_base_url_invalid")


def _validate_execution(execution: Mapping[str, object]) -> None:
    if frozenset(execution) != _EXECUTION_KEYS:
        raise LiveCodingError("execution_fields_invalid")
    if not isinstance(execution["system_prompt"], str) or not execution["system_prompt"].strip():
        raise LiveCodingError("system_prompt_invalid")
    for key in ("timeout_seconds", "max_completion_tokens", "max_output_bytes"):
        value = execution[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise LiveCodingError("execution_budget_invalid")
    if execution["max_calls"] != 3:
        raise LiveCodingError("execution_max_calls_invalid")
    _nonnegative_finite(execution["max_total_cost_usd"], "execution_cost_budget_invalid")
    if execution["max_total_cost_usd"] <= 0:
        raise LiveCodingError("execution_cost_budget_invalid")
    pricing = execution["pricing"]
    if not isinstance(pricing, Mapping) or frozenset(pricing) != _PRICING_KEYS:
        raise LiveCodingError("execution_pricing_invalid")
    for value in pricing.values():
        _nonnegative_finite(value, "execution_pricing_invalid")
    if execution["one_shot_no_retry"] is not True:
        raise LiveCodingError("execution_retry_policy_invalid")
    if execution["network_allowed"] is not True or execution["tool_calls_allowed"] is not False:
        raise LiveCodingError("execution_capability_policy_invalid")


def _validate_reuse_contract(contract: Mapping[str, object]) -> None:
    if frozenset(contract) != _REUSE_CONTRACT_KEYS:
        raise LiveCodingError("reuse_contract_fields_invalid")
    if contract["field"] != "reuse_advice":
        raise LiveCodingError("reuse_contract_field_invalid")
    minimum = contract["min_chars"]
    maximum = contract["max_chars"]
    if (
        isinstance(minimum, bool)
        or isinstance(maximum, bool)
        or not isinstance(minimum, int)
        or not isinstance(maximum, int)
        or minimum < 1
        or maximum < minimum
        or maximum > 4096
    ):
        raise LiveCodingError("reuse_contract_bounds_invalid")


def _expected_episodes(plan: Mapping[str, object]) -> dict[str, str]:
    arms = plan["arms"]
    if not isinstance(arms, list):
        raise LiveCodingError("value_suite_arm_order_invalid")
    episodes: dict[str, str] = {}
    for label, arm in zip(_EXPECTED_ARM_ORDER, arms):
        if not isinstance(arm, Mapping):
            raise LiveCodingError("value_suite_arm_order_invalid")
        episode_id = arm.get("episode_id")
        episodes[label] = _require_id(episode_id, "episode_id")
    if len(set(episodes.values())) != 3:
        raise LiveCodingError("value_suite_episode_ids_invalid")
    return episodes


def _exact_request_hashes(suite: ValueSuite) -> dict[str, str]:
    return {
        label: _hash_json(_request_payload(suite, _prompt_for(label, suite, None)))
        for label in ("source", "control")
    }


def _treatment_template_hash(suite: ValueSuite) -> str:
    return _hash_json(
        _request_payload(suite, _prompt_for("treatment", suite, "{{source_reuse_advice}}"))
    )


def _prompt_for(label: str, suite: ValueSuite, advice: str | None) -> str:
    plan = suite.loop_plan
    task = plan["task"]
    if not isinstance(task, Mapping) or not isinstance(task.get("cases"), Mapping):
        raise LiveCodingError("value_suite_task_invalid")
    case_id = _EXPECTED_CASES[label]
    case = task["cases"].get(case_id)
    if not isinstance(case, Mapping) or not isinstance(case.get("prompt"), str):
        raise LiveCodingError("value_suite_task_invalid")
    sections = ["Task:\n" + case["prompt"]]
    if advice is not None:
        sections.append("Verified reusable experience:\n" + advice)
    if label == "source":
        sections.append('Return JSON exactly with "answer" and "reuse_advice" strings.')
    else:
        sections.append('Return JSON exactly with one "answer" string.')
    return "\n\n".join(sections)


def _request_payload(suite: ValueSuite, prompt: str) -> dict[str, object]:
    return {
        "adapter_kind": suite.provider["adapter_kind"],
        "provider_id": suite.provider["provider_id"],
        "model_id": suite.provider["model_id"],
        "adapter_version": suite.provider["adapter_version"],
        "system_prompt": suite.execution["system_prompt"],
        "prompt": prompt,
        "timeout_seconds": suite.execution["timeout_seconds"],
        "max_completion_tokens": suite.execution["max_completion_tokens"],
        "tool_calls_allowed": suite.execution["tool_calls_allowed"],
    }


def _structured_content(label: str, output_text: str) -> dict[str, object]:
    try:
        parsed = json.loads(output_text)
    except json.JSONDecodeError as exc:
        raise ProviderCallError("provider_output_invalid") from exc
    if not isinstance(parsed, Mapping):
        raise ProviderCallError("provider_output_invalid")
    expected_keys = {"answer", "reuse_advice"} if label == "source" else {"answer"}
    if frozenset(parsed) != expected_keys or any(
        not isinstance(value, str) or not value.strip() for value in parsed.values()
    ):
        raise ProviderCallError("provider_output_invalid")
    return dict(parsed)


def _valid_source_rule(answer: object) -> bool:
    if not isinstance(answer, str):
        return False
    normalized = answer.lower()
    bool_position = normalized.find("bool")
    int_position = normalized.find("int")
    return (
        bool_position >= 0
        and int_position > bool_position
        and any(token in normalized for token in ("reject", "exclude", "check"))
        and "before" in normalized
    )


def _valid_transfer_predicate(answer: object) -> bool:
    if not isinstance(answer, str) or not answer.strip():
        return False
    try:
        tree = ast.parse(answer, mode="eval")
    except SyntaxError:
        return False
    if not _safe_predicate_ast(tree):
        return False
    globals_scope = {"__builtins__": {}, "bool": bool, "int": int, "isinstance": isinstance}
    for value, expected in (
        (True, False),
        (False, False),
        (1, True),
        (65535, True),
        (0, False),
        (-1, False),
        (65536, False),
        ("1", False),
        (1.5, False),
    ):
        try:
            actual = eval(
                compile(tree, "<gate-b-predicate>", "eval"), globals_scope, {"value": value}
            )
        except Exception:
            return False
        if actual is not expected:
            return False
    return True


def _safe_predicate_ast(tree: ast.AST) -> bool:
    allowed_nodes = (
        ast.Expression,
        ast.BoolOp,
        ast.And,
        ast.Call,
        ast.Compare,
        ast.Constant,
        ast.IsNot,
        ast.Load,
        ast.LtE,
        ast.Name,
        ast.Not,
        ast.UnaryOp,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed_nodes):
            return False
        if isinstance(node, ast.Name) and node.id not in {"value", "bool", "int", "isinstance"}:
            return False
        if isinstance(node, ast.Call) and (
            not isinstance(node.func, ast.Name)
            or node.func.id != "isinstance"
            or len(node.args) != 2
            or node.keywords
        ):
            return False
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, bool)):
            return False
    return True


def _computed_cost(result: ProviderResult, pricing: object) -> float:
    if not isinstance(pricing, Mapping):
        raise LiveCodingError("execution_pricing_invalid")
    cost = (
        result.input_tokens * float(pricing["input_per_1k_usd"])
        + result.output_tokens * float(pricing["output_per_1k_usd"])
    ) / 1000
    _nonnegative_finite(cost, "provider_cost_invalid")
    return cost


def _parse_openai_response(raw: bytes, latency_ms: int) -> ProviderResult:
    try:
        if len(raw) > 1024 * 1024:
            raise ValueError("response too large")
        value = json.loads(raw)
        choice = value["choices"][0]
        output_text = choice["message"]["content"]
        usage = value["usage"]
        return ProviderResult(
            output_text=output_text,
            reported_model_id=value["model"],
            input_tokens=usage["prompt_tokens"],
            output_tokens=usage["completion_tokens"],
            estimated_cost_usd=None,
            latency_ms=latency_ms,
        )
    except (KeyError, IndexError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc


def _claude_command(suite: ValueSuite) -> list[str]:
    return [
        str(suite.provider["command"]),
        "-p",
        "--output-format",
        "json",
        "--model",
        str(suite.provider["command_model"]),
        "--safe-mode",
        "--tools",
        "",
        "--strict-mcp-config",
        "--mcp-config",
        '{"mcpServers":{}}',
        "--disable-slash-commands",
        "--no-session-persistence",
        "--permission-mode",
        "plan",
        "--max-budget-usd",
        str(suite.execution["max_total_cost_usd"]),
        "--effort",
        "low",
        "--system-prompt",
        str(suite.execution["system_prompt"]),
    ]


def _claude_environment(environment: Mapping[str, str]) -> dict[str, str]:
    allowed = {
        "ALL_PROXY",
        "APPDATA",
        "COMSPEC",
        "HOME",
        "HOMEDRIVE",
        "HOMEPATH",
        "HTTP_PROXY",
        "HTTPS_PROXY",
        "LOCALAPPDATA",
        "NODE_EXTRA_CA_CERTS",
        "NO_PROXY",
        "OS",
        "PATH",
        "PATHEXT",
        "PROGRAMDATA",
        "PROGRAMFILES",
        "PROGRAMFILES(X86)",
        "PROGRAMW6432",
        "REQUESTS_CA_BUNDLE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "SYSTEMDRIVE",
        "SYSTEMROOT",
        "TEMP",
        "TMP",
        "USERPROFILE",
        "WINDIR",
        "ANTHROPIC_API_KEY",
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_OAUTH_TOKEN",
        "CLAUDE_CONFIG_DIR",
    }
    return {key: value for key, value in environment.items() if key.upper() in allowed}


def _parse_claude_response(raw: bytes, latency_ms: int) -> ProviderResult:
    try:
        value = json.loads(raw)
        if not isinstance(value, Mapping) or value.get("is_error") is True:
            raise ValueError("provider error response")
        usage = value["usage"]
        model_usage = value["modelUsage"]
        if not isinstance(usage, Mapping) or not isinstance(model_usage, Mapping):
            raise ValueError("missing usage")
        if len(model_usage) != 1:
            raise ValueError("ambiguous model usage")
        reported_model_id = next(iter(model_usage))
        return ProviderResult(
            output_text=value["result"],
            reported_model_id=reported_model_id,
            input_tokens=_usage_token(usage, "input_tokens"),
            output_tokens=_usage_token(usage, "output_tokens"),
            estimated_cost_usd=value.get("total_cost_usd"),
            latency_ms=latency_ms,
        )
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
        raise ProviderCallError("provider_output_invalid") from exc


def _usage_token(usage: Mapping[str, object], key: str) -> int:
    value = usage.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError("invalid usage token count")
    return value


def _urllib_post(
    url: str,
    headers: Mapping[str, str],
    body: bytes,
    timeout_seconds: int,
    max_output_bytes: int,
) -> bytes:
    request = urllib.request.Request(url, data=body, headers=dict(headers), method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            body = response.read(max_output_bytes + 1)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, TimeoutError):
            raise ProviderCallError("provider_timeout") from exc
        raise ProviderCallError("provider_transport_failed") from exc
    if len(body) > max_output_bytes:
        raise ProviderCallError("provider_output_too_large")
    return body


def _json_mapping(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, Mapping):
        raise LiveCodingError(f"{label}_invalid")
    try:
        decoded = json.loads(_canonical_json_bytes(dict(value)))
    except (TypeError, ValueError, OverflowError) as exc:
        raise LiveCodingError(f"{label}_invalid") from exc
    if not isinstance(decoded, dict):
        raise LiveCodingError(f"{label}_invalid")
    return decoded


def _require_id(value: object, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise LiveCodingError(f"{label}_invalid")
    return value


def _require_hash(value: object, label: str) -> str:
    if not isinstance(value, str) or len(value) != 71 or not value.startswith(_HASH_PREFIX):
        raise LiveCodingError(f"{label}_invalid")
    try:
        int(value[len(_HASH_PREFIX) :], 16)
    except ValueError as exc:
        raise LiveCodingError(f"{label}_invalid") from exc
    return value


def _nonnegative_finite(value: object, reason_code: str) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise LiveCodingError(reason_code)


def _canonical_json_bytes(value: object) -> bytes:
    try:
        return json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, OverflowError) as exc:
        raise LiveCodingError("canonical_json_invalid") from exc


def _hash_json(value: object) -> str:
    return _HASH_PREFIX + hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


__all__ = [
    "ClaudeCliProvider",
    "GateBSoftwareVerifier",
    "LiveCodingAdapter",
    "LiveCodingError",
    "OpenAICompatibleProvider",
    "ProviderCallError",
    "ProviderResult",
    "ValueSuite",
    "load_value_suite",
    "preflight_value_suite",
]
