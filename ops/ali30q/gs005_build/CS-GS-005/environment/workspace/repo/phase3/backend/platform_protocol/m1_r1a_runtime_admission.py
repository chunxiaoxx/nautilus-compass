"""Source-bound admission for the single local R1a synthetic repair runtime."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from platform_protocol.contracts import PROTOCOL_CONTRACT_VERSION
from platform_protocol.keys import ED25519_V1
from platform_protocol.m1_r1a_admission import (
    AdmissionViolation,
    LocalGitSourceReadback,
    SourceReadback,
)
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_CONTRACT_VERSION,
    EVIDENCE_VECTOR_SET_VERSION,
    EVIDENCE_VECTOR_SHA256,
)

_ADMISSION_SCHEMA = "m1-r1a-runtime-admission-v1"
_V5_EXECUTOR_SCHEMA = "m1-r1a-v5-ephemeral-signer-owner-input-v3"
_G1_B_COMMIT = "082725c46c2a476390f28fa8fb223966e6af09d3"
_G1_A_COMMIT = "21a36fd2cfc8a2223454d1f7c5bc542045910291"
_V5_AUTHORITY = "f560be28ecac550e754eff2b82e36ea91ecad0b6"
_V5_PLAN_PROPOSAL = "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94"
_V5_EXECUTOR_AUTHORITY = "4c18c5a70c16d1d6797f9b71ff96aa58e5a41a67"
_V5_EXECUTOR_PROPOSAL = "f3d94d32fce6316e84628c63754468ba608a1595"
_COMPASS_AUTHORITY = "37efc4fc2f7455202c94515b29314af9e5e2e16e"
_COMPASS_PROPOSAL = "e87234bbdc072bd10e9b88079c21f7c574361506"

_DESIGN_PATH = "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-design.md"
_DESIGN_SHA256 = "15f6d4c127d3ae30afe0ff53cadddbfcf5772be0c522000bcd65b08f8de29f20"
_PLAN_PATH = "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-implementation-plan.md"
_PLAN_SHA256 = "ddeaf76937bb72631832be7fc5fbee2452e328f7b3ec854e2ba1ae3cd1e88c72"
_G1_A_PATH = "phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json"
_G1_A_GIT_BLOB_SHA256 = (
    "92fb2662243b7bbbabcee9de6a4057ab3b11597405a8d40e49b4f9f1bd490a5b"
)
_G1_A_LEGACY_WINDOWS_SHA256 = (
    "f96c61157a977ad30f6299d5c4cbc01b0f965033511464a349bb7f4fd3127bea"
)
_V5_PLAN_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_V5_PLAN_SHA256 = "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
_V5_EXECUTOR_PATH = "docs/contracts/m1-r1a-ephemeral-signer-v3.json"
_V5_EXECUTOR_SHA256 = "dbd18532f30f58a6e59355f3584d609026bda839f49d31e017eeb27b38a4dc29"
_COMPASS_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"
_COMPASS_SHA256 = "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
_PROTOCOL_VECTOR_SHA256 = (
    "d3aa6361ab3152ff3a14e1887a5ed3b8ceac532c2f1392eea1ca3312e9f6fe29"
)
_PROTOCOL_VECTOR_SET_VERSION = "protocol-v2-conformance-v1"
_PROTOCOL_VECTOR_PATH = "platform_protocol/conformance_vectors_v2.json"
_EVIDENCE_VECTOR_PATH = "platform_protocol/m1_r1a_execution_evidence_vectors_v1.json"

_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_TOP_FIELDS = frozenset(
    {
        "authorization",
        "compass_input",
        "decision",
        "g1_a",
        "g1_b_plan",
        "protocol",
        "schema_version",
        "v5_executor_input",
        "v5_plan_only_input",
    }
)
_AUTHORIZATION_FIELDS = frozenset(
    {
        "allowed_action",
        "database_authorized",
        "deployment_authorized",
        "fde_authorized",
        "model_authorized",
        "network_authorized",
        "production_authorized",
        "runtime_authorized",
        "tool_execution_authorized",
    }
)
_G1_B_FIELDS = frozenset(
    {
        "commit",
        "design_path",
        "design_sha256",
        "implementation_plan_path",
        "implementation_plan_sha256",
    }
)
_G1_A_FIELDS = frozenset(
    {
        "commit",
        "evidence_git_blob_sha256",
        "evidence_path",
        "legacy_windows_worktree_sha256",
        "status",
    }
)
_V5_PLAN_FIELDS = frozenset(
    {
        "allowed_action",
        "authority_commit",
        "authorization_path",
        "authorization_sha256",
        "proposal_commit",
        "runtime_authorized",
    }
)
_COMPASS_FIELDS = frozenset(
    {
        "authority_commit",
        "capsule_path",
        "capsule_sha256",
        "proposal_commit",
        "runtime_authorized",
    }
)
_V5_EXECUTOR_FIELDS = frozenset(
    {
        "authority_commit",
        "contract_path",
        "contract_sha256",
        "owner",
        "proposal_commit",
        "proposal_status",
        "runtime_authorized",
        "test_status",
    }
)
_PROTOCOL_FIELDS = frozenset(
    {
        "conformance_vector_path",
        "conformance_vector_sha256",
        "conformance_vector_set_version",
        "contract_version",
        "execution_evidence_contract_version",
        "execution_evidence_vector_path",
        "execution_evidence_vector_set_version",
        "execution_evidence_vector_sha256",
    }
)
_DECISION_FIELDS = frozenset({"reason_codes", "status"})

_OWNER_CONTRACT_FIELDS = frozenset(
    {
        "authorization",
        "authority_commit",
        "bindings",
        "capabilities",
        "executor",
        "owner",
        "schema_version",
        "scope_evidence_policy",
        "session",
        "test_status",
    }
)
_OWNER_AUTHORIZATION_FIELDS = frozenset(
    {
        "database_authorized",
        "environment_key_authorized",
        "general_rpc_authorized",
        "model_authorized",
        "network_authorized",
        "private_key_persistence_authorized",
        "self_modify_authorized",
        "shell_authorized",
        "source_write_authorized",
        "tool_gateway_authorized",
    }
)
_OWNER_BINDING_FIELDS = frozenset(
    {
        "announcement_version",
        "evidence_contract_version",
        "artifact_sha256",
        "bound_capsule_sha256",
        "capability",
        "execution_request_version",
        "execution_result_version",
        "fixture_sha256",
        "session_protocol_version",
        "tool_policy_sha256",
    }
)
_OWNER_EXECUTOR_FIELDS = frozenset(
    {
        "identity_id",
        "key_id",
        "public_key_policy",
        "release",
        "signature_algorithm",
    }
)
_OWNER_SESSION_FIELDS = frozenset(
    {
        "challenge_authority",
        "entrypoint",
        "import_policy",
        "max_announce_challenges",
        "max_challenge_ttl_seconds",
        "max_execution_requests",
        "private_key_lifetime",
        "state_machine",
        "transport",
    }
)
_OWNER_SCOPE_POLICY_FIELDS = frozenset({"allowed_modes", "complete", "missing_scope"})
_OWNER_SCOPE_OUTCOME_FIELDS = frozenset({"result_state", "scope_evidence_ids"})


class R1aRuntimeSourceReadback(SourceReadback, Protocol):
    """Trusted Git authority that can return exact immutable blob bytes."""

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        """Read one fixed path at a verified full commit."""


class LocalR1aRuntimeSourceReadback(LocalGitSourceReadback):
    """Local read-only implementation over the three owner repositories."""

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        self.require_commit(owner, commit)
        return self._show_file(owner, commit, path)


@dataclass(frozen=True, slots=True)
class R1aRuntimeAdmissionDecision:
    status: str
    reason_codes: tuple[str, ...]


def evaluate_r1a_runtime_admission_bytes(
    data: bytes,
    *,
    source_readback: R1aRuntimeSourceReadback,
) -> R1aRuntimeAdmissionDecision:
    """Derive the runtime decision from exact submitted and Git-owned bytes."""
    document = _parse_json_object(data, "R1a runtime admission evidence")
    top = _require_mapping(document, _TOP_FIELDS)
    if top["schema_version"] != _ADMISSION_SCHEMA:
        _violate("invalid R1a runtime admission schema")
    authorization = _parse_authorization(top["authorization"])
    g1_b = _parse_g1_b(top["g1_b_plan"])
    g1_a = _parse_g1_a(top["g1_a"])
    v5_plan = _parse_v5_plan(top["v5_plan_only_input"])
    compass = _parse_compass(top["compass_input"])
    v5_executor = _parse_v5_executor(top["v5_executor_input"])
    protocol = _parse_protocol(top["protocol"])
    submitted_decision = _parse_decision(top["decision"])

    _verify_sources(
        source_readback,
        authorization=authorization,
        g1_b=g1_b,
        g1_a=g1_a,
        v5_plan=v5_plan,
        compass=compass,
        v5_executor=v5_executor,
        protocol=protocol,
    )
    blockers = (
        {"v5_executor_owner_input_missing"}
        if v5_executor["proposal_status"] == "missing"
        else set()
    )
    status = "blocked" if blockers else "admitted_for_local_r1a_synthetic_repair"
    reasons = tuple(sorted(blockers))
    if submitted_decision != (status, reasons):
        _violate("decision does not match source-derived admission")
    return R1aRuntimeAdmissionDecision(status=status, reason_codes=reasons)


def _parse_authorization(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _AUTHORIZATION_FIELDS)
    if document["allowed_action"] != "none":
        _violate("runtime authorization self-declared")
    for field in _AUTHORIZATION_FIELDS - {"allowed_action"}:
        if document[field] is not False:
            _violate("runtime authorization widened")
    return document


def _parse_g1_b(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _G1_B_FIELDS)
    expected = {
        "commit": _G1_B_COMMIT,
        "design_path": _DESIGN_PATH,
        "design_sha256": _DESIGN_SHA256,
        "implementation_plan_path": _PLAN_PATH,
        "implementation_plan_sha256": _PLAN_SHA256,
    }
    if document != expected:
        _violate("fixed G1-B plan binding changed")
    return document


def _parse_g1_a(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _G1_A_FIELDS)
    expected = {
        "commit": _G1_A_COMMIT,
        "evidence_git_blob_sha256": _G1_A_GIT_BLOB_SHA256,
        "evidence_path": _G1_A_PATH,
        "legacy_windows_worktree_sha256": _G1_A_LEGACY_WINDOWS_SHA256,
        "status": "ready_for_r1a_plan",
    }
    if document != expected:
        _violate("fixed G1-A binding changed")
    return document


def _parse_v5_plan(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _V5_PLAN_FIELDS)
    expected = {
        "allowed_action": "draft_r1a_implementation_plan",
        "authority_commit": _V5_AUTHORITY,
        "authorization_path": _V5_PLAN_PATH,
        "authorization_sha256": _V5_PLAN_SHA256,
        "proposal_commit": _V5_PLAN_PROPOSAL,
        "runtime_authorized": False,
    }
    if document != expected:
        _violate("V5 plan-only input changed or was reused")
    return document


def _parse_compass(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _COMPASS_FIELDS)
    expected = {
        "authority_commit": _COMPASS_AUTHORITY,
        "capsule_path": _COMPASS_PATH,
        "capsule_sha256": _COMPASS_SHA256,
        "proposal_commit": _COMPASS_PROPOSAL,
        "runtime_authorized": False,
    }
    if document != expected:
        _violate("fixed Compass binding changed")
    return document


def _parse_v5_executor(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _V5_EXECUTOR_FIELDS)
    if (
        document["authority_commit"] != _V5_EXECUTOR_AUTHORITY
        or document["contract_path"] != _V5_EXECUTOR_PATH
        or document["owner"] != "v5"
        or document["runtime_authorized"] is not False
    ):
        _violate("invalid V5 executor owner binding")
    status = document["proposal_status"]
    if status == "missing":
        if (
            document["proposal_commit"] is not None
            or document["contract_sha256"] is not None
            or document["test_status"] != "not_run"
        ):
            _violate("missing V5 executor input claimed evidence")
    elif status == "submitted":
        _require_sha1(document["proposal_commit"])
        _require_sha256(document["contract_sha256"])
        if (
            document["proposal_commit"] != _V5_EXECUTOR_PROPOSAL
            or document["contract_sha256"] != _V5_EXECUTOR_SHA256
            or document["test_status"] != "pass"
        ):
            _violate("invalid V5 executor owner binding")
    else:
        _violate("invalid V5 executor proposal status")
    return document


def _parse_protocol(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _PROTOCOL_FIELDS)
    expected = {
        "conformance_vector_path": _PROTOCOL_VECTOR_PATH,
        "conformance_vector_sha256": _PROTOCOL_VECTOR_SHA256,
        "conformance_vector_set_version": _PROTOCOL_VECTOR_SET_VERSION,
        "contract_version": PROTOCOL_CONTRACT_VERSION,
        "execution_evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "execution_evidence_vector_path": _EVIDENCE_VECTOR_PATH,
        "execution_evidence_vector_set_version": EVIDENCE_VECTOR_SET_VERSION,
        "execution_evidence_vector_sha256": EVIDENCE_VECTOR_SHA256,
    }
    if document != expected:
        _violate("protocol binding changed")
    return document


def _parse_decision(value: object) -> tuple[str, tuple[str, ...]]:
    document = _require_mapping(value, _DECISION_FIELDS)
    status = document["status"]
    if not isinstance(status, str) or status not in {
        "blocked",
        "admitted_for_local_r1a_synthetic_repair",
    }:
        _violate("invalid runtime admission status")
    reasons = document["reason_codes"]
    if not isinstance(reasons, list) or any(
        not isinstance(reason, str) for reason in reasons
    ):
        _violate("invalid runtime admission reason codes")
    if len(reasons) != len(set(reasons)) or reasons != sorted(reasons):
        _violate("noncanonical runtime admission reason codes")
    return status, tuple(reasons)


def _verify_sources(
    source: R1aRuntimeSourceReadback,
    *,
    authorization: Mapping[str, object],
    g1_b: Mapping[str, object],
    g1_a: Mapping[str, object],
    v5_plan: Mapping[str, object],
    compass: Mapping[str, object],
    v5_executor: Mapping[str, object],
    protocol: Mapping[str, object],
) -> None:
    del authorization, protocol
    source.require_commit("platform", _G1_A_COMMIT)
    source.require_commit("platform", _G1_B_COMMIT)
    source.require_ancestor("platform", _G1_A_COMMIT, _G1_B_COMMIT)
    _read_matching(
        source, "platform", _G1_B_COMMIT, _DESIGN_PATH, g1_b["design_sha256"]
    )
    _read_matching(
        source,
        "platform",
        _G1_B_COMMIT,
        _PLAN_PATH,
        g1_b["implementation_plan_sha256"],
    )
    g1_a_bytes = _read_matching(
        source,
        "platform",
        _G1_A_COMMIT,
        _G1_A_PATH,
        g1_a["evidence_git_blob_sha256"],
    )
    _validate_g1_a_bytes(g1_a_bytes, g1_a["legacy_windows_worktree_sha256"])

    source.require_commit("v5", _V5_AUTHORITY)
    source.require_commit("v5", _V5_PLAN_PROPOSAL)
    source.require_ancestor("v5", _V5_AUTHORITY, _V5_PLAN_PROPOSAL)
    _read_matching(
        source,
        "v5",
        _V5_PLAN_PROPOSAL,
        _V5_PLAN_PATH,
        v5_plan["authorization_sha256"],
    )

    source.require_commit("compass", _COMPASS_AUTHORITY)
    source.require_commit("compass", _COMPASS_PROPOSAL)
    source.require_ancestor("compass", _COMPASS_AUTHORITY, _COMPASS_PROPOSAL)
    compass_bytes = _read_matching(
        source,
        "compass",
        _COMPASS_PROPOSAL,
        _COMPASS_PATH,
        compass["capsule_sha256"],
    )
    _validate_compass_bytes(compass_bytes)

    if v5_executor["proposal_status"] == "missing":
        source.require_file_absent("v5", _V5_EXECUTOR_AUTHORITY, _V5_EXECUTOR_PATH)
        return
    proposal = _string(v5_executor["proposal_commit"])
    source.require_commit("v5", _V5_EXECUTOR_AUTHORITY)
    source.require_commit("v5", proposal)
    source.require_ancestor("v5", _V5_EXECUTOR_AUTHORITY, proposal)
    contract = _read_matching(
        source,
        "v5",
        proposal,
        _V5_EXECUTOR_PATH,
        v5_executor["contract_sha256"],
    )
    _validate_executor_contract(contract)


def _validate_g1_a_bytes(data: bytes, legacy_windows_sha256: object) -> None:
    _require_sha256(legacy_windows_sha256)
    if b"\r" in data:
        _violate("G1-A Git blob is not canonical LF")
    windows_bytes = data.replace(b"\n", b"\r\n")
    if hashlib.sha256(windows_bytes).hexdigest() != legacy_windows_sha256:
        _violate("G1-A legacy Windows hash provenance does not match")
    document = _parse_json_object(data, "G1-A evidence")
    authorization = document.get("authorization")
    decision = document.get("decision")
    if (
        document.get("schema_version") != "m1-r1a-plan-admission-v2"
        or not isinstance(authorization, Mapping)
        or authorization.get("runtime_authorized") is not False
        or authorization.get("allowed_action") != "draft_r1a_implementation_plan"
        or not isinstance(decision, Mapping)
        or decision.get("status") != "ready_for_r1a_plan"
        or decision.get("reason_codes") != []
    ):
        _violate("G1-A evidence is not ready-for-plan only")


def _validate_compass_bytes(data: bytes) -> None:
    document = _parse_json_object(data, "Compass capsule")
    policy = document.get("access_policy")
    if not isinstance(policy, Mapping) or frozenset(policy) != frozenset(
        {"drift_write", "ingest", "model", "network", "recall", "source_write", "tool"}
    ):
        _violate("Compass capability boundary changed")
    if any(value is not False for value in policy.values()):
        _violate("Compass capability boundary widened")
    if (
        document.get("capsule_version") != "m1-r1a-grounding-capsule-v1"
        or document.get("synthetic_scope") != "no_business_data"
    ):
        _violate("Compass capsule binding changed")


def _validate_executor_contract(data: bytes) -> None:
    document = _require_mapping(
        _parse_json_object(data, "V5 executor owner contract"),
        _OWNER_CONTRACT_FIELDS,
    )
    if (
        document["schema_version"] != _V5_EXECUTOR_SCHEMA
        or document["owner"] != "v5"
        or document["authority_commit"] != _V5_EXECUTOR_AUTHORITY
        or document["test_status"] != "pass"
        or document["capabilities"] != ["synthetic_code_repair_v1"]
    ):
        _violate("invalid V5 executor owner contract")
    authorization = _require_mapping(
        document["authorization"], _OWNER_AUTHORIZATION_FIELDS
    )
    if any(value is not False for value in authorization.values()):
        _violate("V5 executor authority widened")
    executor = _require_mapping(document["executor"], _OWNER_EXECUTOR_FIELDS)
    if executor != {
        "identity_id": "exec_r1a_synthetic_01",
        "key_id": "key_r1a_ephemeral_v3",
        "public_key_policy": "ephemeral-process-generated-v1",
        "release": "rel_r1a_ephemeral_v3",
        "signature_algorithm": ED25519_V1,
    }:
        _violate("invalid V5 executor binding")
    bindings = _require_mapping(document["bindings"], _OWNER_BINDING_FIELDS)
    if bindings != {
        "announcement_version": "m1-r1a-ephemeral-signer-announcement-v3",
        "artifact_sha256": (
            "ca32fce8c78684df61d5fdf4e8a101615181ab39978d3c29683b37492c2ef21e"
        ),
        "bound_capsule_sha256": _COMPASS_SHA256,
        "capability": "synthetic_code_repair_v1",
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "execution_request_version": "m1-r1a-ephemeral-sign-request-v3",
        "execution_result_version": "m1-r1a-ephemeral-sign-result-v3",
        "fixture_sha256": (
            "340c7baf9e908ec8349bee450e87671b963f38d52440e743d88e717948724318"
        ),
        "session_protocol_version": "m1-r1a-ephemeral-signer-session-v3",
        "tool_policy_sha256": (
            "8ee996ea414ea5abf87ce88393e817563a94dc5203f5af48ddb133218a4410fb"
        ),
    }:
        _violate("V5 executor uses a noncanonical Platform evidence contract")
    scope_policy = _require_mapping(
        document["scope_evidence_policy"], _OWNER_SCOPE_POLICY_FIELDS
    )
    complete = _require_mapping(scope_policy["complete"], _OWNER_SCOPE_OUTCOME_FIELDS)
    missing_scope = _require_mapping(
        scope_policy["missing_scope"], _OWNER_SCOPE_OUTCOME_FIELDS
    )
    if (
        scope_policy["allowed_modes"] != ["complete", "missing_scope"]
        or complete
        != {
            "result_state": "completed",
            "scope_evidence_ids": [
                "integrity:fixed-patch-sha256",
                "scope:disposable-synthetic-module-only",
            ],
        }
        or missing_scope
        != {
            "result_state": "review_required",
            "scope_evidence_ids": ["integrity:fixed-patch-sha256"],
        }
    ):
        _violate("invalid V5 scope evidence policy")
    session = _require_mapping(document["session"], _OWNER_SESSION_FIELDS)
    if session != {
        "challenge_authority": "platform",
        "entrypoint": "python-module:nautilus_v5_ephemeral_signer",
        "import_policy": "isolated-v5-owner-modules-only-v1",
        "max_announce_challenges": 1,
        "max_challenge_ttl_seconds": 120,
        "max_execution_requests": 1,
        "private_key_lifetime": "single_process_session",
        "state_machine": ["new", "announced", "consumed"],
        "transport": "local-stdin-stdout-jsonl-v1",
    }:
        _violate("invalid V5 ephemeral signer session boundary")


def _read_matching(
    source: R1aRuntimeSourceReadback,
    owner: str,
    commit: str,
    path: str,
    expected: object,
) -> bytes:
    _require_sha256(expected)
    data = source.read_file(owner, commit, path)
    if hashlib.sha256(data).hexdigest() != expected:
        _violate("source blob hash does not match")
    return data


def _parse_json_object(data: bytes, label: str) -> Mapping[str, object]:
    def reject_duplicates(pairs: list[tuple[str, object]]) -> dict[str, object]:
        result: dict[str, object] = {}
        for key, value in pairs:
            if key in result:
                _violate(f"{label} contains duplicate fields")
            result[key] = value
        return result

    try:
        value = json.loads(data.decode("utf-8"), object_pairs_hook=reject_duplicates)
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        _violate(f"{label} is not valid UTF-8 JSON")
    if not isinstance(value, Mapping):
        _violate(f"{label} is not a JSON object")
    return value


def _require_mapping(value: object, fields: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != fields:
        _violate("unexpected R1a runtime admission fields")
    return value


def _require_sha1(value: object) -> None:
    if not isinstance(value, str) or _SHA1_RE.fullmatch(value) is None:
        _violate("invalid full Git SHA")


def _require_sha256(value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate("invalid SHA-256")


def _string(value: object) -> str:
    if not isinstance(value, str):
        _violate("invalid source readback value")
    return value


def _violate(message: str) -> None:
    raise AdmissionViolation(message)
