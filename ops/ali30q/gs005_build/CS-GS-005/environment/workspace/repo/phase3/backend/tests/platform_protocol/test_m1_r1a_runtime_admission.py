"""Fail-closed source admission for the bounded R1a synthetic runtime."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from platform_protocol.m1_r1a_admission import AdmissionViolation
from platform_protocol.m1_r1a_execution_evidence import (
    EVIDENCE_VECTOR_SET_VERSION,
    EVIDENCE_VECTOR_SHA256,
)
from platform_protocol.m1_r1a_runtime_admission import (
    evaluate_r1a_runtime_admission_bytes,
)

_G1_B_COMMIT = "082725c46c2a476390f28fa8fb223966e6af09d3"
_G1_A_COMMIT = "21a36fd2cfc8a2223454d1f7c5bc542045910291"
_V5_AUTHORITY = "f560be28ecac550e754eff2b82e36ea91ecad0b6"
_V5_PLAN_PROPOSAL = "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94"
_V5_EXECUTOR_AUTHORITY = "4c18c5a70c16d1d6797f9b71ff96aa58e5a41a67"
_V5_EXECUTOR_PROPOSAL = "f3d94d32fce6316e84628c63754468ba608a1595"
_V5_EXECUTOR_SHA256 = "dbd18532f30f58a6e59355f3584d609026bda839f49d31e017eeb27b38a4dc29"
_COMPASS_AUTHORITY = "37efc4fc2f7455202c94515b29314af9e5e2e16e"
_COMPASS_PROPOSAL = "e87234bbdc072bd10e9b88079c21f7c574361506"

_DESIGN_PATH = "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-design.md"
_PLAN_PATH = "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-implementation-plan.md"
_G1_A_PATH = "phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json"
_V5_PLAN_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_V5_EXECUTOR_PATH = "docs/contracts/m1-r1a-ephemeral-signer-v3.json"
_COMPASS_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"

_BACKEND = Path(__file__).resolve().parents[2]
_REPOSITORY = _BACKEND.parents[1]
_EVIDENCE_PATH = _BACKEND / "docs" / "evidence" / "m1-r1a-runtime-admission-v1.json"


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def _canonical_json_bytes(value: object) -> bytes:
    return (json.dumps(value, separators=(",", ":"), sort_keys=True) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _compass_capsule() -> dict[str, object]:
    return {
        "access_policy": {
            "drift_write": False,
            "ingest": False,
            "model": False,
            "network": False,
            "recall": False,
            "source_write": False,
            "tool": False,
        },
        "admission": {
            "eligible_workload": "m1-r1a-plan-only-v1",
            "owner_repository": "nautilus-compass",
            "owner_revision_binding": "platform_admission_requires_full_commit",
            "platform_contract_version": "protocol-v2-contracts-v1",
            "proposal_version": "m1-r1a-grounding-owner-proposal-v1",
        },
        "attempt_binding": {
            "binding_field": "execution_attempt.input_ref_hash",
            "binding_version": "m1-attempt-input-hmac-v1",
            "capsule_hash_role": "bound_capsule_hash",
            "derivation_owner": "nautilus-core-platform",
            "input_ref_equals_capsule_hash": False,
        },
        "capsule_id": "cap_m1quality_grounding_v1",
        "capsule_version": "m1-r1a-grounding-capsule-v1",
        "rule_set": {
            "rule_set_version": "m1-quality-grounding-rules-v1",
            "rules": [
                {
                    "condition": "accepted_claim_requires_integrity_and_scope_evidence",
                    "defect_code": "missing_scope_evidence",
                    "missing_scope_outcome": "review_required",
                    "rule_id": "gr_scope_evidence_required_v1",
                }
            ],
        },
        "source_authority": "nautilus-compass",
        "synthetic_scope": "no_business_data",
    }


def _v5_plan_waiver() -> dict[str, object]:
    return {
        "authorization_version": "v5-r1a-plan-only-authorization-v1",
        "decision": "owner_static_plan_only_waiver",
        "authority_commit": _V5_AUTHORITY,
        "authority": {
            "repository": "nautilus-v5",
            "authority_clone_path": "C:\\Users\\chunx\\nautilus-v5",
            "authority_ref": "session/agent-self-improve-20260526",
            "path": _V5_PLAN_PATH,
            "consumption_rule": (
                "platform_binds_authorization_path_and_sha256_to_submitted_"
                "proposal_commit"
            ),
        },
        "provenance": {
            "authority_basis": "platform_designated_authority_clone_clean_head",
            "proposal_binding": "platform_consumer_only",
        },
        "runtime_authorized": False,
        "exemption": {
            "allowed_actions": ["draft_r1a_implementation_plan"],
            "prohibited_actions": [
                "r1a_runtime_implementation",
                "model_calls",
                "tool_execution",
                "network",
                "cloud",
                "docker",
                "runtime_file_writes",
                "database",
                "deployment",
                "code_merge",
                "fde",
            ],
        },
        "boundary": {
            "compass_changes_authorized": False,
            "external_worktree_is_authority": False,
            "platform_changes_authorized": False,
        },
    }


def _executor_contract() -> dict[str, object]:
    return {
        "authorization": {
            "database_authorized": False,
            "environment_key_authorized": False,
            "general_rpc_authorized": False,
            "model_authorized": False,
            "network_authorized": False,
            "private_key_persistence_authorized": False,
            "self_modify_authorized": False,
            "shell_authorized": False,
            "source_write_authorized": False,
            "tool_gateway_authorized": False,
        },
        "authority_commit": _V5_EXECUTOR_AUTHORITY,
        "bindings": {
            "announcement_version": "m1-r1a-ephemeral-signer-announcement-v3",
            "artifact_sha256": (
                "ca32fce8c78684df61d5fdf4e8a101615181ab39978d3c29683b37492c2ef21e"
            ),
            "bound_capsule_sha256": (
                "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
            ),
            "capability": "synthetic_code_repair_v1",
            "evidence_contract_version": "m1-r1a-executor-execution-evidence-v1",
            "execution_request_version": "m1-r1a-ephemeral-sign-request-v3",
            "execution_result_version": "m1-r1a-ephemeral-sign-result-v3",
            "fixture_sha256": (
                "340c7baf9e908ec8349bee450e87671b963f38d52440e743d88e717948724318"
            ),
            "session_protocol_version": "m1-r1a-ephemeral-signer-session-v3",
            "tool_policy_sha256": (
                "8ee996ea414ea5abf87ce88393e817563a94dc5203f5af48ddb133218a4410fb"
            ),
        },
        "capabilities": ["synthetic_code_repair_v1"],
        "executor": {
            "identity_id": "exec_r1a_synthetic_01",
            "key_id": "key_r1a_ephemeral_v3",
            "public_key_policy": "ephemeral-process-generated-v1",
            "release": "rel_r1a_ephemeral_v3",
            "signature_algorithm": "ed25519-v1",
        },
        "owner": "v5",
        "schema_version": "m1-r1a-v5-ephemeral-signer-owner-input-v3",
        "scope_evidence_policy": {
            "allowed_modes": ["complete", "missing_scope"],
            "complete": {
                "result_state": "completed",
                "scope_evidence_ids": [
                    "integrity:fixed-patch-sha256",
                    "scope:disposable-synthetic-module-only",
                ],
            },
            "missing_scope": {
                "result_state": "review_required",
                "scope_evidence_ids": ["integrity:fixed-patch-sha256"],
            },
        },
        "session": {
            "challenge_authority": "platform",
            "entrypoint": "python-module:nautilus_v5_ephemeral_signer",
            "import_policy": "isolated-v5-owner-modules-only-v1",
            "max_announce_challenges": 1,
            "max_challenge_ttl_seconds": 120,
            "max_execution_requests": 1,
            "private_key_lifetime": "single_process_session",
            "state_machine": ["new", "announced", "consumed"],
            "transport": "local-stdin-stdout-jsonl-v1",
        },
        "test_status": "pass",
    }


class _SourceReadback:
    def __init__(self) -> None:
        design = (_REPOSITORY / _DESIGN_PATH).read_bytes()
        plan = (_REPOSITORY / _PLAN_PATH).read_bytes()
        g1_a = (_REPOSITORY / _G1_A_PATH).read_bytes().replace(b"\r\n", b"\n")
        compass = _json_bytes(_compass_capsule())
        v5_plan = _json_bytes(_v5_plan_waiver())
        self.commits = {
            ("platform", _G1_A_COMMIT),
            ("platform", _G1_B_COMMIT),
            ("v5", _V5_AUTHORITY),
            ("v5", _V5_PLAN_PROPOSAL),
            ("v5", _V5_EXECUTOR_AUTHORITY),
            ("v5", _V5_EXECUTOR_PROPOSAL),
            ("compass", _COMPASS_AUTHORITY),
            ("compass", _COMPASS_PROPOSAL),
        }
        self.ancestry = {
            ("platform", _G1_A_COMMIT, _G1_B_COMMIT),
            ("v5", _V5_AUTHORITY, _V5_PLAN_PROPOSAL),
            ("v5", _V5_EXECUTOR_AUTHORITY, _V5_EXECUTOR_PROPOSAL),
            ("compass", _COMPASS_AUTHORITY, _COMPASS_PROPOSAL),
        }
        self.files = {
            ("platform", _G1_B_COMMIT, _DESIGN_PATH): design,
            ("platform", _G1_B_COMMIT, _PLAN_PATH): plan,
            ("platform", _G1_A_COMMIT, _G1_A_PATH): g1_a,
            ("v5", _V5_PLAN_PROPOSAL, _V5_PLAN_PATH): v5_plan,
            (
                "v5",
                _V5_EXECUTOR_PROPOSAL,
                _V5_EXECUTOR_PATH,
            ): _canonical_json_bytes(_executor_contract()),
            ("compass", _COMPASS_PROPOSAL, _COMPASS_PATH): compass,
        }
        self.absence_checks: list[tuple[str, str, str]] = []

    def require_commit(self, owner: str, commit: str) -> None:
        if (owner, commit) not in self.commits:
            raise AdmissionViolation("commit does not resolve")

    def require_ancestor(self, owner: str, ancestor: str, descendant: str) -> None:
        if (owner, ancestor, descendant) not in self.ancestry:
            raise AdmissionViolation("ancestry requirement failed")

    def require_file_absent(self, owner: str, commit: str, path: str) -> None:
        self.absence_checks.append((owner, commit, path))
        if (owner, commit, path) in self.files:
            raise AdmissionViolation("fixed path unexpectedly exists")

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        try:
            return self.files[(owner, commit, path)]
        except KeyError as error:
            raise AdmissionViolation("fixed path does not resolve") from error


def _document(source: _SourceReadback) -> dict[str, object]:
    design = source.files[("platform", _G1_B_COMMIT, _DESIGN_PATH)]
    plan = source.files[("platform", _G1_B_COMMIT, _PLAN_PATH)]
    g1_a = source.files[("platform", _G1_A_COMMIT, _G1_A_PATH)]
    compass = source.files[("compass", _COMPASS_PROPOSAL, _COMPASS_PATH)]
    return {
        "authorization": {
            "allowed_action": "none",
            "database_authorized": False,
            "deployment_authorized": False,
            "fde_authorized": False,
            "model_authorized": False,
            "network_authorized": False,
            "production_authorized": False,
            "runtime_authorized": False,
            "tool_execution_authorized": False,
        },
        "compass_input": {
            "authority_commit": _COMPASS_AUTHORITY,
            "capsule_path": _COMPASS_PATH,
            "capsule_sha256": _sha256(compass),
            "proposal_commit": _COMPASS_PROPOSAL,
            "runtime_authorized": False,
        },
        "decision": {
            "reason_codes": [],
            "status": "admitted_for_local_r1a_synthetic_repair",
        },
        "g1_a": {
            "commit": _G1_A_COMMIT,
            "evidence_path": _G1_A_PATH,
            "evidence_git_blob_sha256": _sha256(g1_a),
            "legacy_windows_worktree_sha256": (
                "f96c61157a977ad30f6299d5c4cbc01b0f965033511464a349bb7f4fd3127bea"
            ),
            "status": "ready_for_r1a_plan",
        },
        "g1_b_plan": {
            "commit": _G1_B_COMMIT,
            "design_path": _DESIGN_PATH,
            "design_sha256": _sha256(design),
            "implementation_plan_path": _PLAN_PATH,
            "implementation_plan_sha256": _sha256(plan),
        },
        "protocol": {
            "conformance_vector_path": "platform_protocol/conformance_vectors_v2.json",
            "contract_version": "protocol-v2-contracts-v1",
            "conformance_vector_sha256": (
                "d3aa6361ab3152ff3a14e1887a5ed3b8ceac532c2f1392eea1ca3312e9f6fe29"
            ),
            "conformance_vector_set_version": "protocol-v2-conformance-v1",
            "execution_evidence_contract_version": (
                "m1-r1a-executor-execution-evidence-v1"
            ),
            "execution_evidence_vector_path": (
                "platform_protocol/m1_r1a_execution_evidence_vectors_v1.json"
            ),
            "execution_evidence_vector_set_version": EVIDENCE_VECTOR_SET_VERSION,
            "execution_evidence_vector_sha256": EVIDENCE_VECTOR_SHA256,
        },
        "schema_version": "m1-r1a-runtime-admission-v1",
        "v5_executor_input": {
            "authority_commit": _V5_EXECUTOR_AUTHORITY,
            "contract_path": _V5_EXECUTOR_PATH,
            "contract_sha256": _V5_EXECUTOR_SHA256,
            "owner": "v5",
            "proposal_commit": _V5_EXECUTOR_PROPOSAL,
            "proposal_status": "submitted",
            "runtime_authorized": False,
            "test_status": "pass",
        },
        "v5_plan_only_input": {
            "allowed_action": "draft_r1a_implementation_plan",
            "authority_commit": _V5_AUTHORITY,
            "authorization_path": _V5_PLAN_PATH,
            "authorization_sha256": (
                "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
            ),
            "proposal_commit": _V5_PLAN_PROPOSAL,
            "runtime_authorized": False,
        },
    }


def _evaluate(document: dict[str, object], source: _SourceReadback):
    return evaluate_r1a_runtime_admission_bytes(
        _json_bytes(document), source_readback=source
    )


def test_current_evidence_admits_only_the_exact_v5_executor_owner_input() -> None:
    source = _SourceReadback()

    decision = _evaluate(_document(source), source)

    assert decision.status == "admitted_for_local_r1a_synthetic_repair"
    assert decision.reason_codes == ()
    assert source.absence_checks == []


def test_committed_evidence_is_the_exact_current_admitted_document() -> None:
    source = _SourceReadback()
    committed = json.loads(_EVIDENCE_PATH.read_bytes())

    assert committed == _document(source)
    decision = evaluate_r1a_runtime_admission_bytes(
        _EVIDENCE_PATH.read_bytes(), source_readback=source
    )
    assert decision.status == "admitted_for_local_r1a_synthetic_repair"
    assert decision.reason_codes == ()


def test_owner_input_is_admitted_only_after_exact_blob_readback() -> None:
    source = _SourceReadback()
    contract = _canonical_json_bytes(_executor_contract())
    document = _document(source)

    assert _sha256(contract) == _V5_EXECUTOR_SHA256

    decision = _evaluate(document, source)

    assert decision.status == "admitted_for_local_r1a_synthetic_repair"
    assert decision.reason_codes == ()


def test_different_v5_descendant_is_rejected_even_with_identical_contract() -> None:
    source = _SourceReadback()
    other_proposal = "a" * 40
    source.commits.add(("v5", other_proposal))
    source.ancestry.add(("v5", _V5_EXECUTOR_AUTHORITY, other_proposal))
    source.files[("v5", other_proposal, _V5_EXECUTOR_PATH)] = _canonical_json_bytes(
        _executor_contract()
    )
    document = _document(source)
    document["v5_executor_input"]["proposal_commit"] = other_proposal

    with pytest.raises(AdmissionViolation, match="V5 executor owner binding"):
        _evaluate(document, source)


def test_owner_input_rejects_public_key_material_in_source_contract() -> None:
    source = _SourceReadback()
    owner_contract = _executor_contract()
    owner_contract["executor"]["public_key_material"] = (
        "ed25519-v1:YNhJwLbsCxvXFfj8TD8IrsD5zsTsAE2A3c0MB9D860w"
    )
    contract = _canonical_json_bytes(owner_contract)
    source.files[("v5", _V5_EXECUTOR_PROPOSAL, _V5_EXECUTOR_PATH)] = contract
    document = _document(source)
    document["v5_executor_input"]["contract_sha256"] = _sha256(contract)

    with pytest.raises(AdmissionViolation, match="V5 executor owner binding"):
        _evaluate(document, source)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("entrypoint", "python-module:nautilus_v5.m1_r1a_ephemeral_signer"),
        ("import_policy", "eager-nautilus-v5-package"),
        ("max_challenge_ttl_seconds", 121),
        ("max_execution_requests", 2),
    ],
)
def test_owner_input_rejects_changed_session_boundary(
    field: str, value: object
) -> None:
    source = _SourceReadback()
    owner_contract = _executor_contract()
    owner_contract["session"][field] = value
    contract = _canonical_json_bytes(owner_contract)
    source.files[("v5", _V5_EXECUTOR_PROPOSAL, _V5_EXECUTOR_PATH)] = contract
    document = _document(source)
    document["v5_executor_input"]["contract_sha256"] = _sha256(contract)

    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("allowed_modes",), ["complete"]),
        (("complete", "result_state"), "review_required"),
        (
            ("complete", "scope_evidence_ids"),
            ["integrity:fixed-patch-sha256"],
        ),
        (("missing_scope", "result_state"), "completed"),
        (
            ("missing_scope", "scope_evidence_ids"),
            [
                "integrity:fixed-patch-sha256",
                "scope:disposable-synthetic-module-only",
            ],
        ),
    ],
)
def test_owner_input_rejects_changed_scope_evidence_policy(
    path: tuple[str, ...], value: object
) -> None:
    source = _SourceReadback()
    owner_contract = _executor_contract()
    target = owner_contract["scope_evidence_policy"]
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value
    contract = _canonical_json_bytes(owner_contract)
    source.files[("v5", _V5_EXECUTOR_PROPOSAL, _V5_EXECUTOR_PATH)] = contract
    document = _document(source)
    document["v5_executor_input"]["contract_sha256"] = _sha256(contract)

    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)


def test_duplicate_json_field_fails_before_evaluation() -> None:
    source = _SourceReadback()
    data = _json_bytes(_document(source))
    duplicated = data.replace(
        b'{\n  "authorization"',
        b'{\n  "schema_version": "m1-r1a-runtime-admission-v1",\n  "authorization"',
        1,
    )

    with pytest.raises(AdmissionViolation, match="duplicate"):
        evaluate_r1a_runtime_admission_bytes(duplicated, source_readback=source)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda document: document.update({"extra": True}),
        lambda document: document["g1_b_plan"].update({"commit": "short"}),
        lambda document: document["g1_b_plan"].update(
            {"design_path": "docs/plans/other.md"}
        ),
        lambda document: document["authorization"].update({"model_authorized": True}),
        lambda document: document["authorization"].update({"network_authorized": True}),
        lambda document: document["authorization"].update(
            {"database_authorized": True}
        ),
        lambda document: document["authorization"].update(
            {"production_authorized": True}
        ),
        lambda document: document["authorization"].update({"fde_authorized": True}),
        lambda document: document["decision"].update(
            {"reason_codes": ["v5_executor_owner_input_missing"], "status": "blocked"}
        ),
        lambda document: document["decision"].update({"status": []}),
        lambda document: document["v5_executor_input"].update(
            {
                "contract_path": _V5_PLAN_PATH,
                "contract_sha256": (
                    "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
                ),
                "proposal_commit": _V5_PLAN_PROPOSAL,
                "proposal_status": "submitted",
                "test_status": "pass",
            }
        ),
    ],
)
def test_invalid_or_widened_admission_inputs_fail_closed(mutate) -> None:
    source = _SourceReadback()
    document = copy.deepcopy(_document(source))
    mutate(document)

    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)


def test_changed_source_bytes_and_ancestry_only_submission_fail_closed() -> None:
    source = _SourceReadback()
    document = _document(source)
    source.files[("platform", _G1_B_COMMIT, _DESIGN_PATH)] += b"tampered"

    with pytest.raises(AdmissionViolation, match="hash"):
        _evaluate(document, source)

    source = _SourceReadback()
    document = _document(source)
    del source.files[("v5", _V5_EXECUTOR_PROPOSAL, _V5_EXECUTOR_PATH)]

    with pytest.raises(AdmissionViolation, match="does not resolve"):
        _evaluate(document, source)


def test_changed_compass_capability_fails_even_with_matching_submitted_hash() -> None:
    source = _SourceReadback()
    document = _document(source)
    capsule = _compass_capsule()
    capsule["access_policy"]["model"] = True
    changed = _json_bytes(capsule)
    source.files[("compass", _COMPASS_PROPOSAL, _COMPASS_PATH)] = changed
    document["compass_input"]["capsule_sha256"] = _sha256(changed)

    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)
