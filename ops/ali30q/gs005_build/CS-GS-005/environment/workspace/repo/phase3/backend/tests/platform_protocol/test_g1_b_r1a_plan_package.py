from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

_REPOSITORY_ROOT = Path(__file__).parents[4]
_ATTRIBUTES_PATH = _REPOSITORY_ROOT / ".gitattributes"
_DESIGN_PATH = (
    _REPOSITORY_ROOT / "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-design.md"
)
_PLAN_PATH = (
    _REPOSITORY_ROOT
    / "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-implementation-plan.md"
)
_PACKAGE_PATH = (
    _REPOSITORY_ROOT / "phase3/backend/docs/evidence/g1-b-r1a-plan-package-v1.json"
)

_PLATFORM_BASELINE = "21a36fd2cfc8a2223454d1f7c5bc542045910291"
_G1_A_EVIDENCE_SHA256 = (
    "f96c61157a977ad30f6299d5c4cbc01b0f965033511464a349bb7f4fd3127bea"
)
_V5_AUTHORITY = "f560be28ecac550e754eff2b82e36ea91ecad0b6"
_V5_PROPOSAL = "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94"
_V5_SHA256 = "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
_COMPASS_AUTHORITY = "37efc4fc2f7455202c94515b29314af9e5e2e16e"
_COMPASS_PROPOSAL = "e87234bbdc072bd10e9b88079c21f7c574361506"
_COMPASS_SHA256 = "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"

_TOP_FIELDS = {
    "authorization",
    "documents",
    "owner_inputs",
    "platform",
    "review",
    "schema_version",
    "scope",
}
_AUTHORIZATION_FIELDS = {
    "allowed_action",
    "business_workflow_authorized",
    "database_authorized",
    "deployment_authorized",
    "dogfood_authorized",
    "fde_authorized",
    "merge_authorized",
    "model_authorized",
    "network_authorized",
    "push_authorized",
    "runtime_authorized",
    "self_modify_authorized",
    "tool_execution_authorized",
}
_OPERATION_CHAIN = [
    "request",
    "dmas_unique_candidate_selection",
    "platform_envelope_acceptance",
    "attempt_claim",
    "attempt_scoped_input_binding",
    "compass_grounding",
    "candidate_patch",
    "executor_signed_execution_evidence",
    "manifest",
    "manifest_read_grant",
    "independent_synthetic_test",
    "independent_receipt",
    "platform_readback",
]


def test_g1_b_plan_package_files_exist() -> None:
    assert _ATTRIBUTES_PATH.is_file()
    assert _DESIGN_PATH.is_file()
    assert _PLAN_PATH.is_file()
    assert _PACKAGE_PATH.is_file()


def test_plan_package_files_are_checkout_stable() -> None:
    assert set(_ATTRIBUTES_PATH.read_text(encoding="utf-8").splitlines()) == {
        "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-design.md text eol=lf",
        (
            "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-implementation-plan.md "
            "text eol=lf"
        ),
        ("phase3/backend/docs/evidence/g1-b-r1a-plan-package-v1.json text eol=lf"),
    }


def _reject_duplicate_pairs(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def _load_package() -> dict[str, object]:
    loaded = json.loads(
        _PACKAGE_PATH.read_bytes(),
        object_pairs_hook=_reject_duplicate_pairs,
    )
    assert isinstance(loaded, dict)
    return loaded


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _require_exact_fields(value: object, fields: set[str]) -> dict[str, object]:
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("unexpected plan-package fields")
    return value


def _validate_package(document: dict[str, object]) -> None:
    top = _require_exact_fields(document, _TOP_FIELDS)
    if top["schema_version"] != "g1-b-r1a-plan-package-v1":
        raise ValueError("wrong plan-package version")

    platform = _require_exact_fields(
        top["platform"],
        {
            "baseline_commit",
            "g1_a_evidence_path",
            "g1_a_evidence_sha256",
            "g1_a_status",
        },
    )
    expected_platform = {
        "baseline_commit": _PLATFORM_BASELINE,
        "g1_a_evidence_path": (
            "phase3/backend/docs/evidence/m1-r1a-plan-admission-v2.json"
        ),
        "g1_a_evidence_sha256": _G1_A_EVIDENCE_SHA256,
        "g1_a_status": "ready_for_r1a_plan",
    }
    if platform != expected_platform:
        raise ValueError("wrong Platform planning authority")

    owner_inputs = _require_exact_fields(top["owner_inputs"], {"compass", "v5"})
    v5 = _require_exact_fields(
        owner_inputs["v5"],
        {"authority_commit", "path", "proposal_commit", "role", "sha256"},
    )
    compass = _require_exact_fields(
        owner_inputs["compass"],
        {"authority_commit", "path", "proposal_commit", "role", "sha256"},
    )
    if v5 != {
        "authority_commit": _V5_AUTHORITY,
        "path": "docs/contracts/v5-r1a-plan-only-authorization-v1.json",
        "proposal_commit": _V5_PROPOSAL,
        "role": "action_owner_plan_input",
        "sha256": _V5_SHA256,
    }:
        raise ValueError("wrong V5 owner input")
    if compass != {
        "authority_commit": _COMPASS_AUTHORITY,
        "path": "docs/contracts/m1-r1a-grounding-capsule-v1.json",
        "proposal_commit": _COMPASS_PROPOSAL,
        "role": "read_only_learning_boundary",
        "sha256": _COMPASS_SHA256,
    }:
        raise ValueError("wrong Compass owner input")

    authorization = _require_exact_fields(top["authorization"], _AUTHORIZATION_FIELDS)
    if authorization["allowed_action"] != "draft_r1a_implementation_plan":
        raise ValueError("plan authority widened")
    for field in _AUTHORIZATION_FIELDS - {"allowed_action"}:
        if authorization[field] is not False:
            raise ValueError("plan authority widened")

    scope = _require_exact_fields(
        top["scope"],
        {
            "data_class",
            "dmas_role",
            "evidence_level",
            "operation_chain",
            "task_count",
            "task_id",
        },
    )
    if scope != {
        "data_class": "synthetic_no_business_data",
        "dmas_role": "platform_pure_unique_candidate_selection",
        "evidence_level": "plan_only",
        "operation_chain": _OPERATION_CHAIN,
        "task_count": 1,
        "task_id": "synthetic_code_repair_v1",
    }:
        raise ValueError("G1-B scope widened")

    documents = _require_exact_fields(
        top["documents"], {"design", "implementation_plan"}
    )
    for name in ("design", "implementation_plan"):
        _require_exact_fields(documents[name], {"path", "sha256"})

    review = _require_exact_fields(
        top["review"],
        {
            "allowed_responses",
            "fourth_coordinator_authorized",
            "owner_reviewers",
            "platform_decision_owner",
            "required_conflict_evidence",
            "required_findings",
        },
    )
    if review != {
        "allowed_responses": ["ACK", "CONFLICT"],
        "fourth_coordinator_authorized": False,
        "owner_reviewers": ["v5", "compass"],
        "platform_decision_owner": "nautilus-core-platform",
        "required_conflict_evidence": [
            "full_commit",
            "path",
            "test_command",
            "test_result",
        ],
        "required_findings": {"high": 0, "medium": 0},
    }:
        raise ValueError("review topology widened")


def test_plan_package_has_exact_authority_scope_and_review_topology() -> None:
    _validate_package(_load_package())


def test_plan_documents_are_byte_bound_and_cover_the_required_chain() -> None:
    package = _load_package()
    documents = package["documents"]
    assert isinstance(documents, dict)
    assert documents["design"] == {
        "path": "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-design.md",
        "sha256": _sha256(_DESIGN_PATH),
    }
    assert documents["implementation_plan"] == {
        "path": "docs/plans/2026-08-09-g1-b-r1a-synthetic-repair-implementation-plan.md",
        "sha256": _sha256(_PLAN_PATH),
    }

    design = _DESIGN_PATH.read_text(encoding="utf-8")
    for heading in (
        "## Outcome",
        "## Fixed authority inputs",
        "## Single synthetic task",
        "## Owner boundaries",
        "## Data flow",
        "## Failure matrix",
        "## Rollback",
        "## Stop conditions",
    ):
        assert heading in design
    for token in (
        "OperationRequestV2",
        "OperationEnvelopeV2",
        "ExecutionAttemptV2",
        "ManifestV2",
        "IndependentReceiptV2",
        "record_attempt",
        "input_ref_hash",
        "review_required",
    ):
        assert token in design
    assert "Claude Code" not in design

    plan = _PLAN_PATH.read_text(encoding="utf-8")
    assert plan.startswith("# G1-B R1a Synthetic Repair Implementation Plan\n")
    assert "> **For Codex:** REQUIRED SUB-SKILL:" in plan
    assert "**Goal:**" in plan
    assert "**Architecture:**" in plan
    assert "**Tech Stack:**" in plan
    assert "No runtime task is authorized by this commit." in plan
    assert "Do not execute Task 1" in plan
    assert "Claude Code" not in plan
    for task in range(1, 8):
        assert f"### Task {task}:" in plan


def test_plan_closes_action_authentication_and_atomic_claim_gaps() -> None:
    package = _load_package()
    assert package["scope"]["operation_chain"] == _OPERATION_CHAIN

    design = _DESIGN_PATH.read_text(encoding="utf-8")
    for token in (
        "ExecutorExecutionEvidenceV1",
        "canonical_signing_bytes",
        "executor_signature",
        "record_execution_evidence_and_manifest",
        "ProtocolRepository.transition",
        "attempt_claim_conflict",
        "two independent PostgreSQL sessions",
    ):
        assert token in design
    normalized_design = " ".join(design.split())
    assert (
        "exactly the plan-allowlisted `protocol_executor_evidence` migration and table"
        in normalized_design
    )
    assert "no migration, production service" not in design

    plan = _PLAN_PATH.read_text(encoding="utf-8")
    for token in (
        "m1_r1a_execution_evidence.py",
        "protocol_executor_evidence",
        "record_execution_evidence_and_manifest",
        "executor_evidence_forged",
        "attempt_claim_conflict",
        "two independent PostgreSQL sessions",
    ):
        assert token in plan
    normalized_plan = " ".join(plan.split())
    assert "no unplanned dependency, migration, or table" in normalized_plan
    assert "exactly the single forward migration" in normalized_plan
    assert "no new dependency/migration/table" not in plan


@pytest.mark.parametrize(
    "mutate",
    [
        lambda value: value.update({"extra": True}),
        lambda value: value["authorization"].update({"runtime_authorized": True}),
        lambda value: value["scope"].update({"task_count": 3}),
        lambda value: value["scope"].update({"evidence_level": "runtime"}),
        lambda value: value["owner_inputs"]["v5"].update({"sha256": "0" * 64}),
        lambda value: value["review"].update({"fourth_coordinator_authorized": True}),
    ],
)
def test_plan_package_mutations_fail_closed(mutate) -> None:
    document = copy.deepcopy(_load_package())
    mutate(document)
    with pytest.raises(ValueError):
        _validate_package(document)
