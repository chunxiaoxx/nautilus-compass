from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import BinaryIO, Literal

import httpx
from g2_a0_deepseek_client import (
    RESPONSE_EXAMPLE_JSON,
    CandidateArtifactV1,
    DeepSeekClientViolation,
    DeepSeekCompletionResultV1,
    DeepSeekTransportClientV1,
)
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1
from g2_a0_synthetic_verifier import (
    SyntheticVerificationResultV1,
    _apply_unified_diff,
    _validate_repaired_source,
    verify_candidate_patch,
)

from platform_protocol.g2_a0_model_gate import (
    DeepSeekModelGatePolicyV1,
    ModelGateContractViolation,
    ModelGateDecisionV1,
    ModelGateRequestBindingV1,
    assert_idempotency_replay_matches,
    canonical_json_bytes,
    sha256_hex,
)

G2_A0_PAID_RUN_AUTHORIZATION = "authorize-g2-a0-one-call-max-cny-5-v1"
_EVIDENCE_VERSION = "g2-a0-model-gate-evidence-v1"
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_HASH_RE = re.compile(r"[0-9a-f]{64}")
_IDEMPOTENCY_RE = re.compile(r"idem_[0-9a-f]{32}")
_BALANCE_RE = re.compile(r"(?:0|[1-9][0-9]{0,12})(?:\.[0-9]{1,6})?")
_TERMINAL_TRACES = {
    "admitted": (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "VALIDATED",
        "VERIFIED",
        "REPLAYED",
        "COMPLETE",
    ),
    "rejected_after_call": (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "REJECTED",
        "REPLAYED",
        "COMPLETE",
    ),
    "rejected_after_validation": (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "VALIDATED",
        "REJECTED",
        "REPLAYED",
        "COMPLETE",
    ),
    "inconclusive": (
        "NEW",
        "BALANCE_READ",
        "CALLING",
        "INCONCLUSIVE",
        "REPLAYED",
        "COMPLETE",
    ),
}
_EVIDENCE_FIELDS = frozenset(
    {
        "balance_delta_micros_cny",
        "balance_delta_status",
        "balance_read_count",
        "cache_hit_input_tokens",
        "cache_miss_input_tokens",
        "calculated_cost_micros_cny",
        "candidate_sha256",
        "child_process_count",
        "contract_version",
        "decision_status",
        "fixture_cleanup_count",
        "fixture_hash",
        "hidden_case_count",
        "implementation_commit",
        "input_tokens",
        "network_call_count",
        "oracle_output_sha256",
        "output_tokens",
        "patched_sha256",
        "policy_hash",
        "provider_call_count",
        "public_case_count",
        "reason_codes",
        "reasoning_sha256",
        "replay_count",
        "replay_provider_call_growth",
        "request_hash",
        "response_content_sha256",
        "response_schema_hash",
        "returned_model",
        "source_sha256",
        "source_write_count",
        "state_trace",
        "system_fingerprint_sha256",
    }
)
_RUNTIME_SOURCE_PATHS = (
    "phase3/backend/platform_protocol/g2_a0_model_gate.py",
    "phase3/backend/tests/platform_protocol/g2_a0_deepseek_client.py",
    "phase3/backend/tests/platform_protocol/g2_a0_synthetic_fixture.py",
    "phase3/backend/tests/platform_protocol/g2_a0_synthetic_verifier.py",
    "phase3/backend/tests/platform_protocol/g2_a0_model_gate_cli.py",
)


class ModelGateRunnerViolation(ValueError):
    """A fixed, redacted failure raised by the test-only gate runner."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def _fail(code: str) -> None:
    raise ModelGateRunnerViolation(code)


def _require_int(value: object, field_name: str, *, minimum: int = 0) -> int:
    if type(value) is not int or value < minimum:
        _fail(f"invalid_{field_name}")
    return value


def _valid_api_key(value: object) -> bool:
    return (
        isinstance(value, str)
        and bool(value)
        and len(value) <= 512
        and value.isascii()
        and not any(character.isspace() for character in value)
    )


def _require_hash_or_none(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
        _fail(f"invalid_{field_name}")
    return value


def _require_hash(value: object, field_name: str) -> str:
    if not isinstance(value, str) or _HASH_RE.fullmatch(value) is None:
        _fail(f"invalid_{field_name}")
    return value


def _candidate_hash(candidate: CandidateArtifactV1) -> str:
    return sha256_hex(
        canonical_json_bytes(
            {
                "artifact_version": candidate.artifact_version,
                "claimed_test_scope": list(candidate.claimed_test_scope),
                "language": candidate.language,
                "summary_code": candidate.summary_code,
                "unified_diff": candidate.unified_diff,
            }
        )
    )


def _expected_verification_hashes(
    candidate: CandidateArtifactV1,
) -> tuple[str, str] | None:
    fixture = SyntheticRepairFixtureV1.default()
    try:
        patched = _apply_unified_diff(fixture.source_bytes, candidate.unified_diff)
        _validate_repaired_source(patched)
    except Exception:  # noqa: BLE001
        return None
    oracle_output = canonical_json_bytes(
        {
            "hidden_passed": True,
            "public_passed": True,
            "status": "passed",
        }
    ) + os.linesep.encode("ascii")
    return hashlib.sha256(patched).hexdigest(), hashlib.sha256(
        oracle_output
    ).hexdigest()


def _fixture_binding_hash(fixture: SyntheticRepairFixtureV1) -> str:
    return sha256_hex(
        canonical_json_bytes(
            {
                "fixture_version": fixture.fixture_version,
                "hidden_case_count": fixture.hidden_case_count,
                "public_case_count": fixture.public_case_count,
                "source_sha256": hashlib.sha256(fixture.source_bytes).hexdigest(),
            }
        )
    )


def _validate_first_request_binding(
    request: ModelGateRequestBindingV1,
    canonical_request: bytes,
) -> None:
    try:
        document = json.loads(canonical_request)
    except (UnicodeDecodeError, ValueError, RecursionError):
        _fail("invalid_canonical_request")
    if not isinstance(document, dict):
        _fail("prompt_binding_mismatch")
    if (
        set(document)
        != {
            "max_tokens",
            "messages",
            "model",
            "reasoning_effort",
            "response_format",
            "stream",
            "thinking",
        }
        or type(document.get("max_tokens")) is not int
        or document.get("max_tokens") != request.policy.max_tokens
        or document.get("model") != request.policy.requested_model
        or document.get("reasoning_effort") != request.policy.reasoning_effort
        or document.get("response_format") != {"type": "json_object"}
        or document.get("stream") is not False
        or document.get("thinking") != {"type": request.policy.thinking_type}
    ):
        _fail("provider_request_mismatch")
    messages = document.get("messages")
    if not isinstance(messages, list) or len(messages) != 1:
        _fail("prompt_binding_mismatch")
    message = messages[0]
    if (
        not isinstance(message, dict)
        or set(message) != {"content", "role"}
        or message.get("role") != "user"
        or not isinstance(message.get("content"), str)
    ):
        _fail("prompt_binding_mismatch")
    prompt = message["content"]
    if hashlib.sha256(prompt.encode("utf-8")).hexdigest() != request.prompt_hash:
        _fail("prompt_binding_mismatch")
    fixture = SyntheticRepairFixtureV1.default()
    if request.fixture_hash != _fixture_binding_hash(fixture):
        _fail("fixture_binding_mismatch")
    if (
        request.response_schema_hash
        != hashlib.sha256(RESPONSE_EXAMPLE_JSON.encode("utf-8")).hexdigest()
    ):
        _fail("response_schema_binding_mismatch")


@dataclass(frozen=True, slots=True)
class ModelGateEvidenceV1:
    contract_version: str
    implementation_commit: str
    request_hash: str
    policy_hash: str
    fixture_hash: str
    response_schema_hash: str
    decision_status: Literal["admitted", "rejected", "inconclusive"]
    reason_codes: tuple[str, ...]
    returned_model: str | None
    response_content_sha256: str | None
    reasoning_sha256: str | None
    system_fingerprint_sha256: str | None
    candidate_sha256: str | None
    source_sha256: str | None
    patched_sha256: str | None
    oracle_output_sha256: str | None
    input_tokens: int
    output_tokens: int
    cache_hit_input_tokens: int
    cache_miss_input_tokens: int
    calculated_cost_micros_cny: int
    balance_delta_micros_cny: int
    balance_delta_status: Literal["known", "ambiguous"]
    provider_call_count: int
    balance_read_count: int
    replay_count: int
    replay_provider_call_growth: int
    public_case_count: int
    hidden_case_count: int
    source_write_count: int
    network_call_count: int
    child_process_count: int
    fixture_cleanup_count: int
    state_trace: tuple[str, ...]

    def _allowed_returned_models(self) -> frozenset[str | None]:
        return frozenset({None, "deepseek-v4-flash-0731"})

    def __post_init__(self) -> None:
        if self.contract_version != _EVIDENCE_VERSION:
            _fail("invalid_contract_version")
        if (
            not isinstance(self.implementation_commit, str)
            or _COMMIT_RE.fullmatch(self.implementation_commit) is None
        ):
            _fail("invalid_implementation_commit")
        for field_name in (
            "request_hash",
            "policy_hash",
            "fixture_hash",
            "response_schema_hash",
        ):
            _require_hash(getattr(self, field_name), field_name)
        try:
            decision = ModelGateDecisionV1(
                status=self.decision_status,
                reason_codes=self.reason_codes,
                request_hash=self.request_hash,
            )
        except ModelGateContractViolation as error:
            raise ModelGateRunnerViolation(error.code) from error
        if decision.status != self.decision_status:
            _fail("invalid_decision")
        if self.returned_model not in self._allowed_returned_models():
            _fail("invalid_returned_model")
        for field_name in (
            "response_content_sha256",
            "reasoning_sha256",
            "system_fingerprint_sha256",
            "candidate_sha256",
            "source_sha256",
            "patched_sha256",
            "oracle_output_sha256",
        ):
            _require_hash_or_none(getattr(self, field_name), field_name)
        for field_name in (
            "input_tokens",
            "output_tokens",
            "cache_hit_input_tokens",
            "cache_miss_input_tokens",
            "calculated_cost_micros_cny",
            "balance_delta_micros_cny",
            "provider_call_count",
            "balance_read_count",
            "replay_count",
            "replay_provider_call_growth",
            "public_case_count",
            "hidden_case_count",
            "source_write_count",
            "network_call_count",
            "child_process_count",
            "fixture_cleanup_count",
        ):
            _require_int(getattr(self, field_name), field_name)
        if self.balance_delta_status not in {"known", "ambiguous"}:
            _fail("invalid_balance_delta_status")
        if (
            self.balance_delta_status == "ambiguous"
            and self.decision_status != "inconclusive"
        ):
            _fail("invalid_balance_delta_status")
        if not isinstance(self.state_trace, tuple) or self.state_trace not in set(
            _TERMINAL_TRACES.values()
        ):
            _fail("invalid_state_trace")
        expected_traces = {
            "admitted": {_TERMINAL_TRACES["admitted"]},
            "inconclusive": {_TERMINAL_TRACES["inconclusive"]},
            "rejected": {
                _TERMINAL_TRACES["rejected_after_call"],
                _TERMINAL_TRACES["rejected_after_validation"],
            },
        }
        if self.state_trace not in expected_traces[self.decision_status]:
            _fail("invalid_state_trace")

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ModelGateEvidenceV1:
        def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
            document: dict[str, object] = {}
            for key, value in pairs:
                if key in document:
                    _fail("duplicate_json_key")
                document[key] = value
            return document

        if not isinstance(data, bytes):
            _fail("invalid_evidence")
        try:
            value = json.loads(
                data.decode("utf-8"),
                object_pairs_hook=reject_duplicates,
            )
        except ModelGateRunnerViolation:
            raise
        except (UnicodeDecodeError, ValueError, RecursionError):
            _fail("invalid_evidence")
        if not isinstance(value, dict) or set(value) != _EVIDENCE_FIELDS:
            _fail("unexpected_evidence_fields")
        reason_codes = value["reason_codes"]
        state_trace = value["state_trace"]
        if not isinstance(reason_codes, list) or not isinstance(state_trace, list):
            _fail("invalid_evidence")
        evidence = cls(
            contract_version=value["contract_version"],
            implementation_commit=value["implementation_commit"],
            request_hash=value["request_hash"],
            policy_hash=value["policy_hash"],
            fixture_hash=value["fixture_hash"],
            response_schema_hash=value["response_schema_hash"],
            decision_status=value["decision_status"],
            reason_codes=tuple(reason_codes),
            returned_model=value["returned_model"],
            response_content_sha256=value["response_content_sha256"],
            reasoning_sha256=value["reasoning_sha256"],
            system_fingerprint_sha256=value["system_fingerprint_sha256"],
            candidate_sha256=value["candidate_sha256"],
            source_sha256=value["source_sha256"],
            patched_sha256=value["patched_sha256"],
            oracle_output_sha256=value["oracle_output_sha256"],
            input_tokens=value["input_tokens"],
            output_tokens=value["output_tokens"],
            cache_hit_input_tokens=value["cache_hit_input_tokens"],
            cache_miss_input_tokens=value["cache_miss_input_tokens"],
            calculated_cost_micros_cny=value["calculated_cost_micros_cny"],
            balance_delta_micros_cny=value["balance_delta_micros_cny"],
            balance_delta_status=value["balance_delta_status"],
            provider_call_count=value["provider_call_count"],
            balance_read_count=value["balance_read_count"],
            replay_count=value["replay_count"],
            replay_provider_call_growth=value["replay_provider_call_growth"],
            public_case_count=value["public_case_count"],
            hidden_case_count=value["hidden_case_count"],
            source_write_count=value["source_write_count"],
            network_call_count=value["network_call_count"],
            child_process_count=value["child_process_count"],
            fixture_cleanup_count=value["fixture_cleanup_count"],
            state_trace=tuple(state_trace),
        )
        if evidence.canonical_bytes != data:
            _fail("non_canonical_evidence")
        return evidence

    def to_mapping(self) -> Mapping[str, object]:
        return {
            "balance_delta_micros_cny": self.balance_delta_micros_cny,
            "balance_delta_status": self.balance_delta_status,
            "balance_read_count": self.balance_read_count,
            "cache_hit_input_tokens": self.cache_hit_input_tokens,
            "cache_miss_input_tokens": self.cache_miss_input_tokens,
            "calculated_cost_micros_cny": self.calculated_cost_micros_cny,
            "candidate_sha256": self.candidate_sha256,
            "child_process_count": self.child_process_count,
            "contract_version": self.contract_version,
            "decision_status": self.decision_status,
            "fixture_cleanup_count": self.fixture_cleanup_count,
            "fixture_hash": self.fixture_hash,
            "hidden_case_count": self.hidden_case_count,
            "implementation_commit": self.implementation_commit,
            "input_tokens": self.input_tokens,
            "network_call_count": self.network_call_count,
            "oracle_output_sha256": self.oracle_output_sha256,
            "output_tokens": self.output_tokens,
            "patched_sha256": self.patched_sha256,
            "policy_hash": self.policy_hash,
            "provider_call_count": self.provider_call_count,
            "public_case_count": self.public_case_count,
            "reason_codes": list(self.reason_codes),
            "reasoning_sha256": self.reasoning_sha256,
            "replay_count": self.replay_count,
            "replay_provider_call_growth": self.replay_provider_call_growth,
            "request_hash": self.request_hash,
            "response_content_sha256": self.response_content_sha256,
            "response_schema_hash": self.response_schema_hash,
            "returned_model": self.returned_model,
            "source_sha256": self.source_sha256,
            "source_write_count": self.source_write_count,
            "state_trace": list(self.state_trace),
            "system_fingerprint_sha256": self.system_fingerprint_sha256,
        }

    @property
    def canonical_bytes(self) -> bytes:
        return canonical_json_bytes(self.to_mapping())


@dataclass(frozen=True, slots=True)
class ModelGateRunResultV1:
    decision: ModelGateDecisionV1
    state_trace: tuple[str, ...]
    evidence_bytes: bytes


@dataclass(slots=True)
class _RunRecord:
    request: ModelGateRequestBindingV1
    canonical_request: bytes
    result: ModelGateRunResultV1
    replay_proven: bool = False


class OfflineModelGateRunnerV1:
    """Same-process test gate; its replay ledger is deliberately not durable."""

    def __init__(
        self,
        *,
        implementation_commit: str,
        balance_reader: Callable[[], int],
        completion: Callable[[bytes, str], DeepSeekCompletionResultV1],
        verifier: Callable[[CandidateArtifactV1], SyntheticVerificationResultV1],
    ) -> None:
        if (
            not isinstance(implementation_commit, str)
            or _COMMIT_RE.fullmatch(implementation_commit) is None
        ):
            _fail("invalid_implementation_commit")
        if not all(callable(value) for value in (balance_reader, completion, verifier)):
            _fail("invalid_dependency")
        self._implementation_commit = implementation_commit
        self._balance_reader = balance_reader
        self._completion = completion
        self._verifier = verifier
        self._records: dict[str, _RunRecord] = {}

    def run(
        self,
        *,
        request: ModelGateRequestBindingV1,
        canonical_request: bytes,
        api_key: str,
    ) -> ModelGateRunResultV1:
        if not isinstance(request, ModelGateRequestBindingV1):
            _fail("invalid_request")
        try:
            canonical_json_bytes(canonical_request)
        except ModelGateContractViolation as error:
            raise ModelGateRunnerViolation("invalid_canonical_request") from error
        existing = self._records.get(request.idempotency_key)
        if existing is not None:
            assert_idempotency_replay_matches(existing.request, request)
            if existing.canonical_request != canonical_request:
                raise ModelGateContractViolation("idempotency_conflict")
            existing.replay_proven = True
            return existing.result
        _validate_first_request_binding(request, canonical_request)
        if not _valid_api_key(api_key):
            _fail("invalid_api_key")

        balance_before = self._read_balance()
        completion_result: DeepSeekCompletionResultV1 | None = None
        verification: SyntheticVerificationResultV1 | None = None
        status: Literal["admitted", "rejected", "inconclusive"]
        reason_codes: tuple[str, ...]
        trace_key: str
        try:
            completion_result = self._completion(canonical_request, api_key)
        except DeepSeekClientViolation as error:
            status = "rejected"
            reason_codes = (error.code,)
            trace_key = "rejected_after_call"
        except Exception:  # noqa: BLE001
            # Provider callbacks are untrusted; no exception detail crosses the gate.
            status = "inconclusive"
            reason_codes = ("provider_call_ambiguous",)
            trace_key = "inconclusive"
        else:
            status, reason_codes, trace_key, verification = self._evaluate_completion(
                request,
                completion_result,
            )
        try:
            balance_after = self._read_balance()
        except ModelGateRunnerViolation:
            status = "inconclusive"
            reason_codes = ("provider_call_ambiguous",)
            trace_key = "inconclusive"
            balance_delta = 0
            balance_delta_status = "ambiguous"
        else:
            if balance_after > balance_before:
                status = "inconclusive"
                reason_codes = ("provider_call_ambiguous",)
                trace_key = "inconclusive"
                balance_delta = 0
                balance_delta_status = "ambiguous"
            else:
                balance_delta = balance_before - balance_after
                balance_delta_status = "known"
        if balance_delta > request.policy.max_cost_micros_cny:
            status = "rejected"
            reason_codes = ("budget_exceeded",)
            trace_key = "rejected_after_call"
        if (
            completion_result is not None
            and completion_result.calculated_cost_micros_cny
            > request.policy.max_cost_micros_cny
        ):
            status = "rejected"
            reason_codes = ("budget_exceeded",)
            trace_key = "rejected_after_call"

        state_trace = _TERMINAL_TRACES[trace_key]
        decision = ModelGateDecisionV1(
            status=status,
            reason_codes=reason_codes,
            request_hash=request.request_hash,
        )
        evidence = self._build_evidence(
            request=request,
            decision=decision,
            completion=completion_result,
            verification=verification,
            balance_delta=balance_delta,
            balance_delta_status=balance_delta_status,
            state_trace=state_trace,
        )
        result = ModelGateRunResultV1(
            decision=decision,
            state_trace=state_trace,
            evidence_bytes=evidence.canonical_bytes,
        )
        record = _RunRecord(
            request=request,
            canonical_request=canonical_request,
            result=result,
        )
        self._records[request.idempotency_key] = record
        replay = self.run(
            request=request,
            canonical_request=canonical_request,
            api_key=api_key,
        )
        if replay is not result or not record.replay_proven:
            _fail("replay_mismatch")
        return result

    def _evaluate_completion(
        self,
        request: ModelGateRequestBindingV1,
        completion: DeepSeekCompletionResultV1,
    ) -> tuple[
        Literal["admitted", "rejected", "inconclusive"],
        tuple[str, ...],
        str,
        SyntheticVerificationResultV1 | None,
    ]:
        if (
            type(completion) is not DeepSeekCompletionResultV1
            or completion.returned_model != request.policy.requested_model
            or type(completion.provider_call_count) is not int
            or completion.provider_call_count != request.policy.max_provider_calls
        ):
            return "rejected", ("policy_violation",), "rejected_after_call", None
        try:
            verification = self._verifier(completion.candidate)
        except Exception:  # noqa: BLE001
            # Verifier callbacks are untrusted; collapse every ordinary failure.
            return (
                "rejected",
                ("candidate_verification_failed",),
                "rejected_after_validation",
                None,
            )
        expected_hashes = _expected_verification_hashes(completion.candidate)
        if (
            type(verification) is not SyntheticVerificationResultV1
            or verification.status != "passed"
            or verification.reason_code != "verified"
            or verification.source_sha256
            != hashlib.sha256(
                SyntheticRepairFixtureV1.default().source_bytes
            ).hexdigest()
            or not isinstance(verification.patched_sha256, str)
            or _HASH_RE.fullmatch(verification.patched_sha256) is None
            or expected_hashes is None
            or verification.patched_sha256 != expected_hashes[0]
            or not isinstance(verification.oracle_output_sha256, str)
            or _HASH_RE.fullmatch(verification.oracle_output_sha256) is None
            or verification.oracle_output_sha256 != expected_hashes[1]
            or type(verification.public_case_count) is not int
            or verification.public_case_count
            != SyntheticRepairFixtureV1.default().public_case_count
            or type(verification.hidden_case_count) is not int
            or verification.hidden_case_count
            != SyntheticRepairFixtureV1.default().hidden_case_count
            or type(verification.source_write_count) is not int
            or verification.source_write_count != 0
            or type(verification.network_call_count) is not int
            or verification.network_call_count != 0
            or type(verification.child_process_count) is not int
            or verification.child_process_count != 1
            or type(verification.fixture_cleanup_count) is not int
            or verification.fixture_cleanup_count != 1
        ):
            return (
                "rejected",
                ("candidate_verification_failed",),
                "rejected_after_validation",
                verification,
            )
        return "admitted", (), "admitted", verification

    def _read_balance(self) -> int:
        try:
            value = self._balance_reader()
        except Exception:  # noqa: BLE001
            raise ModelGateRunnerViolation("balance_ambiguous") from None
        if type(value) is not int or value < 0:
            _fail("balance_ambiguous")
        return value

    def _build_evidence(
        self,
        *,
        request: ModelGateRequestBindingV1,
        decision: ModelGateDecisionV1,
        completion: DeepSeekCompletionResultV1 | None,
        verification: SyntheticVerificationResultV1 | None,
        balance_delta: int,
        balance_delta_status: Literal["known", "ambiguous"],
        state_trace: tuple[str, ...],
    ) -> ModelGateEvidenceV1:
        return ModelGateEvidenceV1(
            contract_version=_EVIDENCE_VERSION,
            implementation_commit=self._implementation_commit,
            request_hash=request.request_hash,
            policy_hash=request.policy.policy_hash,
            fixture_hash=request.fixture_hash,
            response_schema_hash=request.response_schema_hash,
            decision_status=decision.status,
            reason_codes=decision.reason_codes,
            returned_model=completion.returned_model if completion else None,
            response_content_sha256=(
                completion.response_content_sha256 if completion else None
            ),
            reasoning_sha256=completion.reasoning_sha256 if completion else None,
            system_fingerprint_sha256=(
                completion.system_fingerprint_sha256 if completion else None
            ),
            candidate_sha256=_candidate_hash(completion.candidate)
            if completion
            else None,
            source_sha256=verification.source_sha256 if verification else None,
            patched_sha256=verification.patched_sha256 if verification else None,
            oracle_output_sha256=(
                verification.oracle_output_sha256 if verification else None
            ),
            input_tokens=completion.input_tokens if completion else 0,
            output_tokens=completion.output_tokens if completion else 0,
            cache_hit_input_tokens=(
                completion.cache_hit_input_tokens if completion else 0
            ),
            cache_miss_input_tokens=(
                completion.cache_miss_input_tokens if completion else 0
            ),
            calculated_cost_micros_cny=(
                completion.calculated_cost_micros_cny if completion else 0
            ),
            balance_delta_micros_cny=balance_delta,
            balance_delta_status=balance_delta_status,
            provider_call_count=completion.provider_call_count if completion else 1,
            balance_read_count=2,
            replay_count=1,
            replay_provider_call_growth=0,
            public_case_count=verification.public_case_count if verification else 0,
            hidden_case_count=verification.hidden_case_count if verification else 0,
            source_write_count=verification.source_write_count if verification else 0,
            network_call_count=verification.network_call_count if verification else 0,
            child_process_count=verification.child_process_count if verification else 0,
            fixture_cleanup_count=(
                verification.fixture_cleanup_count if verification else 0
            ),
            state_trace=state_trace,
        )

    def validate_evidence_bytes(
        self,
        *,
        request: ModelGateRequestBindingV1,
        data: bytes,
    ) -> ModelGateEvidenceV1:
        if not isinstance(request, ModelGateRequestBindingV1):
            _fail("invalid_request")
        record = self._records.get(request.idempotency_key)
        if record is None or not record.replay_proven:
            _fail("unknown_request")
        assert_idempotency_replay_matches(record.request, request)
        evidence = ModelGateEvidenceV1.from_json_bytes(data)
        if data != record.result.evidence_bytes:
            _fail("evidence_mismatch")
        return evidence


_VALID_PATCH = """--- a/synthetic_target.py
+++ b/synthetic_target.py
@@ -1,2 +1,4 @@
 def clamp_score(value):
-    return max(0, value)
+    if isinstance(value, bool) or not isinstance(value, int):
+        raise TypeError("value must be an integer")
+    return max(0, min(100, value))
"""


def _offline_evidence(implementation_commit: str) -> bytes:
    fixture = SyntheticRepairFixtureV1.default()
    candidate = CandidateArtifactV1(
        artifact_version="g2-a0-candidate-v1",
        claimed_test_scope=("public_behavior",),
        language="python",
        summary_code="bounded_repair",
        unified_diff=_VALID_PATCH,
    )
    completion = DeepSeekCompletionResultV1(
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
        candidate=candidate,
    )
    balances = iter((9_000_000, 8_999_983))
    temp_root = Path(tempfile.mkdtemp(prefix="g2_a0_gate_"))
    try:
        policy = DeepSeekModelGatePolicyV1.default()
        request, canonical_request = _live_request(
            fixture=fixture,
            idempotency_key="idem_00000000000000000000000000000000",
            policy=policy,
        )
        runner = OfflineModelGateRunnerV1(
            implementation_commit=implementation_commit,
            balance_reader=lambda: next(balances),
            completion=lambda canonical_request, api_key: completion,
            verifier=lambda value: verify_candidate_patch(
                fixture=fixture,
                candidate=value,
                temp_root=temp_root,
            ),
        )
        result = runner.run(
            request=request,
            canonical_request=canonical_request,
            api_key="test-process-placeholder",
        )
        return result.evidence_bytes
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _parse_balance_micros(data: bytes) -> int:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        document: dict[str, object] = {}
        for key, value in pairs:
            if key in document:
                _fail("balance_ambiguous")
            document[key] = value
        return document

    try:
        document = json.loads(
            data.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
        )
    except ModelGateRunnerViolation:
        raise
    except (UnicodeDecodeError, ValueError, RecursionError):
        _fail("balance_ambiguous")
    if not isinstance(document, dict) or set(document) != {
        "balance_infos",
        "is_available",
    }:
        _fail("balance_ambiguous")
    if document["is_available"] is not True:
        _fail("balance_ambiguous")
    infos = document["balance_infos"]
    if not isinstance(infos, list) or len(infos) != 1:
        _fail("balance_ambiguous")
    info = infos[0]
    if not isinstance(info, dict) or set(info) != {
        "currency",
        "granted_balance",
        "topped_up_balance",
        "total_balance",
    }:
        _fail("balance_ambiguous")
    if info["currency"] != "CNY":
        _fail("balance_ambiguous")

    values: dict[str, Decimal] = {}
    for field_name in ("granted_balance", "topped_up_balance", "total_balance"):
        raw = info[field_name]
        if not isinstance(raw, str) or _BALANCE_RE.fullmatch(raw) is None:
            _fail("balance_ambiguous")
        try:
            values[field_name] = Decimal(raw)
        except InvalidOperation:
            _fail("balance_ambiguous")
    if (
        values["granted_balance"] + values["topped_up_balance"]
        != values["total_balance"]
    ):
        _fail("balance_ambiguous")
    micros = values["total_balance"] * 1_000_000
    if micros != micros.to_integral_value():
        _fail("balance_ambiguous")
    return int(micros)


def _balance_reader(
    *,
    api_key: str,
    policy: DeepSeekModelGatePolicyV1,
    transport_factory: Callable[[], httpx.BaseTransport],
) -> int:
    transport = transport_factory()
    if not isinstance(transport, httpx.BaseTransport):
        _fail("balance_ambiguous")
    try:
        with httpx.Client(
            base_url=policy.provider_origin,
            transport=transport,
            timeout=httpx.Timeout(policy.timeout_seconds),
            follow_redirects=False,
            trust_env=False,
        ) as http:
            response = http.get(
                policy.balance_path,
                headers={"Authorization": f"Bearer {api_key}"},
            )
    except Exception:  # noqa: BLE001
        # Redact transport and injected-handler failures alike.
        _fail("balance_ambiguous")
    if response.status_code != 200 or len(response.content) > 65_536:
        _fail("balance_ambiguous")
    content_type = response.headers.get("content-type", "").split(";", 1)[0]
    if content_type.strip().lower() != "application/json":
        _fail("balance_ambiguous")
    return _parse_balance_micros(response.content)


def _live_request(
    *,
    fixture: SyntheticRepairFixtureV1,
    idempotency_key: str,
    policy: DeepSeekModelGatePolicyV1,
) -> tuple[ModelGateRequestBindingV1, bytes]:
    prompt = (
        f"{fixture.public_prompt}\n"
        f"Public example: {fixture.public_example}.\n"
        f"Use this exact response shape: {RESPONSE_EXAMPLE_JSON}"
    )
    canonical_request = canonical_json_bytes(
        {
            "max_tokens": policy.max_tokens,
            "messages": [{"content": prompt, "role": "user"}],
            "model": policy.requested_model,
            "reasoning_effort": policy.reasoning_effort,
            "response_format": {"type": "json_object"},
            "stream": False,
            "thinking": {"type": policy.thinking_type},
        }
    )
    fixture_bytes = canonical_json_bytes(
        {
            "fixture_version": fixture.fixture_version,
            "hidden_case_count": fixture.hidden_case_count,
            "public_case_count": fixture.public_case_count,
            "source_sha256": hashlib.sha256(fixture.source_bytes).hexdigest(),
        }
    )
    return (
        ModelGateRequestBindingV1(
            contract_version="g2-a0-model-gate-request-v1",
            idempotency_key=idempotency_key,
            policy=policy,
            prompt_hash=hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
            fixture_hash=hashlib.sha256(fixture_bytes).hexdigest(),
            response_schema_hash=hashlib.sha256(
                RESPONSE_EXAMPLE_JSON.encode("utf-8")
            ).hexdigest(),
        ),
        canonical_request,
    )


def _default_transport_factory() -> httpx.BaseTransport:
    return httpx.HTTPTransport(retries=0)


def execute_live_probe(
    *,
    api_key: str,
    authorization_marker: str,
    idempotency_key: str,
    implementation_commit: str,
    transport_factory: Callable[[], httpx.BaseTransport] = _default_transport_factory,
) -> bytes:
    if authorization_marker != G2_A0_PAID_RUN_AUTHORIZATION:
        _fail("live_authorization_required")
    if not _valid_api_key(api_key):
        _fail("invalid_api_key")
    if (
        not isinstance(idempotency_key, str)
        or _IDEMPOTENCY_RE.fullmatch(idempotency_key) is None
    ):
        _fail("invalid_idempotency_key")
    if (
        not isinstance(implementation_commit, str)
        or _COMMIT_RE.fullmatch(implementation_commit) is None
    ):
        _fail("invalid_implementation_commit")
    if not callable(transport_factory):
        _fail("invalid_transport_factory")

    policy = DeepSeekModelGatePolicyV1.default()
    fixture = SyntheticRepairFixtureV1.default()
    request, canonical_request = _live_request(
        fixture=fixture,
        idempotency_key=idempotency_key,
        policy=policy,
    )
    completion_client = DeepSeekTransportClientV1(
        policy=policy,
        transport=transport_factory(),
    )
    temp_root = Path(tempfile.mkdtemp(prefix="g2_a0_live_gate_"))
    try:
        runner = OfflineModelGateRunnerV1(
            implementation_commit=implementation_commit,
            balance_reader=lambda: _balance_reader(
                api_key=api_key,
                policy=policy,
                transport_factory=transport_factory,
            ),
            completion=lambda payload, secret: completion_client.complete_once(
                canonical_request=payload,
                api_key=secret,
            ),
            verifier=lambda candidate: verify_candidate_patch(
                fixture=fixture,
                candidate=candidate,
                temp_root=temp_root,
            ),
        )
        first = runner.run(
            request=request,
            canonical_request=canonical_request,
            api_key=api_key,
        )
        try:
            runner.run(
                request=replace(request, prompt_hash="0" * 64),
                canonical_request=canonical_request,
                api_key=api_key,
            )
        except ModelGateContractViolation as error:
            if error.code != "idempotency_conflict":
                raise
        else:
            _fail("changed_replay_accepted")
        return runner.validate_evidence_bytes(
            request=request,
            data=first.evidence_bytes,
        ).canonical_bytes
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)


def _find_repository() -> Path:
    current = Path(__file__).resolve().parent
    for directory in (current, *current.parents):
        marker = directory / ".git"
        if not marker.exists():
            continue
        return directory
    _fail("source_readback_failed")


def _find_git_commit() -> str:
    repository = _find_repository()
    marker = repository / ".git"
    if marker.exists():
        git_dir = marker
        if marker.is_file():
            line = marker.read_text(encoding="utf-8").strip()
            if not line.startswith("gitdir: "):
                _fail("source_readback_failed")
            git_dir = Path(line[8:])
        head = (git_dir / "HEAD").read_text(encoding="ascii").strip()
        if _COMMIT_RE.fullmatch(head):
            return head
        if not head.startswith("ref: "):
            _fail("source_readback_failed")
        ref_name = head[5:]
        common_dir = git_dir
        common_file = git_dir / "commondir"
        if common_file.is_file():
            common_dir = (
                git_dir / common_file.read_text(encoding="ascii").strip()
            ).resolve()
        ref_path = common_dir / ref_name
        if ref_path.is_file():
            commit = ref_path.read_text(encoding="ascii").strip()
            if _COMMIT_RE.fullmatch(commit):
                return commit
        packed = common_dir / "packed-refs"
        if packed.is_file():
            for line in packed.read_text(encoding="ascii").splitlines():
                if line.endswith(f" {ref_name}"):
                    commit = line.split(" ", 1)[0]
                    if _COMMIT_RE.fullmatch(commit):
                        return commit
    _fail("source_readback_failed")


def _read_git_blob(repository: Path, commit: str, relative_path: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repository), "show", f"{commit}:{relative_path}"],
            check=False,
            capture_output=True,
            shell=False,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        _fail("source_binding_mismatch")
    if result.returncode != 0:
        _fail("source_binding_mismatch")
    return result.stdout


def _verify_runtime_source(
    commit: str,
    *,
    repository: Path | None = None,
    blob_reader: Callable[[Path, str, str], bytes] = _read_git_blob,
) -> None:
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        _fail("source_binding_mismatch")
    source_repository = _find_repository() if repository is None else repository
    for relative_path in _RUNTIME_SOURCE_PATHS:
        current_path = source_repository / relative_path
        if not current_path.is_file() or current_path.is_symlink():
            _fail("source_binding_mismatch")
        try:
            committed_bytes = blob_reader(
                source_repository,
                commit,
                relative_path,
            )
        except ModelGateRunnerViolation:
            raise
        except Exception:  # noqa: BLE001
            raise ModelGateRunnerViolation("source_binding_mismatch") from None
        if current_path.read_bytes() != committed_bytes:
            _fail("source_binding_mismatch")


def _emit(output: BinaryIO, document: Mapping[str, object] | bytes) -> None:
    payload = (
        document if isinstance(document, bytes) else canonical_json_bytes(document)
    )
    output.write(payload + b"\n")


def _rejection(reason_code: str) -> Mapping[str, object]:
    return {"reason_code": reason_code, "status": "rejected"}


def main(
    argv: list[str] | None = None,
    *,
    environment: Mapping[str, str] | None = None,
    output: BinaryIO | None = None,
    source_commit_reader: Callable[[], str] = _find_git_commit,
    source_binding_checker: Callable[[str], None] = _verify_runtime_source,
    live_execute: Callable[..., bytes] | None = None,
) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--offline-fixture", action="store_true")
    modes.add_argument("--live", action="store_true")
    parser.add_argument("--authorization-marker")
    parser.add_argument("--implementation-commit")
    parser.add_argument("--idempotency-key")
    try:
        arguments = parser.parse_args(argv)
    except SystemExit:
        return 2
    sink = output or sys.stdout.buffer
    try:
        source_commit = source_commit_reader()
    except Exception:  # noqa: BLE001
        # Source readers are injected at this boundary and must fail closed.
        _emit(sink, _rejection("source_readback_failed"))
        return 2
    if (
        not isinstance(source_commit, str)
        or _COMMIT_RE.fullmatch(source_commit) is None
    ):
        _emit(sink, _rejection("source_readback_failed"))
        return 2
    if arguments.offline_fixture:
        try:
            source_binding_checker(source_commit)
        except Exception:  # noqa: BLE001
            _emit(sink, _rejection("source_binding_mismatch"))
            return 2
        _emit(sink, _offline_evidence(source_commit))
        return 0
    if arguments.authorization_marker != G2_A0_PAID_RUN_AUTHORIZATION:
        _emit(sink, _rejection("live_authorization_required"))
        return 2
    if (
        arguments.implementation_commit != source_commit
        or _COMMIT_RE.fullmatch(arguments.implementation_commit or "") is None
    ):
        _emit(sink, _rejection("source_binding_mismatch"))
        return 2
    try:
        source_binding_checker(source_commit)
    except Exception:  # noqa: BLE001
        _emit(sink, _rejection("source_binding_mismatch"))
        return 2
    if (
        not isinstance(arguments.idempotency_key, str)
        or _IDEMPOTENCY_RE.fullmatch(arguments.idempotency_key) is None
    ):
        _emit(sink, _rejection("invalid_idempotency_key"))
        return 2
    process_environment = environment if environment is not None else {}
    api_key = process_environment.get("DEEPSEEK_API_KEY")
    if not _valid_api_key(api_key):
        _emit(sink, _rejection("process_secret_required"))
        return 2
    selected_live_execute = live_execute or execute_live_probe
    try:
        evidence = selected_live_execute(
            api_key=api_key,
            authorization_marker=arguments.authorization_marker,
            idempotency_key=arguments.idempotency_key,
            implementation_commit=source_commit,
        )
        parsed_evidence = ModelGateEvidenceV1.from_json_bytes(evidence)
        if parsed_evidence.implementation_commit != source_commit:
            _fail("source_binding_mismatch")
    except Exception:  # noqa: BLE001
        # Live execution is an injected boundary; never emit provider detail.
        _emit(sink, _rejection("live_execution_failed"))
        return 2
    _emit(sink, parsed_evidence.canonical_bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:], environment=os.environ))
