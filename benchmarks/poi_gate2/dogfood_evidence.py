"""Strict non-authoritative ExperiencePacket evidence for C0 dogfood."""

from __future__ import annotations

import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import PurePosixPath, PureWindowsPath
from typing import Any

from gep.experience_packet import ExperiencePacket, to_frontmatter

from .canonical import hash_json


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_COMMIT_PATTERN = re.compile(r"[0-9a-f]{40}")
_VERIFICATION_OUTCOMES = {
    "locally_verified": "success",
    "repair_resolved": "success_after_repair",
    "blocked": "blocked",
}
_CANDIDATE_SCHEMA = "compass.poi_gate2.dogfood_candidate.v1"
_BUNDLE_SCHEMA = "compass.poi_gate2.dogfood_bundle.v1"
_ARTIFACT_SCHEMA = "compass.poi_gate2.c0_dogfood_artifact.v1"
_CANDIDATE_STATE = "blocked_missing_independent_verdict"
_AUTHORITY_STATE = "blocked_missing_independent_verdicts"
_EVIDENCE_TIER = "c0_convergence_dogfood"
_PACKET_V0_FIELDS = {
    "episode_id",
    "parent_episode_id",
    "task",
    "action_kind",
    "tool_chain",
    "outcome",
    "failure_mode",
    "reward_delta",
    "impact",
    "route_key",
    "capsule_candidate",
    "policy_hint",
}
_PREFLIGHT_FIELDS = {
    "schema_version",
    "source_bundle_hash",
    "candidate_count",
    "local_verification_counts",
    "independent_verdict_count",
    "stage_a_input_count",
    "stage_a_state",
    "development_recommendation",
    "runtime_recommendation",
    "improvement_claim",
}


@dataclass(frozen=True)
class DogfoodPacketCandidate:
    """One locally observed packet that has no independent verdict authority."""

    schema_version: str
    packet: ExperiencePacket
    plan_commit: str
    plan_hash: str
    source_evidence_hashes: tuple[str, ...]
    verification_state: str
    candidate_state: str
    record_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != _CANDIDATE_SCHEMA:
            raise ValueError("schema_version is unsupported")
        if not isinstance(self.packet, ExperiencePacket):
            raise TypeError("packet must be an ExperiencePacket")
        _validate_packet(self.packet, self.verification_state)
        _validate_commit(self.plan_commit)
        _validate_hash("plan_hash", self.plan_hash)
        hashes = _normalize_hashes(self.source_evidence_hashes)
        if self.candidate_state != _CANDIDATE_STATE:
            raise ValueError("candidate_state must remain blocked")
        object.__setattr__(self, "source_evidence_hashes", hashes)
        object.__setattr__(self, "record_hash", hash_json(self._preimage()))

    @classmethod
    def from_args(
        cls,
        *,
        packet: ExperiencePacket,
        plan_commit: str,
        plan_hash: str,
        source_evidence_hashes: Sequence[str],
        verification_state: str,
    ) -> "DogfoodPacketCandidate":
        return cls(
            schema_version=_CANDIDATE_SCHEMA,
            packet=packet,
            plan_commit=plan_commit,
            plan_hash=plan_hash,
            source_evidence_hashes=tuple(source_evidence_hashes),
            verification_state=verification_state,
            candidate_state=_CANDIDATE_STATE,
        )

    def _preimage(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "packet": to_frontmatter(self.packet),
            "plan_commit": self.plan_commit,
            "plan_hash": self.plan_hash,
            "source_evidence_hashes": list(self.source_evidence_hashes),
            "verification_state": self.verification_state,
            "candidate_state": self.candidate_state,
        }


@dataclass(frozen=True)
class DogfoodPacketBundle:
    """A deterministic bundle that cannot confer action or capsule authority."""

    schema_version: str
    evidence_tier: str
    authority_state: str
    candidates: tuple[DogfoodPacketCandidate, ...]
    bundle_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != _BUNDLE_SCHEMA:
            raise ValueError("schema_version is unsupported")
        if self.evidence_tier != _EVIDENCE_TIER:
            raise ValueError("evidence_tier is unsupported")
        if self.authority_state != _AUTHORITY_STATE:
            raise ValueError("authority_state must remain blocked")
        candidates = _normalize_candidates(self.candidates)
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "bundle_hash", hash_json(self._preimage()))

    @classmethod
    def from_args(
        cls,
        *,
        candidates: Sequence[DogfoodPacketCandidate],
    ) -> "DogfoodPacketBundle":
        return cls(
            schema_version=_BUNDLE_SCHEMA,
            evidence_tier=_EVIDENCE_TIER,
            authority_state=_AUTHORITY_STATE,
            candidates=tuple(candidates),
        )

    def _preimage(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "evidence_tier": self.evidence_tier,
            "authority_state": self.authority_state,
            "candidates": [candidate_to_mapping(row) for row in self.candidates],
        }


@dataclass(frozen=True)
class DogfoodArtifact:
    """Portable D0 evidence bound to one frozen plan and source set."""

    schema_version: str
    source_plan_commit: str
    source_plan_path: str
    source_hashes: tuple[tuple[str, str], ...]
    bundle: DogfoodPacketBundle
    artifact_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if self.schema_version != _ARTIFACT_SCHEMA:
            raise ValueError("schema_version is unsupported")
        _validate_commit(self.source_plan_commit)
        _validate_relative_path("source_plan_path", self.source_plan_path)
        source_hashes = _normalize_source_hashes(self.source_hashes)
        if not isinstance(self.bundle, DogfoodPacketBundle):
            raise TypeError("bundle must be a DogfoodPacketBundle")
        source_map = dict(source_hashes)
        if self.source_plan_path not in source_map:
            raise ValueError("source_plan_path must be present in source_hashes")
        evidence_hashes = set(source_map.values())
        for candidate in self.bundle.candidates:
            if candidate.plan_commit != self.source_plan_commit:
                raise ValueError("plan_commit does not match source_plan_commit")
            if candidate.plan_hash != source_map[self.source_plan_path]:
                raise ValueError("plan_hash does not match the frozen plan source hash")
            if not set(candidate.source_evidence_hashes).issubset(evidence_hashes):
                raise ValueError("candidate evidence hashes are not bound by source_hashes")
        object.__setattr__(self, "source_hashes", source_hashes)
        object.__setattr__(self, "artifact_hash", hash_json(self._preimage()))

    @classmethod
    def from_args(
        cls,
        *,
        source_plan_commit: str,
        source_plan_path: str,
        source_hashes: Mapping[str, str],
        bundle: DogfoodPacketBundle,
    ) -> "DogfoodArtifact":
        return cls(
            schema_version=_ARTIFACT_SCHEMA,
            source_plan_commit=source_plan_commit,
            source_plan_path=source_plan_path,
            source_hashes=tuple(source_hashes.items()),
            bundle=bundle,
        )

    @property
    def preflight(self) -> dict[str, Any]:
        return evaluate_dogfood_bundle(self.bundle)

    def _preimage(self) -> dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "source_plan_commit": self.source_plan_commit,
            "source_plan_path": self.source_plan_path,
            "source_hashes": dict(self.source_hashes),
            "bundle": bundle_to_mapping(self.bundle),
            "preflight": self.preflight,
        }


def candidate_to_mapping(candidate: DogfoodPacketCandidate) -> dict[str, Any]:
    if not isinstance(candidate, DogfoodPacketCandidate):
        raise TypeError("candidate must be a DogfoodPacketCandidate")
    return {**candidate._preimage(), "record_hash": candidate.record_hash}


def candidate_from_mapping(raw: Mapping[str, Any]) -> DogfoodPacketCandidate:
    expected = {
        "schema_version",
        "packet",
        "plan_commit",
        "plan_hash",
        "source_evidence_hashes",
        "verification_state",
        "candidate_state",
        "record_hash",
    }
    values = _exact_mapping("DogfoodPacketCandidate", raw, expected)
    supplied_hash = values.pop("record_hash")
    packet = _packet_from_mapping(values.pop("packet"))
    candidate = DogfoodPacketCandidate(packet=packet, **values)
    if supplied_hash != candidate.record_hash:
        raise ValueError("record_hash does not match the canonical preimage")
    return candidate


def bundle_to_mapping(bundle: DogfoodPacketBundle) -> dict[str, Any]:
    if not isinstance(bundle, DogfoodPacketBundle):
        raise TypeError("bundle must be a DogfoodPacketBundle")
    return {**bundle._preimage(), "bundle_hash": bundle.bundle_hash}


def bundle_from_mapping(raw: Mapping[str, Any]) -> DogfoodPacketBundle:
    expected = {
        "schema_version",
        "evidence_tier",
        "authority_state",
        "candidates",
        "bundle_hash",
    }
    values = _exact_mapping("DogfoodPacketBundle", raw, expected)
    supplied_hash = values.pop("bundle_hash")
    candidates = values.pop("candidates")
    if isinstance(candidates, (str, bytes)) or not isinstance(candidates, Sequence):
        raise TypeError("candidates must be an ordered sequence")
    bundle = DogfoodPacketBundle(
        candidates=tuple(candidate_from_mapping(row) for row in candidates),
        **values,
    )
    if supplied_hash != bundle.bundle_hash:
        raise ValueError("bundle_hash does not match the canonical preimage")
    return bundle


def artifact_to_mapping(artifact: DogfoodArtifact) -> dict[str, Any]:
    if not isinstance(artifact, DogfoodArtifact):
        raise TypeError("artifact must be a DogfoodArtifact")
    return {**artifact._preimage(), "artifact_hash": artifact.artifact_hash}


def artifact_from_mapping(raw: Mapping[str, Any]) -> DogfoodArtifact:
    expected = {
        "schema_version",
        "source_plan_commit",
        "source_plan_path",
        "source_hashes",
        "bundle",
        "preflight",
        "artifact_hash",
    }
    values = _exact_mapping("DogfoodArtifact", raw, expected)
    supplied_hash = values.pop("artifact_hash")
    schema_version = values.pop("schema_version")
    if schema_version != _ARTIFACT_SCHEMA:
        raise ValueError("schema_version is unsupported")
    preflight = _exact_mapping(
        "DogfoodPreflight",
        values.pop("preflight"),
        _PREFLIGHT_FIELDS,
    )
    bundle = bundle_from_mapping(values.pop("bundle"))
    source_hashes = _source_hash_mapping(values.pop("source_hashes"))
    artifact = DogfoodArtifact.from_args(
        source_hashes=source_hashes,
        bundle=bundle,
        **values,
    )
    if preflight != artifact.preflight:
        raise ValueError("preflight does not match the bound bundle")
    if supplied_hash != artifact.artifact_hash:
        raise ValueError("artifact_hash does not match the canonical preimage")
    return artifact


def evaluate_dogfood_bundle(bundle: DogfoodPacketBundle) -> dict[str, Any]:
    """Report the exact fail-closed D0 boundary before independent verdicts."""

    if not isinstance(bundle, DogfoodPacketBundle):
        raise TypeError("bundle must be a DogfoodPacketBundle")
    counts: dict[str, int] = {}
    for candidate in bundle.candidates:
        counts[candidate.verification_state] = counts.get(candidate.verification_state, 0) + 1
    return {
        "schema_version": "compass.poi_gate2.dogfood_preflight.v1",
        "source_bundle_hash": bundle.bundle_hash,
        "candidate_count": len(bundle.candidates),
        "local_verification_counts": dict(sorted(counts.items())),
        "independent_verdict_count": 0,
        "stage_a_input_count": 0,
        "stage_a_state": "blocked_missing_independent_verdicts",
        "development_recommendation": "flat",
        "runtime_recommendation": "flat",
        "improvement_claim": False,
    }


def _validate_packet(packet: ExperiencePacket, verification_state: str) -> None:
    _validate_packet_v0_fields(to_frontmatter(packet))
    if not packet.episode_id:
        raise ValueError("packet episode_id is required")
    if packet.capsule_candidate is not False:
        raise ValueError("capsule_candidate must be false")
    if packet.impact is not None:
        raise ValueError("impact must be absent")
    if packet.reward_delta is not None:
        raise ValueError("reward_delta must be absent")
    expected_outcome = _VERIFICATION_OUTCOMES.get(verification_state)
    if expected_outcome is None:
        raise ValueError("verification_state is unsupported")
    if packet.outcome != expected_outcome:
        raise ValueError("outcome does not match verification_state")


def _normalize_hashes(value: Any) -> tuple[str, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("source_evidence_hashes must be an ordered sequence")
    hashes = tuple(value)
    if not hashes:
        raise ValueError("source_evidence_hashes must not be empty")
    if len(set(hashes)) != len(hashes):
        raise ValueError("source_evidence_hashes must be unique")
    for item in hashes:
        _validate_hash("source_evidence_hashes", item)
    return tuple(sorted(hashes))


def _normalize_candidates(value: Any) -> tuple[DogfoodPacketCandidate, ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("candidates must be an ordered sequence")
    candidates = tuple(value)
    if not candidates or any(not isinstance(row, DogfoodPacketCandidate) for row in candidates):
        raise ValueError("candidates must contain DogfoodPacketCandidate values")
    episode_ids = [row.packet.episode_id for row in candidates]
    if len(set(episode_ids)) != len(episode_ids):
        raise ValueError("candidates must contain unique episode_id values")
    plan_bindings = {(row.plan_commit, row.plan_hash) for row in candidates}
    if len(plan_bindings) != 1:
        raise ValueError("candidates must share one frozen plan binding")
    return candidates


def _packet_from_mapping(raw: Any) -> ExperiencePacket:
    if not isinstance(raw, Mapping) or any(not isinstance(key, str) for key in raw):
        raise TypeError("packet must be a string-keyed mapping")
    _validate_packet_v0_fields(raw)
    try:
        return ExperiencePacket(**dict(raw))
    except (TypeError, ValueError) as exc:
        raise ValueError("packet is invalid") from exc


def _exact_mapping(label: str, raw: Any, expected: set[str]) -> dict[str, Any]:
    if not isinstance(raw, Mapping) or any(not isinstance(key, str) for key in raw):
        raise TypeError(f"{label} must be a string-keyed mapping")
    keys = set(raw)
    unknown = keys - expected
    missing = expected - keys
    if unknown:
        raise TypeError(f"unknown {label} fields: {', '.join(sorted(unknown))}")
    if missing:
        raise TypeError(f"missing {label} fields: {', '.join(sorted(missing))}")
    return dict(raw)


def _validate_hash(label: str, value: Any) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{label} must be a lowercase sha256 hash")


def _validate_commit(value: Any) -> None:
    if not isinstance(value, str) or _COMMIT_PATTERN.fullmatch(value) is None:
        raise ValueError("plan_commit must be a lowercase full commit hash")


def _source_hash_mapping(raw: Any) -> dict[str, str]:
    if not isinstance(raw, Mapping) or any(not isinstance(key, str) for key in raw):
        raise TypeError("source_hashes must be a string-keyed mapping")
    return dict(_normalize_source_hashes(tuple(raw.items())))


def _normalize_source_hashes(value: Any) -> tuple[tuple[str, str], ...]:
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise TypeError("source_hashes must be an ordered sequence")
    rows = tuple(value)
    if not rows:
        raise ValueError("source_hashes must not be empty")
    normalized: dict[str, str] = {}
    for row in rows:
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence) or len(row) != 2:
            raise TypeError("source_hashes entries must contain path and hash")
        path, digest = row
        _validate_relative_path("source_hashes path", path)
        _validate_hash("source_hashes", digest)
        if path in normalized:
            raise ValueError("source_hashes paths must be unique")
        normalized[path] = digest
    return tuple(sorted(normalized.items()))


def _validate_relative_path(label: str, value: Any) -> None:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError(f"{label} must be a normalized relative path")
    path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        path.is_absolute()
        or bool(windows_path.drive)
        or ".." in path.parts
        or str(path) != value
    ):
        raise ValueError(f"{label} must be a normalized relative path")


def _validate_packet_v0_fields(raw: Mapping[str, Any]) -> None:
    unknown = set(raw) - _PACKET_V0_FIELDS
    if unknown:
        raise TypeError(f"unknown ExperiencePacket v0 fields: {', '.join(sorted(unknown))}")


__all__ = [
    "DogfoodArtifact",
    "DogfoodPacketBundle",
    "DogfoodPacketCandidate",
    "artifact_from_mapping",
    "artifact_to_mapping",
    "bundle_from_mapping",
    "bundle_to_mapping",
    "candidate_from_mapping",
    "candidate_to_mapping",
    "evaluate_dogfood_bundle",
]
