from __future__ import annotations

import json
from dataclasses import FrozenInstanceError

import pytest

from release_manifest import (
    BUILD_TOOL,
    DEFAULT_POLICY,
    MANIFEST_SCHEMA_VERSION,
    RELEASE_SCHEMA_VERSIONS,
    ReleaseManifest,
    ReleaseManifestError,
)


GIT_SHA = "a" * 40
WHEEL_DIGEST = "sha256:" + "b" * 64
BUILT_AT = "2026-08-01T12:34:56Z"


def valid_mapping(**overrides):
    mapping = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "release_id": "compass-2.3.0-aaaaaaaaaaaa-bbbbbbbbbbbb",
        "version": "2.3.0",
        "git_sha": GIT_SHA,
        "wheel_filename": "nautilus_compass-2.3.0-py3-none-any.whl",
        "wheel_sha256": WHEEL_DIGEST,
        "python_requires": ">=3.9",
        "schema_versions": dict(RELEASE_SCHEMA_VERSIONS),
        "default_policy": DEFAULT_POLICY,
        "built_at": BUILT_AT,
        "build_tool": BUILD_TOOL,
    }
    mapping.update(overrides)
    return mapping


def test_manifest_round_trips_as_canonical_json():
    manifest = ReleaseManifest.from_mapping(valid_mapping(), expected_version="2.3.0")

    encoded = manifest.canonical_bytes()

    assert encoded.endswith(b"\n")
    assert encoded == (
        json.dumps(
            valid_mapping(),
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        + b"\n"
    )
    assert ReleaseManifest.from_json_bytes(
        encoded, expected_version="2.3.0"
    ) == manifest


def test_manifest_is_frozen_and_freezes_schema_versions():
    manifest = ReleaseManifest.from_mapping(valid_mapping())

    with pytest.raises(FrozenInstanceError):
        manifest.version = "9.9.9"
    with pytest.raises(TypeError):
        manifest.schema_versions["flywheel_event"] = "changed"


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "compass.release.manifest.v0"),
        ("release_id", "wrong"),
        ("version", "2.3.0/escape"),
        ("git_sha", "A" * 40),
        ("git_sha", "a" * 39),
        ("wheel_filename", "../artifact.whl"),
        ("wheel_filename", "artifact.zip"),
        ("wheel_sha256", "b" * 64),
        ("wheel_sha256", "sha256:" + "B" * 64),
        ("python_requires", ">=3.8"),
        ("schema_versions", {"flywheel_event": "compass.flywheel.event.v1"}),
        ("default_policy", "poi"),
        ("built_at", "2026-08-01T12:34:56+00:00"),
        ("built_at", "2026-13-01T12:34:56Z"),
        ("build_tool", "other"),
    ],
)
def test_manifest_rejects_invalid_fields(field, value):
    with pytest.raises(ReleaseManifestError):
        ReleaseManifest.from_mapping(valid_mapping(**{field: value}))


@pytest.mark.parametrize("field", tuple(valid_mapping()))
def test_manifest_rejects_missing_fields(field):
    mapping = valid_mapping()
    mapping.pop(field)

    with pytest.raises(ReleaseManifestError, match="invalid_keys"):
        ReleaseManifest.from_mapping(mapping)


def test_manifest_rejects_unknown_fields():
    with pytest.raises(ReleaseManifestError, match="invalid_keys"):
        ReleaseManifest.from_mapping(valid_mapping(extra="not allowed"))


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("version", 230),
        ("git_sha", b"a" * 40),
        ("schema_versions", []),
        ("default_policy", True),
    ],
)
def test_manifest_rejects_type_coercion(field, value):
    with pytest.raises(ReleaseManifestError):
        ReleaseManifest.from_mapping(valid_mapping(**{field: value}))


def test_manifest_requires_expected_package_version():
    with pytest.raises(ReleaseManifestError, match="version_mismatch"):
        ReleaseManifest.from_mapping(valid_mapping(), expected_version="2.3.1")


def test_manifest_rejects_duplicate_json_keys():
    encoded = ReleaseManifest.from_mapping(valid_mapping()).canonical_bytes()
    duplicate = encoded.replace(
        b'{"build_tool":', b'{"version":"2.3.0","build_tool":', 1
    )

    with pytest.raises(ReleaseManifestError, match="invalid_json"):
        ReleaseManifest.from_json_bytes(duplicate)


def test_build_hashes_wheel_and_derives_stable_release_id(tmp_path):
    wheel = tmp_path / "nautilus_compass-2.3.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel bytes")

    first = ReleaseManifest.build(
        version="2.3.0",
        git_sha=GIT_SHA,
        wheel_path=wheel,
        built_at=BUILT_AT,
    )
    second = ReleaseManifest.build(
        version="2.3.0",
        git_sha=GIT_SHA,
        wheel_path=wheel,
        built_at="2026-08-01T12:35:56Z",
    )

    assert first.release_id == second.release_id
    assert first.release_id.startswith("compass-2.3.0-aaaaaaaaaaaa-")
    assert first.wheel_sha256.startswith("sha256:")
    assert len(first.wheel_sha256) == 71
    assert first.built_at != second.built_at


def test_from_json_requires_utf8_object_bytes():
    with pytest.raises(ReleaseManifestError, match="invalid_json"):
        ReleaseManifest.from_json_bytes("not bytes")
    with pytest.raises(ReleaseManifestError, match="invalid_json"):
        ReleaseManifest.from_json_bytes(b"[]")
    with pytest.raises(ReleaseManifestError, match="invalid_json"):
        ReleaseManifest.from_json_bytes(b"\xff")
