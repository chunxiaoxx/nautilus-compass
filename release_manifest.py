"""Strict provenance manifest for immutable Compass release artifacts."""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from types import MappingProxyType
from typing import Any, Dict, Optional


MANIFEST_SCHEMA_VERSION = "compass.release.manifest.v1"
DEFAULT_POLICY = "flat"
BUILD_TOOL = "compass-release-control-v1"
PYTHON_REQUIRES = ">=3.9"
RELEASE_SCHEMA_VERSIONS = MappingProxyType(
    {
        "experience_packet": "compass.experience_packet.v0",
        "flywheel_event": "compass.flywheel.event.v1",
        "verdict_packet": "compass.verdict_packet.v0",
    }
)

_MANIFEST_KEYS = frozenset(
    {
        "schema_version",
        "release_id",
        "version",
        "git_sha",
        "wheel_filename",
        "wheel_sha256",
        "python_requires",
        "schema_versions",
        "default_policy",
        "built_at",
        "build_tool",
    }
)
_VERSION_PATTERN = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+(?:[A-Za-z0-9][A-Za-z0-9._+-]*)?")
_GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_WHEEL_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._+-]*\.whl")
_UTC_RFC3339_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)


class ReleaseManifestError(ValueError):
    """Fail-closed manifest validation error with a stable reason code."""

    def __init__(self, reason_code: str) -> None:
        self.reason_code = reason_code
        super().__init__(reason_code)


class _DuplicateKeyError(ValueError):
    pass


def _strict_object(pairs):
    result: Dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise _DuplicateKeyError(key)
        result[key] = value
    return result


def _reject_json_constant(_value: str) -> None:
    raise ValueError("non-finite JSON constant")


def _require_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping[key]
    if not isinstance(value, str):
        raise ReleaseManifestError("invalid_type")
    return value


def _validate_timestamp(value: str) -> None:
    if _UTC_RFC3339_PATTERN.fullmatch(value) is None:
        raise ReleaseManifestError("invalid_built_at")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ReleaseManifestError("invalid_built_at") from exc
    if parsed.tzinfo != timezone.utc:
        raise ReleaseManifestError("invalid_built_at")


def _release_id(version: str, git_sha: str, wheel_sha256: str) -> str:
    return "compass-{}-{}-{}".format(
        version,
        git_sha[:12],
        wheel_sha256[len("sha256:") : len("sha256:") + 12],
    )


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return "sha256:" + digest.hexdigest()


@dataclass(frozen=True)
class ReleaseManifest:
    """One immutable, hash-bound Compass wheel release."""

    schema_version: str
    release_id: str
    version: str
    git_sha: str
    wheel_filename: str
    wheel_sha256: str
    python_requires: str
    schema_versions: Mapping[str, str]
    default_policy: str
    built_at: str
    build_tool: str

    @classmethod
    def from_mapping(
        cls,
        mapping: Mapping[str, Any],
        expected_version: Optional[str] = None,
    ) -> "ReleaseManifest":
        if not isinstance(mapping, Mapping):
            raise ReleaseManifestError("invalid_mapping")
        if set(mapping) != _MANIFEST_KEYS:
            raise ReleaseManifestError("invalid_keys")

        values = {key: _require_string(mapping, key) for key in _MANIFEST_KEYS - {"schema_versions"}}
        schema_versions = mapping["schema_versions"]
        if not isinstance(schema_versions, Mapping):
            raise ReleaseManifestError("invalid_type")
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in schema_versions.items()):
            raise ReleaseManifestError("invalid_type")
        if dict(schema_versions) != dict(RELEASE_SCHEMA_VERSIONS):
            raise ReleaseManifestError("invalid_schema_versions")

        if values["schema_version"] != MANIFEST_SCHEMA_VERSION:
            raise ReleaseManifestError("invalid_schema_version")
        if _VERSION_PATTERN.fullmatch(values["version"]) is None:
            raise ReleaseManifestError("invalid_version")
        if expected_version is not None:
            if not isinstance(expected_version, str) or values["version"] != expected_version:
                raise ReleaseManifestError("version_mismatch")
        if _GIT_SHA_PATTERN.fullmatch(values["git_sha"]) is None:
            raise ReleaseManifestError("invalid_git_sha")
        if (
            "/" in values["wheel_filename"]
            or "\\" in values["wheel_filename"]
            or _WHEEL_PATTERN.fullmatch(values["wheel_filename"]) is None
        ):
            raise ReleaseManifestError("invalid_wheel_filename")
        if _HASH_PATTERN.fullmatch(values["wheel_sha256"]) is None:
            raise ReleaseManifestError("invalid_wheel_hash")
        if values["python_requires"] != PYTHON_REQUIRES:
            raise ReleaseManifestError("invalid_python_requires")
        if values["default_policy"] != DEFAULT_POLICY:
            raise ReleaseManifestError("invalid_default_policy")
        _validate_timestamp(values["built_at"])
        if values["build_tool"] != BUILD_TOOL:
            raise ReleaseManifestError("invalid_build_tool")

        expected_release_id = _release_id(
            values["version"], values["git_sha"], values["wheel_sha256"]
        )
        if values["release_id"] != expected_release_id:
            raise ReleaseManifestError("invalid_release_id")

        return cls(
            schema_version=values["schema_version"],
            release_id=values["release_id"],
            version=values["version"],
            git_sha=values["git_sha"],
            wheel_filename=values["wheel_filename"],
            wheel_sha256=values["wheel_sha256"],
            python_requires=values["python_requires"],
            schema_versions=MappingProxyType(dict(schema_versions)),
            default_policy=values["default_policy"],
            built_at=values["built_at"],
            build_tool=values["build_tool"],
        )

    @classmethod
    def from_json_bytes(
        cls,
        encoded: bytes,
        expected_version: Optional[str] = None,
    ) -> "ReleaseManifest":
        if not isinstance(encoded, bytes):
            raise ReleaseManifestError("invalid_json")
        try:
            mapping = json.loads(
                encoded.decode("utf-8"),
                object_pairs_hook=_strict_object,
                parse_constant=_reject_json_constant,
            )
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError) as exc:
            raise ReleaseManifestError("invalid_json") from exc
        if not isinstance(mapping, Mapping):
            raise ReleaseManifestError("invalid_json")
        return cls.from_mapping(mapping, expected_version=expected_version)

    @classmethod
    def build(
        cls,
        version: str,
        git_sha: str,
        wheel_path: Path,
        built_at: str,
    ) -> "ReleaseManifest":
        path = Path(wheel_path)
        if not path.is_file():
            raise ReleaseManifestError("wheel_missing")
        wheel_digest = _sha256_file(path)
        mapping = {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "release_id": _release_id(version, git_sha, wheel_digest),
            "version": version,
            "git_sha": git_sha,
            "wheel_filename": path.name,
            "wheel_sha256": wheel_digest,
            "python_requires": PYTHON_REQUIRES,
            "schema_versions": dict(RELEASE_SCHEMA_VERSIONS),
            "default_policy": DEFAULT_POLICY,
            "built_at": built_at,
            "build_tool": BUILD_TOOL,
        }
        return cls.from_mapping(mapping, expected_version=version)

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "release_id": self.release_id,
            "version": self.version,
            "git_sha": self.git_sha,
            "wheel_filename": self.wheel_filename,
            "wheel_sha256": self.wheel_sha256,
            "python_requires": self.python_requires,
            "schema_versions": dict(self.schema_versions),
            "default_policy": self.default_policy,
            "built_at": self.built_at,
            "build_tool": self.build_tool,
        }

    def canonical_bytes(self) -> bytes:
        return (
            json.dumps(
                self.to_mapping(),
                ensure_ascii=False,
                separators=(",", ":"),
                sort_keys=True,
            ).encode("utf-8")
            + b"\n"
        )


__all__ = [
    "BUILD_TOOL",
    "DEFAULT_POLICY",
    "MANIFEST_SCHEMA_VERSION",
    "PYTHON_REQUIRES",
    "RELEASE_SCHEMA_VERSIONS",
    "ReleaseManifest",
    "ReleaseManifestError",
]
