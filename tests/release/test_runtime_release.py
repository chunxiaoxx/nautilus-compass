from __future__ import annotations

import json
import threading
import time

import pytest

from release_manifest import ReleaseManifest
from runtime_release import (
    POINTER_SCHEMA_VERSION,
    RECEIPT_SCHEMA_VERSION,
    RuntimePointer,
    RuntimeReleaseError,
    activate_release,
    load_pointer,
    rollback_release,
    stage_release,
    verify_slot,
)
from tests.release.wheel_fixture import extract_test_wheel, write_test_wheel


GIT_SHA_1 = "1" * 40
GIT_SHA_2 = "2" * 40
BUILT_AT_1 = "2026-08-01T12:00:00Z"
BUILT_AT_2 = "2026-08-01T12:01:00Z"


def make_candidate(tmp_path, name, version, git_sha, payload, built_at):
    candidate = tmp_path / name
    candidate.mkdir()
    wheel = candidate / f"nautilus_compass-{version}-py3-none-any.whl"
    write_test_wheel(wheel, payload)
    manifest = ReleaseManifest.build(
        version=version,
        git_sha=git_sha,
        wheel_path=wheel,
        built_at=built_at,
    )
    manifest_path = candidate / "release-manifest.json"
    manifest_path.write_bytes(manifest.canonical_bytes())
    return manifest, manifest_path, wheel


def fake_installer(stage_dir, _wheel_path):
    return extract_test_wheel(stage_dir, _wheel_path)


def receipt_mappings(runtime_root):
    return [
        json.loads(path.read_text(encoding="utf-8"))
        for path in sorted((runtime_root / "receipts").glob("*.json"))
    ]


def test_pointer_rejects_unknown_keys_and_invalid_types():
    valid = {
        "schema_version": POINTER_SCHEMA_VERSION,
        "active_slot": "a",
        "release_id": "compass-2.3.0-111111111111-aaaaaaaaaaaa",
        "manifest_sha256": "sha256:" + "a" * 64,
        "generation": 1,
    }

    assert RuntimePointer.from_mapping(valid).to_mapping() == valid
    with pytest.raises(RuntimeReleaseError, match="invalid_pointer_keys"):
        RuntimePointer.from_mapping(dict(valid, extra=True))
    with pytest.raises(RuntimeReleaseError, match="invalid_pointer"):
        RuntimePointer.from_mapping(dict(valid, generation=True))
    with pytest.raises(RuntimeReleaseError, match="invalid_pointer"):
        RuntimePointer.from_mapping(dict(valid, active_slot="c"))


def test_initial_stage_uses_slot_a_and_is_idempotent(tmp_path):
    runtime_root = tmp_path / "runtime"
    manifest, manifest_path, wheel = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )

    first = stage_release(
        runtime_root,
        manifest_path,
        wheel,
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    second = stage_release(
        runtime_root,
        manifest_path,
        wheel,
        installer=fake_installer,
        created_at=BUILT_AT_2,
    )

    assert first.slot == "a"
    assert first.release_id == manifest.release_id
    assert first.idempotent is False
    assert second == first.as_idempotent()
    assert (first.path / "release-manifest.json").read_bytes() == manifest.canonical_bytes()
    assert (first.path / manifest.wheel_filename).read_bytes() == wheel.read_bytes()
    assert (first.path / "venv" / "Scripts" / "python.exe").is_file()
    assert load_pointer(runtime_root) is None
    assert [item["status"] for item in receipt_mappings(runtime_root)] == ["verified"]


def test_active_a_stages_next_candidate_only_to_b(tmp_path):
    runtime_root = tmp_path / "runtime"
    first = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    second = make_candidate(
        tmp_path, "two", "2.3.1", GIT_SHA_2, b"wheel-two", BUILT_AT_2
    )
    staged_first = stage_release(
        runtime_root, first[1], first[2], installer=fake_installer, created_at=BUILT_AT_1
    )
    activate_release(runtime_root, staged_first.release_id, created_at=BUILT_AT_1)

    staged_second = stage_release(
        runtime_root, second[1], second[2], installer=fake_installer, created_at=BUILT_AT_2
    )

    assert staged_second.slot == "b"
    assert load_pointer(runtime_root).release_id == first[0].release_id


def test_changed_wheel_is_rejected_before_slot_mutation(tmp_path):
    runtime_root = tmp_path / "runtime"
    manifest, manifest_path, wheel = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    wheel.write_bytes(b"tampered")

    with pytest.raises(RuntimeReleaseError, match="wheel_hash_mismatch"):
        stage_release(
            runtime_root,
            manifest_path,
            wheel,
            installer=fake_installer,
            created_at=BUILT_AT_1,
        )

    assert not (runtime_root / "slots").exists()
    assert load_pointer(runtime_root) is None
    assert manifest.release_id not in repr(receipt_mappings(runtime_root))


def test_failed_installer_leaves_current_pointer_untouched(tmp_path):
    runtime_root = tmp_path / "runtime"
    first = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    second = make_candidate(
        tmp_path, "two", "2.3.1", GIT_SHA_2, b"wheel-two", BUILT_AT_2
    )
    staged = stage_release(
        runtime_root, first[1], first[2], installer=fake_installer, created_at=BUILT_AT_1
    )
    before = activate_release(
        runtime_root, staged.release_id, created_at=BUILT_AT_1
    )

    def failing_installer(_stage_dir, _wheel_path):
        raise RuntimeError("synthetic installer failure")

    with pytest.raises(RuntimeReleaseError, match="installer_failed"):
        stage_release(
            runtime_root,
            second[1],
            second[2],
            installer=failing_installer,
            created_at=BUILT_AT_2,
        )

    assert load_pointer(runtime_root) == before
    assert not (runtime_root / "slots" / "b" / second[0].release_id).exists()
    assert receipt_mappings(runtime_root)[-1]["status"] == "blocked"
    assert "synthetic installer failure" not in repr(receipt_mappings(runtime_root))


def test_existing_conflicting_slot_fails_closed(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    (staged.path / candidate[0].wheel_filename).write_bytes(
        b"changed after verification"
    )

    with pytest.raises(RuntimeReleaseError, match="slot_conflict"):
        stage_release(
            runtime_root,
            candidate[1],
            candidate[2],
            installer=fake_installer,
            created_at=BUILT_AT_2,
        )


def test_activation_is_atomic_and_records_previous_binding(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )

    pointer = activate_release(
        runtime_root, staged.release_id, created_at=BUILT_AT_1
    )

    assert pointer.active_slot == "a"
    assert pointer.release_id == staged.release_id
    assert pointer.generation == 1
    assert load_pointer(runtime_root) == pointer
    assert not (runtime_root / "previous.json").exists()
    activation = receipt_mappings(runtime_root)[-1]
    assert activation["operation"] == "activate"
    assert activation["previous_release_id"] is None
    assert activation["status"] == "active"


def test_second_activation_then_rollback_restores_without_installer(tmp_path):
    runtime_root = tmp_path / "runtime"
    first = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    second = make_candidate(
        tmp_path, "two", "2.3.1", GIT_SHA_2, b"wheel-two", BUILT_AT_2
    )
    staged_first = stage_release(
        runtime_root, first[1], first[2], installer=fake_installer, created_at=BUILT_AT_1
    )
    active_first = activate_release(
        runtime_root, staged_first.release_id, created_at=BUILT_AT_1
    )
    staged_second = stage_release(
        runtime_root, second[1], second[2], installer=fake_installer, created_at=BUILT_AT_2
    )
    active_second = activate_release(
        runtime_root, staged_second.release_id, created_at=BUILT_AT_2
    )

    rolled_back = rollback_release(
        runtime_root, created_at="2026-08-01T12:02:00Z"
    )

    assert active_first.active_slot == "a"
    assert active_second.active_slot == "b"
    assert active_second.generation == 2
    assert rolled_back.active_slot == "a"
    assert rolled_back.release_id == active_first.release_id
    assert rolled_back.manifest_sha256 == active_first.manifest_sha256
    assert rolled_back.generation == 3
    assert load_pointer(runtime_root) == rolled_back
    assert receipt_mappings(runtime_root)[-1]["operation"] == "rollback"


def test_tampered_staged_manifest_cannot_activate(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    mapping = json.loads((staged.path / "release-manifest.json").read_text())
    mapping["built_at"] = BUILT_AT_2
    (staged.path / "release-manifest.json").write_text(json.dumps(mapping), encoding="utf-8")

    with pytest.raises(RuntimeReleaseError, match="slot_manifest_mismatch"):
        activate_release(runtime_root, staged.release_id, created_at=BUILT_AT_2)

    assert load_pointer(runtime_root) is None


def test_receipts_have_exact_non_secret_schema(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    activate_release(runtime_root, staged.release_id, created_at=BUILT_AT_1)

    expected_keys = {
        "schema_version",
        "operation",
        "release_id",
        "manifest_sha256",
        "previous_release_id",
        "generation",
        "status",
        "reason_code",
        "created_at",
    }
    for mapping in receipt_mappings(runtime_root):
        assert set(mapping) == expected_keys
        assert mapping["schema_version"] == RECEIPT_SCHEMA_VERSION
        assert not set(mapping).intersection(
            {"password", "token", "dsn", "environment", "command_line", "user"}
        )


def test_verify_slot_rejects_unknown_slot_record_keys(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    slot_record_path = staged.path / "slot.json"
    mapping = json.loads(slot_record_path.read_text(encoding="utf-8"))
    mapping["unknown"] = "blocked"
    slot_record_path.write_text(json.dumps(mapping), encoding="utf-8")

    with pytest.raises(RuntimeReleaseError, match="invalid_slot_record_keys"):
        verify_slot(runtime_root, "a", staged.release_id)


def test_verify_slot_rejects_tampered_installed_package(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    installed = (
        staged.path / "venv" / "Lib" / "site-packages" / "nautilus_compass" / "__init__.py"
    )
    installed.write_text("PAYLOAD = b'tampered'\n", encoding="utf-8")

    with pytest.raises(RuntimeReleaseError, match="slot_install_mismatch"):
        verify_slot(runtime_root, "a", staged.release_id)


@pytest.mark.parametrize(
    "relative_path",
    (
        "venv/Lib/site-packages/compass-shadow.pth",
        "venv/Lib/site-packages/sitecustomize.py",
        "venv/Lib/site-packages/sitecustomize/__init__.py",
        "venv/Lib/site-packages/usercustomize/__init__.py",
        "venv/Lib/site-packages/nautilus_compass/shadow.py",
    ),
)
def test_verify_slot_rejects_untracked_executable_install_files(tmp_path, relative_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    injected = staged.path / relative_path
    injected.parent.mkdir(parents=True, exist_ok=True)
    injected.write_text("raise RuntimeError('shadowed')\n", encoding="utf-8")

    with pytest.raises(RuntimeReleaseError, match="slot_install_mismatch"):
        verify_slot(runtime_root, "a", staged.release_id)


def test_verify_slot_rejects_tampered_python_executable(tmp_path):
    runtime_root = tmp_path / "runtime"
    candidate = make_candidate(
        tmp_path, "one", "2.3.0", GIT_SHA_1, b"wheel-one", BUILT_AT_1
    )
    staged = stage_release(
        runtime_root,
        candidate[1],
        candidate[2],
        installer=fake_installer,
        created_at=BUILT_AT_1,
    )
    executable = staged.path / "venv" / "Scripts" / "python.exe"
    executable.write_bytes(b"tampered-python")

    with pytest.raises(RuntimeReleaseError, match="slot_python_mismatch"):
        verify_slot(runtime_root, "a", staged.release_id)


def test_transition_lock_serializes_release_mutations(tmp_path):
    from runtime_release import _transition_lock

    observed = []

    def worker(name):
        with _transition_lock(tmp_path / "runtime"):
            observed.append(f"{name}:start")
            time.sleep(0.05)
            observed.append(f"{name}:end")

    first = threading.Thread(target=worker, args=("first",))
    second = threading.Thread(target=worker, args=("second",))
    first.start()
    time.sleep(0.01)
    second.start()
    first.join(timeout=2)
    second.join(timeout=2)

    assert observed == ["first:start", "first:end", "second:start", "second:end"]
