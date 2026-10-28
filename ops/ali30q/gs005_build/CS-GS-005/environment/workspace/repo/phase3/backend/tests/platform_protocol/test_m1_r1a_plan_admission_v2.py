"""Tests for the G1-A planning-only constitutional gate."""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from platform_protocol.m1_r1a_admission import AdmissionViolation
from platform_protocol.m1_r1a_plan_admission_v2 import (
    evaluate_plan_only_admission_bytes_v2,
    evaluate_plan_only_admission_v2,
)

_PLATFORM_SHA = "2a2b91534fbfc9af9a8c3cadd1ae1da9552c0535"
_ADJUDICATOR_SHA = "286ff5535aa089ebdcda7f1bf80a814f21c58a7d"
_TASK6_SHA = "caf00fa7d1ac68d7e26adfa28317c58af88460c1"
_HISTORICAL_V5_SHA = "a651b5e96f0bcb5fcaaa490e20da5db7b5456bd7"
_HISTORICAL_COMPASS_SHA = "d719db1e6f735cdd2fe99ab9ec997f5c8ea3e6fd"
_V5_AUTHORITY_SHA = "f560be28ecac550e754eff2b82e36ea91ecad0b6"
_V5_PROPOSAL_SHA = "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94"
_COMPASS_AUTHORITY_SHA = "37efc4fc2f7455202c94515b29314af9e5e2e16e"
_COMPASS_PROPOSAL_SHA = "2" * 40
_CURRENT_COMPASS_PROPOSAL_SHA = "e87234bbdc072bd10e9b88079c21f7c574361506"
_CURRENT_COMPASS_CAPSULE_SHA256 = (
    "1387d4d12edddbe2a8b83e54160ac864760d33d8b9372010976df1279a5f53d0"
)
_TASK6_PATH = "docs/plans/2026-08-03-platform-protocol-v2-adapter-review-template.md"
_O1_PATH = "docs/evidence/m1/o1_acceptance.json"
_V5_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_COMPASS_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"
_EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "evidence"
    / "m1-r1a-plan-admission-v2.json"
)


def _json_bytes(value: object) -> bytes:
    return (json.dumps(value, indent=2) + "\n").encode()


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _v5_waiver() -> dict[str, object]:
    return {
        "authorization_version": "v5-r1a-plan-only-authorization-v1",
        "decision": "owner_static_plan_only_waiver",
        "authority_commit": _V5_AUTHORITY_SHA,
        "authority": {
            "repository": "nautilus-v5",
            "authority_clone_path": "C:\\Users\\chunx\\nautilus-v5",
            "authority_ref": "session/agent-self-improve-20260526",
            "path": _V5_PATH,
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
                    "condition": (
                        "accepted_claim_requires_integrity_and_scope_evidence"
                    ),
                    "defect_code": "missing_scope_evidence",
                    "missing_scope_outcome": "review_required",
                    "rule_id": "gr_scope_evidence_required_v1",
                }
            ],
        },
        "source_authority": "nautilus-compass",
        "synthetic_scope": "no_business_data",
    }


def _o1_evidence() -> dict[str, object]:
    return {
        "admission": {
            "compass_revision": _HISTORICAL_COMPASS_SHA,
            "v5_revision": _HISTORICAL_V5_SHA,
        },
        "schema_version": "nautilus.m1.o1.acceptance-evidence.v1",
        "status": "accepted",
        "task6_revision": _TASK6_SHA,
    }


class _SourceReadback:
    def __init__(self) -> None:
        self.commits = {
            ("platform", _PLATFORM_SHA),
            ("platform", _ADJUDICATOR_SHA),
            ("platform", _TASK6_SHA),
            ("v5", _V5_AUTHORITY_SHA),
            ("v5", _V5_PROPOSAL_SHA),
            ("compass", _COMPASS_AUTHORITY_SHA),
            ("compass", _COMPASS_PROPOSAL_SHA),
        }
        self.ancestry = {
            ("platform", _TASK6_SHA, _PLATFORM_SHA),
            ("v5", _V5_AUTHORITY_SHA, _V5_PROPOSAL_SHA),
            ("compass", _COMPASS_AUTHORITY_SHA, _COMPASS_PROPOSAL_SHA),
        }
        self.files = {
            ("platform", _ADJUDICATOR_SHA, _TASK6_PATH): b"task6-template\n",
            ("platform", _PLATFORM_SHA, _O1_PATH): _json_bytes(_o1_evidence()),
            ("v5", _V5_PROPOSAL_SHA, _V5_PATH): _json_bytes(_v5_waiver()),
            ("compass", _COMPASS_PROPOSAL_SHA, _COMPASS_PATH): _json_bytes(
                _compass_capsule()
            ),
        }
        self.reads: list[tuple[str, str, str]] = []
        self.absence_checks: list[tuple[str, str, str]] = []

    def require_commit(self, owner: str, commit: str) -> None:
        if (owner, commit) not in self.commits:
            raise AdmissionViolation("commit does not resolve")

    def require_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        if (owner, ancestor, descendant) not in self.ancestry:
            raise AdmissionViolation("ancestry requirement failed")

    def require_file_absent(self, owner: str, commit: str, path: str) -> None:
        self.absence_checks.append((owner, commit, path))
        if (owner, commit, path) in self.files:
            raise AdmissionViolation("fixed path unexpectedly exists")

    def read_file(self, owner: str, commit: str, path: str) -> bytes:
        self.reads.append((owner, commit, path))
        try:
            return self.files[(owner, commit, path)]
        except KeyError as error:
            raise AdmissionViolation("fixed path does not resolve") from error


def _owner_input(
    owner: str,
    authority_commit: str,
    proposal_commit: str | None,
    *,
    status: str = "submitted",
) -> dict[str, object]:
    return {
        "authority_commit": authority_commit,
        "owner": owner,
        "proposal_commit": proposal_commit,
        "proposal_status": status,
        "runtime_authorized": False,
        "schema_version": "m1-r1a-owner-input-v1",
        "test_status": "pass" if status != "missing" else "not_run",
    }


def _ready_document(source: _SourceReadback) -> dict[str, object]:
    task6_bytes = source.files[("platform", _ADJUDICATOR_SHA, _TASK6_PATH)]
    o1_bytes = source.files[("platform", _PLATFORM_SHA, _O1_PATH)]
    v5_bytes = source.files[("v5", _V5_PROPOSAL_SHA, _V5_PATH)]
    compass_bytes = source.files[("compass", _COMPASS_PROPOSAL_SHA, _COMPASS_PATH)]
    return {
        "adjudicator": {
            "task6_template_commit": _ADJUDICATOR_SHA,
            "task6_template_sha256": _sha256(task6_bytes),
            "template_role": "reference_only",
        },
        "authorization": {
            "allowed_action": "draft_r1a_implementation_plan",
            "business_workflow_authorized": False,
            "database_authorized": False,
            "deployment_authorized": False,
            "fde_authorized": False,
            "model_authorized": False,
            "network_authorized": False,
            "owner_repository_write_authorized": False,
            "runtime_authorized": False,
        },
        "compass_plan_input": {
            **_owner_input("compass", _COMPASS_AUTHORITY_SHA, _COMPASS_PROPOSAL_SHA),
            "capsule_path": _COMPASS_PATH,
            "capsule_sha256": _sha256(compass_bytes),
        },
        "decision": {"reason_codes": [], "status": "ready_for_r1a_plan"},
        "historical_o1": {
            "candidate_commit": _PLATFORM_SHA,
            "compass_revision": _HISTORICAL_COMPASS_SHA,
            "evidence_path": _O1_PATH,
            "evidence_sha256": _sha256(o1_bytes),
            "role": "historical_capability_provenance",
            "schema_version": "m1-r1a-historical-o1-provenance-v1",
            "task6_commit": _TASK6_SHA,
            "v5_revision": _HISTORICAL_V5_SHA,
        },
        "schema_version": "m1-r1a-plan-admission-v2",
        "v5_plan_input": {
            **_owner_input("v5", _V5_AUTHORITY_SHA, _V5_PROPOSAL_SHA),
            "authorization_path": _V5_PATH,
            "authorization_sha256": _sha256(v5_bytes),
        },
    }


def _evaluate(document: dict[str, object], source: _SourceReadback | None = None):
    return evaluate_plan_only_admission_v2(
        document,
        source_readback=source or _SourceReadback(),
    )


def test_ready_requires_historical_provenance_and_current_owner_blobs() -> None:
    source = _SourceReadback()
    document = _ready_document(source)

    decision = _evaluate(document, source)

    assert decision.status == "ready_for_r1a_plan"
    assert decision.reason_codes == ()
    assert source.reads == [
        ("platform", _ADJUDICATOR_SHA, _TASK6_PATH),
        ("platform", _PLATFORM_SHA, _O1_PATH),
        ("v5", _V5_PROPOSAL_SHA, _V5_PATH),
        ("compass", _COMPASS_PROPOSAL_SHA, _COMPASS_PATH),
    ]
    assert (
        document["historical_o1"]["v5_revision"]
        != document["v5_plan_input"]["proposal_commit"]
    )


def test_missing_compass_is_the_only_current_blocker() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    document["compass_plan_input"] = {
        **_owner_input("compass", _COMPASS_AUTHORITY_SHA, None, status="missing"),
        "capsule_path": None,
        "capsule_sha256": None,
    }
    document["decision"] = {
        "reason_codes": ["compass_owner_input_missing"],
        "status": "blocked",
    }

    decision = _evaluate(document, source)

    assert decision.reason_codes == ("compass_owner_input_missing",)
    assert source.absence_checks == [("compass", _COMPASS_AUTHORITY_SHA, _COMPASS_PATH)]


def test_self_declared_ready_cannot_override_missing_compass() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    document["compass_plan_input"] = {
        **_owner_input("compass", _COMPASS_AUTHORITY_SHA, None, status="missing"),
        "capsule_path": None,
        "capsule_sha256": None,
    }

    with pytest.raises(AdmissionViolation, match="decision does not match"):
        _evaluate(document, source)


def test_matching_hash_cannot_hide_v5_runtime_widening() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    waiver = _v5_waiver()
    waiver["runtime_authorized"] = True
    changed = _json_bytes(waiver)
    source.files[("v5", _V5_PROPOSAL_SHA, _V5_PATH)] = changed
    document["v5_plan_input"]["authorization_sha256"] = _sha256(changed)

    with pytest.raises(AdmissionViolation, match="fixed V5 input"):
        _evaluate(document, source)


def test_matching_hash_cannot_hide_compass_capability_widening() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    capsule = _compass_capsule()
    capsule["access_policy"]["recall"] = True
    changed = _json_bytes(capsule)
    source.files[("compass", _COMPASS_PROPOSAL_SHA, _COMPASS_PATH)] = changed
    document["compass_plan_input"]["capsule_sha256"] = _sha256(changed)

    with pytest.raises(AdmissionViolation, match="Compass capsule"):
        _evaluate(document, source)


def test_compass_input_ref_cannot_equal_capsule_hash_by_contract() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    capsule = _compass_capsule()
    capsule["attempt_binding"]["input_ref_equals_capsule_hash"] = True
    changed = _json_bytes(capsule)
    source.files[("compass", _COMPASS_PROPOSAL_SHA, _COMPASS_PATH)] = changed
    document["compass_plan_input"]["capsule_sha256"] = _sha256(changed)

    with pytest.raises(AdmissionViolation, match="Compass capsule"):
        _evaluate(document, source)


@pytest.mark.parametrize(
    "mutate",
    [
        lambda document: document.update({"extra": True}),
        lambda document: document["authorization"].update({"runtime_authorized": True}),
        lambda document: document["authorization"].update(
            {"allowed_action": "execute_r1a_runtime"}
        ),
        lambda document: document["historical_o1"].update(
            {"role": "current_runtime_evidence"}
        ),
        lambda document: document["v5_plan_input"].update(
            {"authorization_path": "docs/contracts/other.json"}
        ),
        lambda document: document["compass_plan_input"].update(
            {"capsule_path": "docs/contracts/other.json"}
        ),
        lambda document: document["decision"].update({"extra": True}),
    ],
)
def test_unknown_fields_or_authority_widening_fail_closed(mutate) -> None:
    source = _SourceReadback()
    document = copy.deepcopy(_ready_document(source))
    mutate(document)

    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)


def test_wrong_commit_ancestry_or_hash_fails_closed() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    document["v5_plan_input"]["proposal_commit"] = "9" * 40
    with pytest.raises(AdmissionViolation):
        _evaluate(document, source)

    source = _SourceReadback()
    source.ancestry.remove(("v5", _V5_AUTHORITY_SHA, _V5_PROPOSAL_SHA))
    with pytest.raises(AdmissionViolation):
        _evaluate(_ready_document(source), source)

    source = _SourceReadback()
    document = _ready_document(source)
    document["historical_o1"]["evidence_sha256"] = "0" * 64
    with pytest.raises(AdmissionViolation, match="hash"):
        _evaluate(document, source)


def test_fixed_v5_input_cannot_be_replaced_by_a_matching_waiver() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    other_authority = "3" * 40
    other_proposal = "4" * 40
    waiver = _v5_waiver()
    waiver["authority_commit"] = other_authority
    changed = _json_bytes(waiver)
    source.commits.update({("v5", other_authority), ("v5", other_proposal)})
    source.ancestry.add(("v5", other_authority, other_proposal))
    source.files[("v5", other_proposal, _V5_PATH)] = changed
    document["v5_plan_input"].update(
        {
            "authority_commit": other_authority,
            "proposal_commit": other_proposal,
            "authorization_sha256": _sha256(changed),
        }
    )

    with pytest.raises(AdmissionViolation, match="fixed V5 input"):
        _evaluate(document, source)


def test_task6_adjudicator_commit_cannot_be_substituted() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    other_commit = "5" * 40
    other_bytes = b"other-task6-template\n"
    source.commits.add(("platform", other_commit))
    source.files[("platform", other_commit, _TASK6_PATH)] = other_bytes
    document["adjudicator"].update(
        {
            "task6_template_commit": other_commit,
            "task6_template_sha256": _sha256(other_bytes),
        }
    )

    with pytest.raises(AdmissionViolation, match="fixed adjudicator"):
        _evaluate(document, source)


def test_historical_o1_provenance_cannot_be_substituted() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    other_candidate = "6" * 40
    other_bytes = _json_bytes(_o1_evidence())
    source.commits.add(("platform", other_candidate))
    source.ancestry.add(("platform", _TASK6_SHA, other_candidate))
    source.files[("platform", other_candidate, _O1_PATH)] = other_bytes
    document["historical_o1"].update(
        {
            "candidate_commit": other_candidate,
            "evidence_sha256": _sha256(other_bytes),
        }
    )

    with pytest.raises(AdmissionViolation, match="fixed historical O1"):
        _evaluate(document, source)


def test_compass_authority_baseline_cannot_be_self_declared() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    substituted_authority = "7" * 40
    substituted_proposal = "8" * 40
    compass_input = document["compass_plan_input"]
    compass_input["authority_commit"] = substituted_authority
    compass_input["proposal_commit"] = substituted_proposal
    source.commits.update(
        {
            ("compass", substituted_authority),
            ("compass", substituted_proposal),
        }
    )
    source.ancestry.add(("compass", substituted_authority, substituted_proposal))
    source.files[("compass", substituted_proposal, _COMPASS_PATH)] = _json_bytes(
        _compass_capsule()
    )

    with pytest.raises(AdmissionViolation, match="fixed Compass authority"):
        _evaluate(document, source)


def test_serialized_admission_rejects_duplicate_json_fields() -> None:
    source = _SourceReadback()
    serialized = _json_bytes(_ready_document(source))
    duplicated = serialized.replace(
        b'    "runtime_authorized": false\n',
        b'    "runtime_authorized": true,\n    "runtime_authorized": false\n',
        1,
    )

    with pytest.raises(AdmissionViolation, match="duplicate fields"):
        evaluate_plan_only_admission_bytes_v2(
            duplicated,
            source_readback=source,
        )


def test_incomplete_or_noncanonical_blockers_fail_closed() -> None:
    source = _SourceReadback()
    document = _ready_document(source)
    document["v5_plan_input"] = {
        **_owner_input("v5", _V5_AUTHORITY_SHA, _V5_PROPOSAL_SHA, status="pending"),
        "authorization_path": None,
        "authorization_sha256": None,
    }
    document["compass_plan_input"] = {
        **_owner_input("compass", _COMPASS_AUTHORITY_SHA, None, status="missing"),
        "capsule_path": None,
        "capsule_sha256": None,
    }
    document["decision"] = {
        "reason_codes": [
            "v5_plan_input_pending",
            "compass_owner_input_missing",
        ],
        "status": "blocked",
    }

    with pytest.raises(AdmissionViolation, match="decision does not match"):
        _evaluate(document, source)


def test_current_evidence_is_ready_after_compass_owner_submission() -> None:
    evidence_bytes = _EVIDENCE_PATH.read_bytes()
    document = json.loads(evidence_bytes)
    assert document["v5_plan_input"] == {
        "authority_commit": "f560be28ecac550e754eff2b82e36ea91ecad0b6",
        "authorization_path": _V5_PATH,
        "authorization_sha256": (
            "9aebc513029150af81068b13d0e454aedc7cad67bcc9d46348e7ba6de101aec6"
        ),
        "owner": "v5",
        "proposal_commit": "cdd55315f03c145e7d83d5a0eddbfeeb5d951c94",
        "proposal_status": "submitted",
        "runtime_authorized": False,
        "schema_version": "m1-r1a-owner-input-v1",
        "test_status": "pass",
    }
    assert document["compass_plan_input"] == {
        "authority_commit": _COMPASS_AUTHORITY_SHA,
        "capsule_path": _COMPASS_PATH,
        "capsule_sha256": _CURRENT_COMPASS_CAPSULE_SHA256,
        "owner": "compass",
        "proposal_commit": _CURRENT_COMPASS_PROPOSAL_SHA,
        "proposal_status": "submitted",
        "runtime_authorized": False,
        "schema_version": "m1-r1a-owner-input-v1",
        "test_status": "pass",
    }

    source = _SourceReadback()
    evaluated = copy.deepcopy(document)
    synthetic_sources = _ready_document(source)
    evaluated["adjudicator"] = synthetic_sources["adjudicator"]
    evaluated["historical_o1"] = synthetic_sources["historical_o1"]
    evaluated["v5_plan_input"] = synthetic_sources["v5_plan_input"]
    source.commits.add(("compass", _CURRENT_COMPASS_PROPOSAL_SHA))
    source.ancestry.add(
        ("compass", _COMPASS_AUTHORITY_SHA, _CURRENT_COMPASS_PROPOSAL_SHA)
    )
    source.files[("compass", _CURRENT_COMPASS_PROPOSAL_SHA, _COMPASS_PATH)] = (
        _json_bytes(_compass_capsule())
    )

    decision = evaluate_plan_only_admission_bytes_v2(
        _json_bytes(evaluated),
        source_readback=source,
    )

    assert document["authorization"]["runtime_authorized"] is False
    assert decision.status == "ready_for_r1a_plan"
    assert decision.reason_codes == ()
