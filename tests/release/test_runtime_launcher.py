from __future__ import annotations

import json
from pathlib import Path

import pytest

from release_manifest import ReleaseManifest
from runtime_launcher import (
    RuntimeLauncherError,
    execute_resolved,
    main,
    resolve_active_command,
)
from runtime_release import activate_release, stage_release


BUILT_AT = "2026-08-01T14:00:00Z"


def fake_installer(stage_dir, _wheel_path):
    relative = Path("venv") / "Scripts" / "python.exe"
    executable = stage_dir / relative
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"fake-python")
    return executable


def active_runtime(tmp_path):
    candidate = tmp_path / "candidate"
    candidate.mkdir()
    wheel = candidate / "nautilus_compass-2.3.0-py3-none-any.whl"
    wheel.write_bytes(b"wheel")
    manifest = ReleaseManifest.build(
        version="2.3.0",
        git_sha="a" * 40,
        wheel_path=wheel,
        built_at=BUILT_AT,
    )
    manifest_path = candidate / "release-manifest.json"
    manifest_path.write_bytes(manifest.canonical_bytes())
    runtime_root = tmp_path / "runtime"
    staged = stage_release(
        runtime_root,
        manifest_path,
        wheel,
        installer=fake_installer,
        created_at=BUILT_AT,
    )
    activate_release(runtime_root, staged.release_id, created_at=BUILT_AT)
    return runtime_root, manifest, staged


def test_valid_runtime_resolves_only_active_slot(tmp_path):
    runtime_root, manifest, staged = active_runtime(tmp_path)

    resolved = resolve_active_command(runtime_root)

    assert resolved.release_id == manifest.release_id
    assert resolved.executable == staged.path / "venv" / "Scripts" / "python.exe"
    assert resolved.arguments == (
        str(resolved.executable),
        "-m",
        "nautilus_compass.mcp_server",
    )
    assert resolved.default_policy == "flat"
    assert resolved.manifest_sha256.startswith("sha256:")


@pytest.mark.parametrize(
    ("mutation", "reason_code"),
    [
        ("remove_pointer", "no_active_release"),
        ("remove_manifest", "slot_manifest_invalid"),
        ("change_wheel", "slot_wheel_mismatch"),
        ("remove_python", "slot_python_missing"),
    ],
)
def test_invalid_runtime_never_falls_back_to_source(tmp_path, mutation, reason_code):
    runtime_root, manifest, staged = active_runtime(tmp_path)
    if mutation == "remove_pointer":
        (runtime_root / "current.json").unlink()
    elif mutation == "remove_manifest":
        (staged.path / "release-manifest.json").unlink()
    elif mutation == "change_wheel":
        (staged.path / manifest.wheel_filename).write_bytes(b"changed")
    elif mutation == "remove_python":
        (staged.path / "venv" / "Scripts" / "python.exe").unlink()

    with pytest.raises(RuntimeLauncherError, match=reason_code):
        resolve_active_command(runtime_root)


def test_pointer_binding_mismatch_is_rejected(tmp_path):
    runtime_root, _manifest, _staged = active_runtime(tmp_path)
    pointer_path = runtime_root / "current.json"
    pointer = json.loads(pointer_path.read_text(encoding="utf-8"))
    pointer["manifest_sha256"] = "sha256:" + "f" * 64
    pointer_path.write_text(json.dumps(pointer), encoding="utf-8")

    with pytest.raises(RuntimeLauncherError, match="active_pointer_mismatch"):
        resolve_active_command(runtime_root)


def test_execute_passes_argument_list_to_injected_executor(tmp_path):
    runtime_root, _manifest, _staged = active_runtime(tmp_path)
    resolved = resolve_active_command(runtime_root)
    observed = {}

    def executor(arguments):
        observed["arguments"] = arguments
        return 7

    result = execute_resolved(resolved, executor=executor)

    assert result == 7
    assert observed["arguments"] == list(resolved.arguments)
    assert all(isinstance(value, str) for value in observed["arguments"])


def test_dry_run_json_reports_binding_without_starting_process(tmp_path, capsys):
    runtime_root, manifest, _staged = active_runtime(tmp_path)

    result = main(
        ["--runtime-root", str(runtime_root), "--dry-run", "--json"]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["release_id"] == manifest.release_id
    assert output["arguments"][1:] == ["-m", "nautilus_compass.mcp_server"]
    assert set(output) == {
        "schema_version",
        "release_id",
        "manifest_sha256",
        "default_policy",
        "executable",
        "arguments",
    }


def test_runtime_root_can_come_from_environment(tmp_path, monkeypatch, capsys):
    runtime_root, manifest, _staged = active_runtime(tmp_path)
    monkeypatch.setenv("COMPASS_RUNTIME_ROOT", str(runtime_root))

    assert main(["--dry-run", "--json"]) == 0

    assert json.loads(capsys.readouterr().out)["release_id"] == manifest.release_id


def test_controlled_error_never_echoes_environment(tmp_path, monkeypatch, capsys):
    sentinel = "synthetic-secret-that-must-not-appear"
    monkeypatch.setenv("COMPASS_API_TOKEN", sentinel)

    result = main(
        ["--runtime-root", str(tmp_path / "missing"), "--dry-run", "--json"]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert captured.out == ""
    assert captured.err.strip() == "compass_runtime_error:no_active_release"
    assert sentinel not in captured.err


def test_json_flag_without_dry_run_is_rejected(tmp_path, capsys):
    runtime_root, _manifest, _staged = active_runtime(tmp_path)

    result = main(["--runtime-root", str(runtime_root), "--json"])

    assert result == 2
    assert capsys.readouterr().err.strip() == "compass_runtime_error:json_requires_dry_run"
