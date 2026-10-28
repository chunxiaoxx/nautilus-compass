"""G1-A planning-only admission derived from immutable owner evidence."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Protocol

from platform_protocol.m1_r1a_admission import (
    AdmissionViolation,
    LocalGitSourceReadback,
    SourceReadback,
)

_ADMISSION_SCHEMA = "m1-r1a-plan-admission-v2"
_HISTORICAL_O1_SCHEMA = "m1-r1a-historical-o1-provenance-v1"
_OWNER_INPUT_SCHEMA = "m1-r1a-owner-input-v1"
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_TASK6_PATH = "docs/plans/2026-08-03-platform-protocol-v2-adapter-review-template.md"
_O1_PATH = "docs/evidence/m1/o1_acceptance.json"
_V5_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_COMPASS_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"
_FIXED_ADJUDICATOR_COMMIT = "286ff5535aa089ebdcda7f1bf80a814f21c58a7d"
_FIXED_HISTORICAL_O1 = {
    "candidate_commit": "2a2b91534fbfc9af9a8c3cadd1ae1da9552c0535",
    "compass_revision": "d719db1e6f735cdd2fe99ab9ec997f5c8ea3e6fd",
    "task6_commit": "caf00fa7d1ac68d7e26adfa28317c58af88460c1",
    "v5_revision": "a651b5e96f0bcb5fcaaa490e20da5db7b5456bd7",
}
_FIXED_V5_AUTHORITY = "f560be28ecac550e754eff2b82e36ea91ecad0b6"
_FIXED_V5_PROPOSAL = "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94"
_FIXED_V5_SHA256 = "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
_FIXED_COMPASS_AUTHORITY = "37efc4fc2f7455202c94515b29314af9e5e2e16e"

_TOP_FIELDS = frozenset(
    {
        "adjudicator",
        "authorization",
        "compass_plan_input",
        "decision",
        "historical_o1",
        "schema_version",
        "v5_plan_input",
    }
)
_ADJUDICATOR_FIELDS = frozenset(
    {"task6_template_commit", "task6_template_sha256", "template_role"}
)
_AUTHORIZATION_FIELDS = frozenset(
    {
        "allowed_action",
        "business_workflow_authorized",
        "database_authorized",
        "deployment_authorized",
        "fde_authorized",
        "model_authorized",
        "network_authorized",
        "owner_repository_write_authorized",
        "runtime_authorized",
    }
)
_HISTORICAL_O1_FIELDS = frozenset(
    {
        "candidate_commit",
        "compass_revision",
        "evidence_path",
        "evidence_sha256",
        "role",
        "schema_version",
        "task6_commit",
        "v5_revision",
    }
)
_OWNER_FIELDS = frozenset(
    {
        "authority_commit",
        "owner",
        "proposal_commit",
        "proposal_status",
        "runtime_authorized",
        "schema_version",
        "test_status",
    }
)
_V5_INPUT_FIELDS = _OWNER_FIELDS | frozenset(
    {"authorization_path", "authorization_sha256"}
)
_COMPASS_INPUT_FIELDS = _OWNER_FIELDS | frozenset({"capsule_path", "capsule_sha256"})
_DECISION_FIELDS = frozenset({"reason_codes", "status"})

_V5_WAIVER_FIELDS = frozenset(
    {
        "authorization_version",
        "decision",
        "authority_commit",
        "authority",
        "provenance",
        "runtime_authorized",
        "exemption",
        "boundary",
    }
)
_V5_AUTHORITY_FIELDS = frozenset(
    {
        "repository",
        "authority_clone_path",
        "authority_ref",
        "path",
        "consumption_rule",
    }
)
_V5_PROVENANCE_FIELDS = frozenset({"authority_basis", "proposal_binding"})
_V5_EXEMPTION_FIELDS = frozenset({"allowed_actions", "prohibited_actions"})
_V5_BOUNDARY_FIELDS = frozenset(
    {
        "compass_changes_authorized",
        "external_worktree_is_authority",
        "platform_changes_authorized",
    }
)
_V5_PROHIBITED_ACTIONS = (
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
)

_COMPASS_FIELDS = frozenset(
    {
        "access_policy",
        "admission",
        "attempt_binding",
        "capsule_id",
        "capsule_version",
        "rule_set",
        "source_authority",
        "synthetic_scope",
    }
)
_COMPASS_POLICY_FIELDS = frozenset(
    {"drift_write", "ingest", "model", "network", "recall", "source_write", "tool"}
)
_COMPASS_ADMISSION_FIELDS = frozenset(
    {
        "eligible_workload",
        "owner_repository",
        "owner_revision_binding",
        "platform_contract_version",
        "proposal_version",
    }
)
_COMPASS_BINDING_FIELDS = frozenset(
    {
        "binding_field",
        "binding_version",
        "capsule_hash_role",
        "derivation_owner",
        "input_ref_equals_capsule_hash",
    }
)
_COMPASS_RULE_SET_FIELDS = frozenset({"rule_set_version", "rules"})
_COMPASS_RULE_FIELDS = frozenset(
    {"condition", "defect_code", "missing_scope_outcome", "rule_id"}
)


class ConstitutionalSourceReadback(SourceReadback, Protocol):
    """Read exact owner-controlled bytes without trusting submitted paths."""

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        """Read a fixed Git blob at a verified commit."""


class LocalConstitutionalSourceReadback(LocalGitSourceReadback):
    """Extend the existing local Git authority with exact byte reads."""

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        self.require_commit(owner, commit)
        return self._show_file(owner, commit, path)


@dataclass(frozen=True, slots=True)
class PlanOnlyAdmissionDecisionV2:
    status: str
    reason_codes: tuple[str, ...]


def evaluate_plan_only_admission_bytes_v2(
    data: bytes,
    *,
    source_readback: ConstitutionalSourceReadback,
) -> PlanOnlyAdmissionDecisionV2:
    """Parse serialized evidence without duplicate fields, then evaluate it."""
    document = _parse_json_object(data, "G1-A admission evidence")
    return evaluate_plan_only_admission_v2(
        document,
        source_readback=source_readback,
    )


def evaluate_plan_only_admission_v2(
    document: Mapping[str, object],
    *,
    source_readback: ConstitutionalSourceReadback,
) -> PlanOnlyAdmissionDecisionV2:
    """Return the derived plan-only decision after all source checks pass."""
    top = _require_mapping(document, _TOP_FIELDS)
    if top["schema_version"] != _ADMISSION_SCHEMA:
        _violate("invalid G1-A admission schema")
    adjudicator = _parse_adjudicator(top["adjudicator"])
    authorization = _parse_authorization(top["authorization"])
    historical_o1 = _parse_historical_o1(top["historical_o1"])
    v5_input = _parse_v5_input(top["v5_plan_input"])
    compass_input = _parse_compass_input(top["compass_plan_input"])
    decision = _parse_decision(top["decision"])

    _verify_sources(
        source_readback,
        adjudicator=adjudicator,
        authorization=authorization,
        historical_o1=historical_o1,
        v5_input=v5_input,
        compass_input=compass_input,
    )
    blockers = _derive_blockers(v5_input, compass_input)
    expected_status = "blocked" if blockers else "ready_for_r1a_plan"
    expected_reasons = tuple(sorted(blockers))
    if decision != (expected_status, expected_reasons):
        _violate("decision does not match current owner evidence")
    return PlanOnlyAdmissionDecisionV2(expected_status, expected_reasons)


def _parse_adjudicator(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _ADJUDICATOR_FIELDS)
    _require_sha1(document["task6_template_commit"])
    _require_sha256(document["task6_template_sha256"])
    if document["task6_template_commit"] != _FIXED_ADJUDICATOR_COMMIT:
        _violate("fixed adjudicator commit changed")
    if document["template_role"] != "reference_only":
        _violate("Task 6 template cannot become authority")
    return document


def _parse_authorization(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _AUTHORIZATION_FIELDS)
    if document["allowed_action"] != "draft_r1a_implementation_plan":
        _violate("G1-A allowed action widened")
    for field in _AUTHORIZATION_FIELDS - {"allowed_action"}:
        if document[field] is not False:
            _violate("G1-A authorization widened")
    return document


def _parse_historical_o1(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _HISTORICAL_O1_FIELDS)
    if document["schema_version"] != _HISTORICAL_O1_SCHEMA:
        _violate("invalid historical O1 schema")
    if document["role"] != "historical_capability_provenance":
        _violate("historical O1 role widened")
    if document["evidence_path"] != _O1_PATH:
        _violate("invalid historical O1 path")
    for field in (
        "candidate_commit",
        "compass_revision",
        "task6_commit",
        "v5_revision",
    ):
        _require_sha1(document[field])
        if document[field] != _FIXED_HISTORICAL_O1[field]:
            _violate("fixed historical O1 provenance changed")
    _require_sha256(document["evidence_sha256"])
    return document


def _parse_owner_input(
    value: object,
    *,
    expected_owner: str,
    expected_fields: frozenset[str],
) -> Mapping[str, object]:
    document = _require_mapping(value, expected_fields)
    if document["schema_version"] != _OWNER_INPUT_SCHEMA:
        _violate("invalid owner input schema")
    if document["owner"] != expected_owner:
        _violate("owner input submitted by wrong owner")
    _require_sha1(document["authority_commit"])
    status = document["proposal_status"]
    if status not in {"missing", "pending", "submitted"}:
        _violate("invalid owner proposal status")
    if status == "missing":
        if document["proposal_commit"] is not None:
            _violate("missing owner input claimed a proposal")
        if document["test_status"] != "not_run":
            _violate("missing owner input claimed tests")
    else:
        _require_sha1(document["proposal_commit"])
        if document["test_status"] != "pass":
            _violate("present owner input has no passing tests")
    if document["runtime_authorized"] is not False:
        _violate("owner runtime authorization is prohibited")
    return document


def _parse_v5_input(value: object) -> Mapping[str, object]:
    document = _parse_owner_input(
        value,
        expected_owner="v5",
        expected_fields=_V5_INPUT_FIELDS,
    )
    if document["proposal_status"] == "submitted":
        if document["authorization_path"] != _V5_PATH:
            _violate("invalid V5 authorization path")
        _require_sha256(document["authorization_sha256"])
        if (
            document["authority_commit"] != _FIXED_V5_AUTHORITY
            or document["proposal_commit"] != _FIXED_V5_PROPOSAL
            or document["authorization_sha256"] != _FIXED_V5_SHA256
        ):
            _violate("fixed V5 input changed")
    elif (
        document["authorization_path"] is not None
        or document["authorization_sha256"] is not None
    ):
        _violate("unsubmitted V5 input claimed authorization")
    return document


def _parse_compass_input(value: object) -> Mapping[str, object]:
    document = _parse_owner_input(
        value,
        expected_owner="compass",
        expected_fields=_COMPASS_INPUT_FIELDS,
    )
    if document["authority_commit"] != _FIXED_COMPASS_AUTHORITY:
        _violate("fixed Compass authority changed")
    if document["proposal_status"] == "submitted":
        if document["capsule_path"] != _COMPASS_PATH:
            _violate("invalid Compass capsule path")
        _require_sha256(document["capsule_sha256"])
    elif document["capsule_path"] is not None or document["capsule_sha256"] is not None:
        _violate("unsubmitted Compass input claimed a capsule")
    return document


def _parse_decision(value: object) -> tuple[str, tuple[str, ...]]:
    document = _require_mapping(value, _DECISION_FIELDS)
    if document["status"] not in {"blocked", "ready_for_r1a_plan"}:
        _violate("invalid G1-A decision status")
    reasons = document["reason_codes"]
    if not isinstance(reasons, list) or any(
        not isinstance(item, str) for item in reasons
    ):
        _violate("invalid G1-A reason codes")
    if len(reasons) != len(set(reasons)):
        _violate("duplicate G1-A reason codes")
    return document["status"], tuple(reasons)


def _derive_blockers(
    v5_input: Mapping[str, object],
    compass_input: Mapping[str, object],
) -> set[str]:
    blockers: set[str] = set()
    if v5_input["proposal_status"] == "missing":
        blockers.add("v5_owner_input_missing")
    elif v5_input["proposal_status"] == "pending":
        blockers.add("v5_plan_input_pending")
    if compass_input["proposal_status"] == "missing":
        blockers.add("compass_owner_input_missing")
    elif compass_input["proposal_status"] == "pending":
        blockers.add("compass_plan_input_pending")
    return blockers


def _verify_sources(
    source: ConstitutionalSourceReadback,
    *,
    adjudicator: Mapping[str, object],
    authorization: Mapping[str, object],
    historical_o1: Mapping[str, object],
    v5_input: Mapping[str, object],
    compass_input: Mapping[str, object],
) -> None:
    del authorization
    task6_commit = _string(adjudicator["task6_template_commit"])
    source.require_commit("platform", task6_commit)
    task6_bytes = source.read_file("platform", task6_commit, _TASK6_PATH)
    _require_matching_hash(task6_bytes, adjudicator["task6_template_sha256"])

    candidate = _string(historical_o1["candidate_commit"])
    historical_task6 = _string(historical_o1["task6_commit"])
    source.require_commit("platform", candidate)
    source.require_commit("platform", historical_task6)
    source.require_ancestor("platform", historical_task6, candidate)
    o1_bytes = source.read_file("platform", candidate, _O1_PATH)
    _require_matching_hash(o1_bytes, historical_o1["evidence_sha256"])
    _validate_o1_bytes(o1_bytes, historical_o1)

    _verify_owner_source(source, "v5", v5_input)
    _verify_owner_source(source, "compass", compass_input)


def _verify_owner_source(
    source: ConstitutionalSourceReadback,
    owner: str,
    owner_input: Mapping[str, object],
) -> None:
    authority = _string(owner_input["authority_commit"])
    source.require_commit(owner, authority)
    status = owner_input["proposal_status"]
    if status in {"pending", "submitted"}:
        proposal = _string(owner_input["proposal_commit"])
        source.require_commit(owner, proposal)
        source.require_ancestor(owner, authority, proposal)
    if owner == "v5" and status == "submitted":
        proposal = _string(owner_input["proposal_commit"])
        data = source.read_file(owner, proposal, _V5_PATH)
        _require_matching_hash(data, owner_input["authorization_sha256"])
        _validate_v5_waiver(data, owner_input)
    if owner == "compass":
        if status == "missing":
            source.require_file_absent(owner, authority, _COMPASS_PATH)
        elif status == "submitted":
            proposal = _string(owner_input["proposal_commit"])
            data = source.read_file(owner, proposal, _COMPASS_PATH)
            _require_matching_hash(data, owner_input["capsule_sha256"])
            _validate_compass_capsule(data)


def _validate_o1_bytes(data: bytes, binding: Mapping[str, object]) -> None:
    document = _parse_json_object(data, "historical O1")
    admission = document.get("admission")
    if not isinstance(admission, Mapping):
        _violate("historical O1 admission missing")
    if (
        document.get("schema_version") != "nautilus.m1.o1.acceptance-evidence.v1"
        or document.get("status") != "accepted"
        or document.get("task6_revision") != binding["task6_commit"]
        or admission.get("v5_revision") != binding["v5_revision"]
        or admission.get("compass_revision") != binding["compass_revision"]
    ):
        _violate("historical O1 bindings do not match")


def _validate_v5_waiver(data: bytes, owner_input: Mapping[str, object]) -> None:
    document = _require_mapping(
        _parse_json_object(data, "V5 waiver"), _V5_WAIVER_FIELDS
    )
    authority = _require_mapping(document["authority"], _V5_AUTHORITY_FIELDS)
    provenance = _require_mapping(document["provenance"], _V5_PROVENANCE_FIELDS)
    exemption = _require_mapping(document["exemption"], _V5_EXEMPTION_FIELDS)
    boundary = _require_mapping(document["boundary"], _V5_BOUNDARY_FIELDS)
    valid = (
        document["authorization_version"] == "v5-r1a-plan-only-authorization-v1"
        and document["decision"] == "owner_static_plan_only_waiver"
        and document["authority_commit"] == owner_input["authority_commit"]
        and document["runtime_authorized"] is False
        and authority["repository"] == "nautilus-v5"
        and isinstance(authority["authority_clone_path"], str)
        and authority["authority_ref"] == "session/agent-self-improve-20260526"
        and authority["path"] == _V5_PATH
        and authority["consumption_rule"]
        == "platform_binds_authorization_path_and_sha256_to_submitted_proposal_commit"
        and provenance["authority_basis"]
        == "platform_designated_authority_clone_clean_head"
        and provenance["proposal_binding"] == "platform_consumer_only"
        and exemption["allowed_actions"] == ["draft_r1a_implementation_plan"]
        and exemption["prohibited_actions"] == list(_V5_PROHIBITED_ACTIONS)
        and all(value is False for value in boundary.values())
    )
    if not valid:
        _violate("V5 plan-only waiver widened or malformed")


def _validate_compass_capsule(data: bytes) -> None:
    document = _require_mapping(
        _parse_json_object(data, "Compass capsule"), _COMPASS_FIELDS
    )
    policy = _require_mapping(document["access_policy"], _COMPASS_POLICY_FIELDS)
    admission = _require_mapping(document["admission"], _COMPASS_ADMISSION_FIELDS)
    binding = _require_mapping(document["attempt_binding"], _COMPASS_BINDING_FIELDS)
    rule_set = _require_mapping(document["rule_set"], _COMPASS_RULE_SET_FIELDS)
    rules = rule_set["rules"]
    if not isinstance(rules, list) or len(rules) != 1:
        _violate("Compass capsule rule set is invalid")
    rule = _require_mapping(rules[0], _COMPASS_RULE_FIELDS)
    valid = (
        all(value is False for value in policy.values())
        and admission["eligible_workload"] == "m1-r1a-plan-only-v1"
        and admission["owner_repository"] == "nautilus-compass"
        and admission["owner_revision_binding"]
        == "platform_admission_requires_full_commit"
        and admission["platform_contract_version"] == "protocol-v2-contracts-v1"
        and admission["proposal_version"] == "m1-r1a-grounding-owner-proposal-v1"
        and binding["binding_field"] == "execution_attempt.input_ref_hash"
        and binding["binding_version"] == "m1-attempt-input-hmac-v1"
        and binding["capsule_hash_role"] == "bound_capsule_hash"
        and binding["derivation_owner"] == "nautilus-core-platform"
        and binding["input_ref_equals_capsule_hash"] is False
        and document["capsule_id"] == "cap_m1quality_grounding_v1"
        and document["capsule_version"] == "m1-r1a-grounding-capsule-v1"
        and rule_set["rule_set_version"] == "m1-quality-grounding-rules-v1"
        and rule["condition"] == "accepted_claim_requires_integrity_and_scope_evidence"
        and rule["defect_code"] == "missing_scope_evidence"
        and rule["missing_scope_outcome"] == "review_required"
        and rule["rule_id"] == "gr_scope_evidence_required_v1"
        and document["source_authority"] == "nautilus-compass"
        and document["synthetic_scope"] == "no_business_data"
    )
    if not valid:
        _violate("Compass capsule widened or malformed")


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
    except (UnicodeDecodeError, json.JSONDecodeError):
        _violate(f"{label} is not valid UTF-8 JSON")
    if not isinstance(value, Mapping):
        _violate(f"{label} is not a JSON object")
    return value


def _require_matching_hash(data: bytes, expected: object) -> None:
    _require_sha256(expected)
    if hashlib.sha256(data).hexdigest() != expected:
        _violate("source blob hash does not match")


def _require_mapping(value: object, fields: frozenset[str]) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != fields:
        _violate("unexpected G1-A fields")
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
