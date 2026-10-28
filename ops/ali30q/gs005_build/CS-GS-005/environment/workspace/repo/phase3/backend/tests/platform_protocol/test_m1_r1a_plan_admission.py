"""Fail-closed tests for the M1 R1a cross-owner plan-admission overlay."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from platform_protocol.m1_r1a_admission import (
    AdmissionViolation,
    LocalGitSourceReadback,
    evaluate_plan_admission,
)

_SHA = "a" * 40
_SHA256 = "b" * 64
_CAPSULE_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"
_V5_WAIVER_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_EVIDENCE_PATH = (
    Path(__file__).resolve().parents[2]
    / "docs"
    / "evidence"
    / "m1-r1a-plan-admission-v1.json"
)


class _RejectingSourceReadback:
    def require_commit(self, owner: str, commit: str) -> None:
        raise AdmissionViolation(f"source readback rejected {owner}:{commit}")


class _PermissiveSourceReadback:
    def require_commit(self, owner: str, commit: str) -> None:
        return None

    def require_absent_commit(self, owner: str, commit: str) -> None:
        return None

    def require_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        return None

    def require_not_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        return None

    def require_file_sha256(
        self,
        owner: str,
        commit: str,
        path: str,
        sha256: str,
    ) -> None:
        return None

    def require_file_absent(self, owner: str, commit: str, path: str) -> None:
        return None

    def require_o1_evidence(
        self,
        commit: str,
        task6_commit: str,
        v5_revision: str,
        compass_revision: str,
    ) -> None:
        return None


class _V5WaiverBindingSourceReadback(_PermissiveSourceReadback):
    def __init__(self) -> None:
        self.v5_waiver_checks: list[tuple[str, str, str]] = []

    def require_file_sha256(
        self,
        owner: str,
        commit: str,
        path: str,
        sha256: str,
    ) -> None:
        if owner != "v5":
            return
        self.v5_waiver_checks.append((commit, path, sha256))
        if (commit, path, sha256) != (_SHA, _V5_WAIVER_PATH, _SHA256):
            raise AdmissionViolation("unexpected V5 plan-only waiver binding")


class _RejectingO1SourceReadback(_PermissiveSourceReadback):
    def require_o1_evidence(
        self,
        commit: str,
        task6_commit: str,
        v5_revision: str,
        compass_revision: str,
    ) -> None:
        raise AdmissionViolation("O1 evidence bindings rejected")


def _evaluate(document: dict[str, object]):
    return evaluate_plan_admission(
        document,
        source_readback=_PermissiveSourceReadback(),
    )


def _git(repository: Path, *args: str) -> bytes:
    result = subprocess.run(
        ["git", "-C", str(repository), *args],
        check=False,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr.decode("utf-8", errors="replace")
    return result.stdout


def _git_repository(tmp_path: Path) -> tuple[Path, str, str]:
    repository = tmp_path / "authority"
    repository.mkdir()
    _git(repository, "init", "--quiet")
    _git(repository, "config", "user.email", "test@example.invalid")
    _git(repository, "config", "user.name", "M1 R1a Test")
    (repository / "pinned.txt").write_bytes(b"pinned-source-bytes\n")
    _git(repository, "add", "pinned.txt")
    _git(repository, "commit", "--quiet", "-m", "initial")
    parent = _git(repository, "rev-parse", "HEAD").decode("ascii").strip()
    (repository / "child.txt").write_bytes(b"child\n")
    _git(repository, "add", "child.txt")
    _git(repository, "commit", "--quiet", "-m", "child")
    child = _git(repository, "rev-parse", "HEAD").decode("ascii").strip()
    return repository, parent, child


def test_local_git_source_readback_uses_commit_and_blob_bytes(tmp_path: Path) -> None:
    repository, parent, child = _git_repository(tmp_path)
    source_readback = LocalGitSourceReadback(
        platform=repository,
        v5=repository,
        compass=repository,
    )
    digest = hashlib.sha256(b"pinned-source-bytes\n").hexdigest()

    source_readback.require_commit("platform", parent)
    source_readback.require_ancestor("v5", parent, child)
    source_readback.require_not_ancestor("compass", child, parent)
    source_readback.require_file_sha256("platform", parent, "pinned.txt", digest)
    source_readback.require_file_absent("compass", child, "absent.txt")
    source_readback.require_absent_commit("v5", "0" * 40)

    with pytest.raises(AdmissionViolation):
        source_readback.require_file_sha256("platform", parent, "pinned.txt", "0" * 64)


def _owner_input(owner: str, *, status: str = "submitted") -> dict[str, object]:
    return {
        "authority_commit": _SHA,
        "owner": owner,
        "proposal_commit": _SHA,
        "proposal_status": status,
        "runtime_authorized": False,
        "schema_version": "m1-r1a-owner-input-v1",
        "test_status": "pass",
    }


def _ready_document() -> dict[str, object]:
    return {
        "adjudicator": {
            "task6_template_commit": _SHA,
            "task6_template_sha256": _SHA256,
            "template_role": "reference_only",
        },
        "decision": {
            "reason_codes": [],
            "status": "ready_for_r1a_plan",
        },
        "platform_o1": {
            "candidate_commit": _SHA,
            "compass_revision_status": "current_owner_pinned",
            "compass_o1_revision": _SHA,
            "o1_evidence_sha256": _SHA256,
            "schema_version": "m1-r1a-platform-o1-candidate-v1",
            "task6_commit": _SHA,
            "v5_o1_revision": _SHA,
            "v5_revision_status": "current_owner_pinned",
            "verification_status": "reverified_candidate",
        },
        "schema_version": "m1-r1a-plan-admission-v1",
        "v5_g0": {
            **_owner_input("v5"),
            "authorization_path": _V5_WAIVER_PATH,
            "authorization_sha256": _SHA256,
        },
        "compass_capsule": {
            **_owner_input("compass"),
            "capsule_hash": _SHA256,
            "capsule_path": _CAPSULE_PATH,
            "runtime_capabilities": {
                "drift_write": False,
                "ingest": False,
                "model": False,
                "network": False,
                "recall": False,
                "source_write": False,
                "tool": False,
            },
        },
    }


def _blocked_current_document() -> dict[str, object]:
    document = _ready_document()
    document["decision"] = {
        "reason_codes": [
            "compass_o1_revision_noncanonical",
            "compass_owner_input_missing",
            "platform_o1_historical_candidate",
            "v5_g0_pending",
            "v5_o1_revision_unresolvable",
        ],
        "status": "blocked",
    }
    document["platform_o1"] = {
        **document["platform_o1"],
        "compass_revision_status": "noncanonical",
        "v5_revision_status": "unresolvable",
        "verification_status": "historical_candidate",
    }
    document["v5_g0"] = {
        **_owner_input("v5", status="pending"),
    }
    document["compass_capsule"] = {
        **document["compass_capsule"],
        "capsule_hash": None,
        "capsule_path": None,
        "proposal_commit": None,
        "proposal_status": "missing",
        "runtime_capabilities": {},
        "test_status": "not_run",
    }
    return document


def test_ready_decision_requires_three_current_owner_inputs() -> None:
    decision = evaluate_plan_admission(
        _ready_document(),
        source_readback=_PermissiveSourceReadback(),
    )

    assert decision.status == "ready_for_r1a_plan"
    assert decision.reason_codes == ()


def test_submitted_v5_plan_only_waiver_is_bound_to_exact_blob() -> None:
    document = _ready_document()
    document["v5_g0"] = {
        **_owner_input("v5"),
        "authorization_path": _V5_WAIVER_PATH,
        "authorization_sha256": _SHA256,
    }
    source_readback = _V5WaiverBindingSourceReadback()

    decision = evaluate_plan_admission(document, source_readback=source_readback)

    assert decision.status == "ready_for_r1a_plan"
    assert source_readback.v5_waiver_checks == [(_SHA, _V5_WAIVER_PATH, _SHA256)]

    document["v5_g0"] = {
        **document["v5_g0"],
        "authorization_sha256": "c" * 64,
    }
    with pytest.raises(
        AdmissionViolation, match="unexpected V5 plan-only waiver binding"
    ):
        evaluate_plan_admission(document, source_readback=source_readback)


def test_submitted_v5_input_without_plan_only_waiver_binding_is_rejected() -> None:
    document = _ready_document()
    document["v5_g0"] = _owner_input("v5")

    with pytest.raises(AdmissionViolation, match="submitted V5 input requires waiver"):
        evaluate_plan_admission(
            document,
            source_readback=_PermissiveSourceReadback(),
        )


def test_admission_checks_source_readback_before_returning_ready() -> None:
    with pytest.raises(AdmissionViolation, match="source readback rejected"):
        evaluate_plan_admission(
            _ready_document(),
            source_readback=_RejectingSourceReadback(),
        )


def test_admission_checks_o1_evidence_bindings_before_returning_ready() -> None:
    with pytest.raises(AdmissionViolation, match="O1 evidence bindings rejected"):
        evaluate_plan_admission(
            _ready_document(),
            source_readback=_RejectingO1SourceReadback(),
        )


def test_ready_o1_requires_the_current_task6_adjudicator_commit() -> None:
    document = _ready_document()
    document["platform_o1"]["task6_commit"] = "c" * 40

    with pytest.raises(AdmissionViolation, match="current Task 6 adjudicator"):
        _evaluate(document)


def test_historical_o1_cannot_become_ready() -> None:
    document = _ready_document()
    document["platform_o1"]["verification_status"] = "historical_candidate"
    document["decision"] = {
        "reason_codes": ["platform_o1_historical_candidate"],
        "status": "blocked",
    }

    decision = evaluate_plan_admission(
        document,
        source_readback=_PermissiveSourceReadback(),
    )

    assert decision.status == "blocked"
    assert decision.reason_codes == ("platform_o1_historical_candidate",)


def test_current_candidate_evidence_returns_exact_blockers() -> None:
    decision = _evaluate(_blocked_current_document())

    assert decision.status == "blocked"
    assert decision.reason_codes == (
        "compass_o1_revision_noncanonical",
        "compass_owner_input_missing",
        "platform_o1_historical_candidate",
        "v5_g0_pending",
        "v5_o1_revision_unresolvable",
    )


def test_current_source_readback_evidence_is_exactly_blocked() -> None:
    document = json.loads(_EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert document["v5_g0"] == {
        "authority_commit": "f560be28ecac550e754eff2b82e36ea91ecad0b6",
        "authorization_path": _V5_WAIVER_PATH,
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

    decision = _evaluate(document)

    assert decision.status == "blocked"
    assert decision.reason_codes == (
        "compass_o1_revision_noncanonical",
        "compass_owner_input_missing",
        "platform_o1_historical_candidate",
        "v5_o1_revision_unresolvable",
    )


def test_pending_compass_capsule_cannot_become_ready() -> None:
    document = _ready_document()
    document["compass_capsule"]["proposal_status"] = "pending"
    document["platform_o1"]["compass_revision_status"] = "noncanonical"
    document["decision"] = {
        "reason_codes": [
            "compass_capsule_pending",
            "compass_o1_revision_noncanonical",
        ],
        "status": "blocked",
    }

    decision = _evaluate(document)

    assert decision.status == "blocked"
    assert decision.reason_codes == (
        "compass_capsule_pending",
        "compass_o1_revision_noncanonical",
    )


@pytest.mark.parametrize(
    "mutate",
    [
        lambda document: document["v5_g0"].update({"runtime_authorized": True}),
        lambda document: document["compass_capsule"]["runtime_capabilities"].update(
            {"recall": True}
        ),
        lambda document: document["decision"].update({"status": "approved"}),
        lambda document: document.update({"runtime_authorized": True}),
        lambda document: document["v5_g0"].update({"unexpected": "authority"}),
    ],
)
def test_admission_rejects_runtime_widening_or_unknown_authority(
    mutate,
) -> None:
    document = copy.deepcopy(_ready_document())
    mutate(document)

    with pytest.raises(AdmissionViolation):
        _evaluate(document)


def test_blocked_decision_rejects_incomplete_reason_inventory() -> None:
    document = _blocked_current_document()
    document["decision"]["reason_codes"] = ["v5_owner_input_missing"]

    with pytest.raises(AdmissionViolation):
        _evaluate(document)


def test_missing_owner_input_rejects_claimed_proposal_or_capsule() -> None:
    document = _blocked_current_document()
    document["compass_capsule"]["capsule_hash"] = _SHA256

    with pytest.raises(AdmissionViolation):
        _evaluate(document)
