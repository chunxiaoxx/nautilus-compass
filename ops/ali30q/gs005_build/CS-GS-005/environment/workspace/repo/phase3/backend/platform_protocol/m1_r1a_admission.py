"""Fail-closed M1 R1a cross-owner plan-admission evaluation."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

_ADMISSION_SCHEMA = "m1-r1a-plan-admission-v1"
_OWNER_INPUT_SCHEMA = "m1-r1a-owner-input-v1"
_PLATFORM_O1_SCHEMA = "m1-r1a-platform-o1-candidate-v1"
_SHA1_RE = re.compile(r"[0-9a-f]{40}\Z")
_SHA256_RE = re.compile(r"[0-9a-f]{64}\Z")
_TASK6_TEMPLATE_PATH = (
    "docs/plans/2026-08-03-platform-protocol-v2-adapter-review-template.md"
)
_O1_EVIDENCE_PATH = "docs/evidence/m1/o1_acceptance.json"
_COMPASS_CAPSULE_PATH = "docs/contracts/m1-r1a-grounding-capsule-v1.json"
_V5_PLAN_ONLY_WAIVER_PATH = "docs/contracts/v5-r1a-plan-only-authorization-v1.json"
_TOP_LEVEL_FIELDS = frozenset(
    {
        "adjudicator",
        "compass_capsule",
        "decision",
        "platform_o1",
        "schema_version",
        "v5_g0",
    }
)
_ADJUDICATOR_FIELDS = frozenset(
    {"task6_template_commit", "task6_template_sha256", "template_role"}
)
_DECISION_FIELDS = frozenset({"reason_codes", "status"})
_PLATFORM_O1_FIELDS = frozenset(
    {
        "candidate_commit",
        "compass_revision_status",
        "compass_o1_revision",
        "o1_evidence_sha256",
        "schema_version",
        "task6_commit",
        "v5_o1_revision",
        "v5_revision_status",
        "verification_status",
    }
)
_OWNER_INPUT_FIELDS = frozenset(
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
_V5_OWNER_INPUT_FIELDS = _OWNER_INPUT_FIELDS | frozenset(
    {"authorization_path", "authorization_sha256"}
)
_COMPASS_CAPSULE_FIELDS = _OWNER_INPUT_FIELDS | frozenset(
    {"capsule_hash", "capsule_path", "runtime_capabilities"}
)
_COMPASS_CAPABILITY_FIELDS = frozenset(
    {
        "drift_write",
        "ingest",
        "model",
        "network",
        "recall",
        "source_write",
        "tool",
    }
)


class AdmissionViolation(ValueError):
    """Raised when plan-admission input widens the static R1a boundary."""


class SourceReadback(Protocol):
    """Trusted, read-only source authority used to ground an admission decision."""

    def require_commit(self, owner: str, commit: str) -> None:
        """Require the full commit to resolve in the owner's authority."""

    def require_absent_commit(self, owner: str, commit: str) -> None:
        """Require the full commit to be absent from the owner's authority."""

    def require_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        """Require an owner-local commit ancestry relation."""

    def require_not_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        """Require an owner-local non-ancestry relation."""

    def require_file_sha256(
        self,
        owner: str,
        commit: str,
        path: str,
        sha256: str,
    ) -> None:
        """Require canonical file bytes to match the published digest."""

    def require_file_absent(self, owner: str, commit: str, path: str) -> None:
        """Require a fixed path not to exist at the authority commit."""

    def require_o1_evidence(
        self,
        commit: str,
        task6_commit: str,
        v5_revision: str,
        compass_revision: str,
    ) -> None:
        """Require O1's own evidence to bind its Task 6 and cross-owner pins."""


@dataclass(frozen=True, slots=True)
class LocalGitSourceReadback:
    """Read immutable Git objects locally without fetch, checkout, or writes."""

    platform: Path
    v5: Path
    compass: Path

    def require_commit(self, owner: str, commit: str) -> None:
        if self._object_type(owner, commit) != "commit":
            _violate(f"{owner} commit does not resolve")

    def require_absent_commit(self, owner: str, commit: str) -> None:
        if self._object_type(owner, commit) != "missing":
            _violate(f"{owner} commit unexpectedly resolves")

    def require_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        self.require_commit(owner, ancestor)
        self.require_commit(owner, descendant)
        result = self._git(owner, "merge-base", "--is-ancestor", ancestor, descendant)
        if result.returncode != 0:
            _violate(f"{owner} ancestry requirement failed")

    def require_not_ancestor(
        self,
        owner: str,
        ancestor: str,
        descendant: str,
    ) -> None:
        self.require_commit(owner, ancestor)
        self.require_commit(owner, descendant)
        result = self._git(owner, "merge-base", "--is-ancestor", ancestor, descendant)
        if result.returncode == 0:
            _violate(f"{owner} non-ancestry requirement failed")
        if result.returncode != 1:
            _violate(f"{owner} non-ancestry readback failed")

    def require_file_sha256(
        self,
        owner: str,
        commit: str,
        path: str,
        sha256: str,
    ) -> None:
        self.require_commit(owner, commit)
        data = self._show_file(owner, commit, path)
        if hashlib.sha256(data).hexdigest() != sha256:
            _violate(f"{owner} pinned file hash does not match")

    def require_file_absent(self, owner: str, commit: str, path: str) -> None:
        self.require_commit(owner, commit)
        result = self._git(owner, "show", f"{commit}:{path}")
        if result.returncode == 0:
            _violate(f"{owner} fixed path unexpectedly exists")

    def require_o1_evidence(
        self,
        commit: str,
        task6_commit: str,
        v5_revision: str,
        compass_revision: str,
    ) -> None:
        data = self._show_file("platform", commit, _O1_EVIDENCE_PATH)
        try:
            document = json.loads(data)
        except json.JSONDecodeError:
            _violate("Platform O1 evidence is not canonical JSON")
        if not isinstance(document, Mapping):
            _violate("Platform O1 evidence is not an object")
        admission = document.get("admission")
        if not isinstance(admission, Mapping):
            _violate("Platform O1 evidence has no admission bindings")
        if (
            document.get("schema_version") != "nautilus.m1.o1.acceptance-evidence.v1"
            or document.get("status") != "accepted"
            or document.get("task6_revision") != task6_commit
            or admission.get("v5_revision") != v5_revision
            or admission.get("compass_revision") != compass_revision
        ):
            _violate("Platform O1 evidence bindings do not match")

    def _object_type(self, owner: str, commit: str) -> str:
        result = self._git(
            owner,
            "cat-file",
            "--batch-check=%(objecttype)",
            input_bytes=f"{commit}\n".encode("ascii"),
        )
        if result.returncode != 0:
            _violate(f"{owner} object readback failed")
        fields = result.stdout.decode("ascii", errors="replace").strip().split()
        if fields == ["commit"]:
            return "commit"
        if fields == [commit, "missing"]:
            return "missing"
        _violate(f"{owner} object readback is malformed")

    def _show_file(self, owner: str, commit: str, path: str) -> bytes:
        result = self._git(owner, "show", f"{commit}:{path}")
        if result.returncode != 0:
            _violate(f"{owner} fixed path does not resolve")
        return result.stdout

    def _git(
        self,
        owner: str,
        *arguments: str,
        input_bytes: bytes | None = None,
    ) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(
            ["git", "-C", str(self._repository(owner)), *arguments],
            check=False,
            input=input_bytes,
            capture_output=True,
        )

    def _repository(self, owner: str) -> Path:
        repositories = {
            "platform": self.platform,
            "v5": self.v5,
            "compass": self.compass,
        }
        try:
            return repositories[owner]
        except KeyError:
            _violate("unknown source authority")


@dataclass(frozen=True, slots=True)
class PlanAdmissionDecision:
    status: str
    reason_codes: tuple[str, ...]


def evaluate_plan_admission(
    document: Mapping[str, object],
    *,
    source_readback: SourceReadback,
) -> PlanAdmissionDecision:
    """Return the sole R1a planning decision or reject malformed authority."""
    top = _require_mapping(document, _TOP_LEVEL_FIELDS)
    if top["schema_version"] != _ADMISSION_SCHEMA:
        _violate("invalid admission schema")

    adjudicator = _parse_adjudicator(top["adjudicator"])
    platform_o1 = _parse_platform_o1(top["platform_o1"])
    v5_g0 = _parse_v5_owner_input(top["v5_g0"])
    compass = _parse_compass_capsule(top["compass_capsule"])
    decision = _parse_decision(top["decision"])
    if (
        platform_o1["verification_status"] == "reverified_candidate"
        and platform_o1["task6_commit"] != adjudicator["task6_template_commit"]
    ):
        _violate("reverified O1 must bind the current Task 6 adjudicator")

    _verify_source_readback(
        source_readback,
        adjudicator=adjudicator,
        platform_o1=platform_o1,
        v5_g0=v5_g0,
        compass=compass,
    )
    blockers = _derive_blockers(platform_o1, v5_g0, compass)
    expected_status = "blocked" if blockers else "ready_for_r1a_plan"
    expected_reasons = tuple(sorted(blockers))
    if decision != (expected_status, expected_reasons):
        _violate("decision does not match owner evidence")
    return PlanAdmissionDecision(
        status=expected_status,
        reason_codes=expected_reasons,
    )


def _parse_adjudicator(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _ADJUDICATOR_FIELDS)
    _require_sha1(document["task6_template_commit"])
    _require_sha256(document["task6_template_sha256"])
    if document["template_role"] != "reference_only":
        _violate("Task 6 template cannot become a domain authority")
    return document


def _parse_platform_o1(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _PLATFORM_O1_FIELDS)
    if document["schema_version"] != _PLATFORM_O1_SCHEMA:
        _violate("invalid Platform O1 schema")
    _require_sha1(document["candidate_commit"])
    _require_sha1(document["task6_commit"])
    _require_sha256(document["o1_evidence_sha256"])
    _require_sha1(document["v5_o1_revision"])
    _require_sha1(document["compass_o1_revision"])
    if document["verification_status"] not in {
        "historical_candidate",
        "reverified_candidate",
    }:
        _violate("invalid Platform O1 verification status")
    if document["v5_revision_status"] not in {
        "current_owner_pinned",
        "unresolvable",
    }:
        _violate("invalid V5 O1 revision status")
    if document["compass_revision_status"] not in {
        "current_owner_pinned",
        "noncanonical",
    }:
        _violate("invalid Compass O1 revision status")
    return document


def _parse_owner_input(
    value: object,
    expected_owner: str,
    expected_fields: frozenset[str] = _OWNER_INPUT_FIELDS,
) -> Mapping[str, object]:
    document = _require_mapping(value, expected_fields)
    if document["schema_version"] != _OWNER_INPUT_SCHEMA:
        _violate("invalid owner-input schema")
    if document["owner"] != expected_owner:
        _violate("owner input submitted by wrong owner")
    _require_sha1(document["authority_commit"])
    proposal_status = document["proposal_status"]
    if proposal_status not in {"missing", "pending", "submitted"}:
        _violate("invalid owner proposal status")
    if document["test_status"] not in {"not_run", "pass"}:
        _violate("invalid owner test status")
    if proposal_status in {"pending", "submitted"}:
        _require_sha1(document["proposal_commit"])
    elif document["proposal_commit"] is not None:
        _violate("missing owner input cannot claim a proposal")
    if (
        proposal_status in {"pending", "submitted"}
        and document["test_status"] != "pass"
    ):
        _violate("present owner input has no passing tests")
    if proposal_status == "missing" and document["test_status"] != "not_run":
        _violate("missing owner input cannot claim tests")
    if document["runtime_authorized"] is not False:
        _violate("runtime authorization is prohibited")
    return document


def _parse_v5_owner_input(value: object) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        _violate("invalid admission mapping")
    fields = frozenset(value)
    if fields not in {_OWNER_INPUT_FIELDS, _V5_OWNER_INPUT_FIELDS}:
        _violate("unexpected admission fields")
    document = _parse_owner_input(value, "v5", fields)
    if document["proposal_status"] != "submitted":
        if fields != _OWNER_INPUT_FIELDS:
            _violate("unsubmitted V5 input cannot claim a waiver")
        return document
    if fields != _V5_OWNER_INPUT_FIELDS:
        _violate("submitted V5 input requires waiver binding")
    if document["authorization_path"] != _V5_PLAN_ONLY_WAIVER_PATH:
        _violate("invalid V5 plan-only waiver path")
    _require_sha256(document["authorization_sha256"])
    return document


def _parse_compass_capsule(value: object) -> Mapping[str, object]:
    document = _require_mapping(value, _COMPASS_CAPSULE_FIELDS)
    owner_input = _parse_owner_input(document, "compass", _COMPASS_CAPSULE_FIELDS)
    if owner_input["proposal_status"] == "missing":
        if (
            document["capsule_hash"] is not None
            or document["capsule_path"] is not None
            or document["runtime_capabilities"] != {}
        ):
            _violate("missing Compass input cannot claim a capsule")
        return document
    _require_sha256(document["capsule_hash"])
    if document["capsule_path"] != _COMPASS_CAPSULE_PATH:
        _violate("invalid Compass capsule path")
    capabilities = _require_mapping(
        document["runtime_capabilities"],
        _COMPASS_CAPABILITY_FIELDS,
    )
    if any(capability is not False for capability in capabilities.values()):
        _violate("Compass runtime capability is prohibited")
    return document


def _parse_decision(value: object) -> tuple[str, tuple[str, ...]]:
    document = _require_mapping(value, _DECISION_FIELDS)
    status = document["status"]
    reasons = document["reason_codes"]
    if status not in {"blocked", "ready_for_r1a_plan"}:
        _violate("invalid admission decision status")
    if not isinstance(reasons, list) or any(
        not isinstance(reason, str) for reason in reasons
    ):
        _violate("invalid admission reason codes")
    if len(set(reasons)) != len(reasons):
        _violate("duplicate admission reason codes")
    return status, tuple(reasons)


def _derive_blockers(
    platform_o1: Mapping[str, object],
    v5_g0: Mapping[str, object],
    compass: Mapping[str, object],
) -> set[str]:
    blockers: set[str] = set()
    if platform_o1["verification_status"] == "historical_candidate":
        blockers.add("platform_o1_historical_candidate")
    if platform_o1["v5_revision_status"] == "unresolvable":
        blockers.add("v5_o1_revision_unresolvable")
    if platform_o1["compass_revision_status"] == "noncanonical":
        blockers.add("compass_o1_revision_noncanonical")
    if v5_g0["proposal_status"] == "missing":
        blockers.add("v5_owner_input_missing")
    elif v5_g0["proposal_status"] == "pending":
        blockers.add("v5_g0_pending")
    if compass["proposal_status"] == "missing":
        blockers.add("compass_owner_input_missing")
    elif compass["proposal_status"] == "pending":
        blockers.add("compass_capsule_pending")
    return blockers


def _verify_source_readback(
    source_readback: SourceReadback,
    *,
    adjudicator: Mapping[str, object],
    platform_o1: Mapping[str, object],
    v5_g0: Mapping[str, object],
    compass: Mapping[str, object],
) -> None:
    source_readback.require_commit(
        "platform",
        _string(adjudicator["task6_template_commit"]),
    )
    source_readback.require_file_sha256(
        "platform",
        _string(adjudicator["task6_template_commit"]),
        _TASK6_TEMPLATE_PATH,
        _string(adjudicator["task6_template_sha256"]),
    )
    source_readback.require_commit(
        "platform",
        _string(platform_o1["candidate_commit"]),
    )
    source_readback.require_commit("platform", _string(platform_o1["task6_commit"]))
    source_readback.require_file_sha256(
        "platform",
        _string(platform_o1["candidate_commit"]),
        _O1_EVIDENCE_PATH,
        _string(platform_o1["o1_evidence_sha256"]),
    )
    source_readback.require_o1_evidence(
        _string(platform_o1["candidate_commit"]),
        _string(platform_o1["task6_commit"]),
        _string(platform_o1["v5_o1_revision"]),
        _string(platform_o1["compass_o1_revision"]),
    )
    source_readback.require_ancestor(
        "platform",
        _string(platform_o1["task6_commit"]),
        _string(platform_o1["candidate_commit"]),
    )
    _verify_owner_source(source_readback, "v5", v5_g0)
    _verify_v5_plan_only_waiver_source(source_readback, v5_g0)
    _verify_owner_source(source_readback, "compass", compass)
    _verify_o1_owner_pins(source_readback, platform_o1, v5_g0, compass)
    _verify_compass_capsule_source(source_readback, compass)


def _verify_owner_source(
    source_readback: SourceReadback,
    owner: str,
    owner_input: Mapping[str, object],
) -> None:
    authority_commit = _string(owner_input["authority_commit"])
    source_readback.require_commit(owner, authority_commit)
    if owner_input["proposal_status"] in {"pending", "submitted"}:
        proposal_commit = _string(owner_input["proposal_commit"])
        source_readback.require_commit(owner, proposal_commit)
        source_readback.require_ancestor(owner, authority_commit, proposal_commit)


def _verify_o1_owner_pins(
    source_readback: SourceReadback,
    platform_o1: Mapping[str, object],
    v5_g0: Mapping[str, object],
    compass: Mapping[str, object],
) -> None:
    v5_revision = _string(platform_o1["v5_o1_revision"])
    if platform_o1["v5_revision_status"] == "unresolvable":
        source_readback.require_absent_commit("v5", v5_revision)
    else:
        _require_matching_owner_pin(v5_revision, v5_g0, "V5")
        source_readback.require_commit("v5", v5_revision)

    compass_revision = _string(platform_o1["compass_o1_revision"])
    compass_authority = _string(compass["authority_commit"])
    if platform_o1["compass_revision_status"] == "noncanonical":
        source_readback.require_commit("compass", compass_revision)
        source_readback.require_not_ancestor(
            "compass",
            compass_revision,
            compass_authority,
        )
    else:
        _require_matching_owner_pin(compass_revision, compass, "Compass")
        source_readback.require_commit("compass", compass_revision)


def _verify_v5_plan_only_waiver_source(
    source_readback: SourceReadback,
    v5_g0: Mapping[str, object],
) -> None:
    if v5_g0["proposal_status"] != "submitted":
        return
    source_readback.require_file_sha256(
        "v5",
        _string(v5_g0["proposal_commit"]),
        _string(v5_g0["authorization_path"]),
        _string(v5_g0["authorization_sha256"]),
    )


def _require_matching_owner_pin(
    o1_revision: str,
    owner_input: Mapping[str, object],
    owner: str,
) -> None:
    if owner_input["proposal_status"] != "submitted":
        _violate(f"current {owner} O1 pin requires a submitted owner input")
    if o1_revision != owner_input["proposal_commit"]:
        _violate(f"O1 {owner} revision does not match its owner proposal")


def _verify_compass_capsule_source(
    source_readback: SourceReadback,
    compass: Mapping[str, object],
) -> None:
    authority_commit = _string(compass["authority_commit"])
    if compass["proposal_status"] == "missing":
        source_readback.require_file_absent(
            "compass",
            authority_commit,
            _COMPASS_CAPSULE_PATH,
        )
        return
    source_readback.require_file_sha256(
        "compass",
        _string(compass["proposal_commit"]),
        _string(compass["capsule_path"]),
        _string(compass["capsule_hash"]),
    )


def _string(value: object) -> str:
    if not isinstance(value, str):
        _violate("invalid source readback value")
    return value


def _require_mapping(
    value: object, expected_fields: frozenset[str]
) -> Mapping[str, object]:
    if not isinstance(value, Mapping) or frozenset(value) != expected_fields:
        _violate("unexpected admission fields")
    return value


def _require_sha1(value: object) -> None:
    if not isinstance(value, str) or _SHA1_RE.fullmatch(value) is None:
        _violate("invalid full Git SHA")


def _require_sha256(value: object) -> None:
    if not isinstance(value, str) or _SHA256_RE.fullmatch(value) is None:
        _violate("invalid SHA-256")


def _violate(message: str) -> None:
    raise AdmissionViolation(message)
