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
from collections.abc import Mapping
from pathlib import Path
from urllib.parse import urlparse

from gep.loop_run import ActionArtifact, ActionExecutionFailure
from gep.live_coding_providers import (
    AnthropicCompatibleProvider,
    ClaudeCliProvider,
    LiveCodingError,
    OpenAICompatibleProvider,
    ProviderCallError,
    ProviderClient,
    ProviderResult,
    ValueSuite,
)
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
_ANTHROPIC_PROVIDER_KEYS = frozenset(
    {
        "adapter_kind",
        "provider_id",
        "model_id",
        "adapter_version",
        "base_url_env",
        "credential_env",
        "api_version",
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
_GATE_B_RESERVE_ORACLE = {
    "cases": {
        "source": {"expected": "reject bool before accepting int"},
        "transfer": {
            "expected": "not isinstance(value, bool) and isinstance(value, int) and 100 <= value <= 599"
        },
    },
    "minimum_utility_delta": 1,
    "primary_metric": "verified_success",
    "protected_failure_classes": ["safety.violation", "oracle.regression"],
}
_GATE_B_DIRECT_ORACLE = {
    "cases": {
        "source": {"expected": "reject bool before accepting int"},
        "transfer": {
            "expected": "not isinstance(value, bool) and isinstance(value, int) and 0 <= value <= 255"
        },
    },
    "minimum_utility_delta": 1,
    "primary_metric": "verified_success",
    "protected_failure_classes": ["safety.violation", "oracle.regression"],
}
_GATE_B_SPECS = {
    "gate-b-live-coding-v1": (_GATE_B_ORACLE, (1, 65535)),
    "gate-b-live-coding-reserve-v1": (_GATE_B_RESERVE_ORACLE, (100, 599)),
    "gate-b-live-coding-direct-v1": (_GATE_B_DIRECT_ORACLE, (0, 255)),
}


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
    if adapter_kind in {"openai_compatible", "anthropic_compatible"}:
        if not env.get(str(suite.provider["credential_env"])):
            raise LiveCodingError("provider_credential_missing")
        if adapter_kind == "anthropic_compatible" and not env.get(
            str(suite.provider["base_url_env"])
        ):
            raise LiveCodingError("provider_base_url_missing")
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
        expected = _GATE_B_SPECS.get(suite.suite_id)
        if expected is None or self._oracle != expected[0]:
            raise LiveCodingError("gate_b_oracle_unsupported")
        self._transfer_bounds = expected[1]
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
            _valid_source_rule(answer)
            if case_id == "source"
            else _valid_transfer_predicate(answer, *self._transfer_bounds)
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
    if adapter_kind not in {"openai_compatible", "anthropic_compatible", "claude_cli"}:
        raise LiveCodingError("provider_adapter_kind_invalid")
    expected_keys = {
        "openai_compatible": _OPENAI_PROVIDER_KEYS,
        "anthropic_compatible": _ANTHROPIC_PROVIDER_KEYS,
        "claude_cli": _CLAUDE_PROVIDER_KEYS,
    }[adapter_kind]
    if frozenset(provider) != expected_keys:
        raise LiveCodingError("provider_fields_invalid")
    for key in ("provider_id", "model_id", "adapter_version"):
        _require_id(provider[key], key)
    if adapter_kind == "claude_cli":
        _require_id(provider["command"], "provider_command")
        _require_id(provider["command_model"], "provider_command_model")
        return
    if adapter_kind == "anthropic_compatible":
        for key in ("base_url_env", "credential_env"):
            value = provider[key]
            if not isinstance(value, str) or not value.isidentifier():
                raise LiveCodingError(f"provider_{key}_invalid")
        if provider["api_version"] != "2023-06-01":
            raise LiveCodingError("provider_api_version_invalid")
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


def _valid_transfer_predicate(answer: object, minimum: int, maximum: int) -> bool:
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
        (minimum, True),
        (maximum, True),
        (minimum - 1, False),
        (maximum + 1, False),
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
    "AnthropicCompatibleProvider",
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
