from __future__ import annotations

import hashlib
import json
import re
import shutil
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, fields, replace
from pathlib import Path
from typing import Literal

import httpx
from g2_a0_deepseek_client import (
    RESPONSE_EXAMPLE_JSON,
    CandidateArtifactV1,
    DeepSeekClientViolation,
    DeepSeekCompletionResultV1,
    DeepSeekTransportClientV1,
)
from g2_a0_model_gate_cli import (
    _EVIDENCE_FIELDS,
    _RUNTIME_SOURCE_PATHS,
    _TERMINAL_TRACES,
    ModelGateEvidenceV1,
    ModelGateRunnerViolation,
    OfflineModelGateRunnerV1,
    _balance_reader,
    _candidate_hash,
    _find_repository,
    _read_git_blob,
    _valid_api_key,
    _validate_first_request_binding,
)
from g2_a0_synthetic_fixture import SyntheticRepairFixtureV1
from g2_a0_synthetic_verifier import (
    SyntheticVerificationResultV1,
    verify_candidate_patch,
)

from platform_protocol.g2_a0_model_gate import (
    ModelGateContractViolation,
    ModelGateDecisionV1,
    canonical_json_bytes,
)
from platform_protocol.g2_a0_model_gate_v3 import (
    MAX_COST_MICROS_CNY_V3,
    MODEL_GATE_REQUEST_VERSION_V3,
    DeepSeekModelGatePolicyV3,
    ModelGateRequestBindingV3,
    assert_v3_idempotency_replay_matches,
)

G2_A0_PAID_RUN_AUTHORIZATION_V3 = "authorize-g2-a0-one-call-max-cny-10-v3"
MODEL_GATE_EVIDENCE_VERSION_V3 = "g2-a0-model-gate-evidence-v3"

_V1_EVIDENCE_VERSION = "g2-a0-model-gate-evidence-v1"
_COMMIT_RE = re.compile(r"[0-9a-f]{40}")
_IDEMPOTENCY_RE = re.compile(r"idem_[0-9a-f]{32}")
_RUNTIME_SOURCE_PATHS_V3 = (
    *_RUNTIME_SOURCE_PATHS,
    "phase3/backend/platform_protocol/g2_a0_model_gate_v3.py",
    "phase3/backend/tests/platform_protocol/g2_a0_model_gate_v3_cli.py",
)


def _fail(code: str) -> None:
    raise ModelGateRunnerViolation(code)


def _verify_runtime_source_v3(
    commit: str,
    *,
    repository: Path | None = None,
    blob_reader: Callable[[Path, str, str], bytes] = _read_git_blob,
) -> None:
    if not isinstance(commit, str) or _COMMIT_RE.fullmatch(commit) is None:
        _fail("source_binding_mismatch")
    source_repository = _find_repository() if repository is None else repository
    for relative_path in _RUNTIME_SOURCE_PATHS_V3:
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


class _DeepSeekTransportClientV3(DeepSeekTransportClientV1):
    def __post_init__(self) -> None:
        if type(self.policy) is not DeepSeekModelGatePolicyV3:
            _fail("policy_violation")
        if not isinstance(self.transport, httpx.BaseTransport):
            _fail("policy_violation")


def _evidence_kwargs(evidence: ModelGateEvidenceV1) -> dict[str, object]:
    return {field.name: getattr(evidence, field.name) for field in fields(evidence)}


@dataclass(frozen=True, slots=True)
class ModelGateEvidenceV3(ModelGateEvidenceV1):
    def __post_init__(self) -> None:
        if self.contract_version != MODEL_GATE_EVIDENCE_VERSION_V3:
            _fail("invalid_contract_version")
        values = _evidence_kwargs(self)
        values["contract_version"] = _V1_EVIDENCE_VERSION
        values["returned_model"] = None  # validated against the V3 allowlist below
        ModelGateEvidenceV1(**values)  # type: ignore[arg-type]
        if self.returned_model not in self._allowed_returned_models():
            _fail("invalid_returned_model")
        over_limit = (
            self.calculated_cost_micros_cny > MAX_COST_MICROS_CNY_V3
            or self.balance_delta_micros_cny > MAX_COST_MICROS_CNY_V3
        )
        is_budget_rejection = (
            self.decision_status == "rejected"
            and self.reason_codes == ("budget_exceeded",)
            and self.state_trace == _TERMINAL_TRACES["rejected_after_call"]
        )
        if over_limit != is_budget_rejection:
            _fail("budget_evidence_mismatch")

    def _allowed_returned_models(self) -> frozenset[str | None]:
        return frozenset({None, "deepseek-v4-flash"})

    @classmethod
    def from_json_bytes(cls, data: bytes) -> ModelGateEvidenceV3:
        canonical_json_bytes(data)
        value = json.loads(data)
        if not isinstance(value, dict) or set(value) != _EVIDENCE_FIELDS:
            _fail("unexpected_evidence_fields")
        if value.get("contract_version") != MODEL_GATE_EVIDENCE_VERSION_V3:
            _fail("invalid_contract_version")
        if value.get("returned_model") not in {None, "deepseek-v4-flash"}:
            _fail("invalid_returned_model")
        v1_document = dict(value)
        v1_document["contract_version"] = _V1_EVIDENCE_VERSION
        v1_document["returned_model"] = None  # validated against the V3 allowlist above
        v1 = ModelGateEvidenceV1.from_json_bytes(canonical_json_bytes(v1_document))
        values = _evidence_kwargs(v1)
        values["contract_version"] = MODEL_GATE_EVIDENCE_VERSION_V3
        values["returned_model"] = value["returned_model"]
        evidence = cls(**values)  # type: ignore[arg-type]
        if evidence.canonical_bytes != data:
            _fail("non_canonical_evidence")
        return evidence


@dataclass(frozen=True, slots=True)
class ModelGateRunResultV3:
    decision: ModelGateDecisionV1
    state_trace: tuple[str, ...]
    evidence_bytes: bytes


@dataclass(slots=True)
class _RunRecordV3:
    request: ModelGateRequestBindingV3
    canonical_request: bytes
    result: ModelGateRunResultV3
    replay_proven: bool = False


class OfflineModelGateRunnerV3:
    """Same-process, injected-dependency V3 gate with no durable secrets."""

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
        self._records: dict[str, _RunRecordV3] = {}

    def run(
        self,
        *,
        request: ModelGateRequestBindingV3,
        canonical_request: bytes,
        api_key: str,
    ) -> ModelGateRunResultV3:
        if type(request) is not ModelGateRequestBindingV3:
            _fail("invalid_request")
        try:
            canonical_json_bytes(canonical_request)
        except ModelGateContractViolation as error:
            raise ModelGateRunnerViolation("invalid_canonical_request") from error
        existing = self._records.get(request.idempotency_key)
        if existing is not None:
            assert_v3_idempotency_replay_matches(existing.request, request)
            if existing.canonical_request != canonical_request:
                raise ModelGateContractViolation("idempotency_conflict")
            existing.replay_proven = True
            return existing.result
        _validate_first_request_binding(request, canonical_request)  # type: ignore[arg-type]
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
            if error.code == "budget_exceeded":
                status = "inconclusive"
                reason_codes = ("provider_call_ambiguous",)
                trace_key = "inconclusive"
            else:
                status = "rejected"
                reason_codes = (error.code,)
                trace_key = "rejected_after_call"
        except Exception:  # noqa: BLE001
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
            balance_delta_status: Literal["known", "ambiguous"] = "ambiguous"
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
        result = ModelGateRunResultV3(
            decision=decision,
            state_trace=state_trace,
            evidence_bytes=evidence.canonical_bytes,
        )
        record = _RunRecordV3(
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

    def _read_balance(self) -> int:
        return OfflineModelGateRunnerV1._read_balance(self)  # type: ignore[arg-type]

    def _evaluate_completion(
        self,
        request: ModelGateRequestBindingV3,
        completion: DeepSeekCompletionResultV1,
    ) -> tuple[
        Literal["admitted", "rejected", "inconclusive"],
        tuple[str, ...],
        str,
        SyntheticVerificationResultV1 | None,
    ]:
        return OfflineModelGateRunnerV1._evaluate_completion(  # type: ignore[arg-type]
            self,
            request,
            completion,
        )

    def _build_evidence(
        self,
        *,
        request: ModelGateRequestBindingV3,
        decision: ModelGateDecisionV1,
        completion: DeepSeekCompletionResultV1 | None,
        verification: SyntheticVerificationResultV1 | None,
        balance_delta: int,
        balance_delta_status: Literal["known", "ambiguous"],
        state_trace: tuple[str, ...],
    ) -> ModelGateEvidenceV3:
        return ModelGateEvidenceV3(
            contract_version=MODEL_GATE_EVIDENCE_VERSION_V3,
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
        request: ModelGateRequestBindingV3,
        data: bytes,
    ) -> ModelGateEvidenceV3:
        if type(request) is not ModelGateRequestBindingV3:
            _fail("invalid_request")
        record = self._records.get(request.idempotency_key)
        if record is None or not record.replay_proven:
            _fail("unknown_request")
        assert_v3_idempotency_replay_matches(record.request, request)
        evidence = ModelGateEvidenceV3.from_json_bytes(data)
        if data != record.result.evidence_bytes:
            _fail("evidence_mismatch")
        return evidence


def build_request_v3(
    *,
    fixture: SyntheticRepairFixtureV1,
    idempotency_key: str,
    policy: DeepSeekModelGatePolicyV3,
) -> tuple[ModelGateRequestBindingV3, bytes]:
    if type(fixture) is not SyntheticRepairFixtureV1:
        _fail("invalid_fixture")
    if type(policy) is not DeepSeekModelGatePolicyV3:
        _fail("invalid_policy")
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
        ModelGateRequestBindingV3(
            contract_version=MODEL_GATE_REQUEST_VERSION_V3,
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


def execute_probe_v3(
    *,
    api_key: str,
    authorization_marker: str,
    idempotency_key: str,
    implementation_commit: str,
    balance_reader: Callable[[], int],
    completion: Callable[[bytes, str], DeepSeekCompletionResultV1],
    verifier: Callable[[CandidateArtifactV1], SyntheticVerificationResultV1],
    source_binding_checker: Callable[[str], None] = _verify_runtime_source_v3,
) -> bytes:
    if authorization_marker != G2_A0_PAID_RUN_AUTHORIZATION_V3:
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
    if not all(
        callable(value)
        for value in (
            balance_reader,
            completion,
            verifier,
            source_binding_checker,
        )
    ):
        _fail("invalid_dependency")
    try:
        source_binding_checker(implementation_commit)
    except Exception:  # noqa: BLE001
        _fail("source_binding_mismatch")

    fixture = SyntheticRepairFixtureV1.default()
    request, canonical_request = build_request_v3(
        fixture=fixture,
        idempotency_key=idempotency_key,
        policy=DeepSeekModelGatePolicyV3.default(),
    )
    runner = OfflineModelGateRunnerV3(
        implementation_commit=implementation_commit,
        balance_reader=balance_reader,
        completion=completion,
        verifier=verifier,
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


def _default_transport_factory_v3() -> httpx.BaseTransport:
    return httpx.HTTPTransport(retries=0)


def execute_live_probe_v3(
    *,
    api_key: str,
    authorization_marker: str,
    idempotency_key: str,
    implementation_commit: str,
    transport_factory: Callable[
        [], httpx.BaseTransport
    ] = _default_transport_factory_v3,
    source_binding_checker: Callable[[str], None] = _verify_runtime_source_v3,
) -> bytes:
    if authorization_marker != G2_A0_PAID_RUN_AUTHORIZATION_V3:
        _fail("live_authorization_required")
    if not callable(transport_factory) or not callable(source_binding_checker):
        _fail("invalid_dependency")
    try:
        source_binding_checker(implementation_commit)
    except Exception:  # noqa: BLE001
        _fail("source_binding_mismatch")

    policy = DeepSeekModelGatePolicyV3.default()
    completion_client = _DeepSeekTransportClientV3(
        policy=policy,  # type: ignore[arg-type]
        transport=transport_factory(),
    )
    fixture = SyntheticRepairFixtureV1.default()
    temp_root = Path(tempfile.mkdtemp(prefix="g2_a0_v3_live_gate_"))
    try:
        return execute_probe_v3(
            api_key=api_key,
            authorization_marker=authorization_marker,
            idempotency_key=idempotency_key,
            implementation_commit=implementation_commit,
            balance_reader=lambda: _balance_reader(
                api_key=api_key,
                policy=policy,  # type: ignore[arg-type]
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
            source_binding_checker=lambda commit: None,
        )
    finally:
        shutil.rmtree(temp_root, ignore_errors=True)
