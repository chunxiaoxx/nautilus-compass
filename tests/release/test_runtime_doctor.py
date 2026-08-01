from __future__ import annotations

import json

import pytest

from release_manifest import ReleaseManifest
from runtime_doctor import (
    DOCTOR_SCHEMA_VERSION,
    DaemonProbe,
    McpProbe,
    ProcessSnapshot,
    PythonProbe,
    build_doctor_report,
    main,
)
from runtime_release import activate_release, stage_release


BUILT_AT = "2026-08-01T16:00:00Z"


def fake_installer(stage_dir, _wheel_path):
    executable = stage_dir / "venv" / "Scripts" / "python.exe"
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


def healthy_probes(active_executable):
    process_provider = lambda: (
        ProcessSnapshot(100, 50, str(active_executable), "2026-08-01T15:59:00Z"),
        ProcessSnapshot(50, 1, "C:/Program Files/Codex/codex.exe", "2026-08-01T15:00:00Z"),
    )
    daemon_probe = lambda: DaemonProbe(True, (27808,), 3.5)
    python_probe = lambda _path: PythonProbe(True, "3.13.13")
    mcp_probe = lambda _arguments, _cwd: McpProbe(True, "2.3.0", 17, 41.2)
    return process_provider, daemon_probe, python_probe, mcp_probe


def test_doctor_reports_exact_active_provenance_and_healthy_ownership(tmp_path):
    runtime_root, manifest, staged = active_runtime(tmp_path)
    probes = healthy_probes(staged.path / "venv" / "Scripts" / "python.exe")

    report = build_doctor_report(
        runtime_root,
        process_provider=probes[0],
        daemon_probe=probes[1],
        python_probe=probes[2],
        mcp_probe=probes[3],
        generated_at=BUILT_AT,
    ).to_mapping()

    assert set(report) == {
        "schema_version",
        "status",
        "active_release",
        "integrity",
        "python",
        "mcp",
        "daemon",
        "processes",
        "default_policy",
        "warnings",
        "generated_at",
    }
    assert report["schema_version"] == DOCTOR_SCHEMA_VERSION
    assert report["status"] == "ok"
    assert report["active_release"] == {
        "release_id": manifest.release_id,
        "version": "2.3.0",
        "git_sha": "a" * 40,
        "manifest_sha256": report["integrity"]["manifest_sha256"],
        "wheel_sha256": manifest.wheel_sha256,
        "active_slot": "a",
        "generation": 1,
    }
    assert report["integrity"]["status"] == "ok"
    assert report["python"] == {"supported": True, "version": "3.13.13"}
    assert report["mcp"]["tool_count"] == 17
    assert report["daemon"]["state"] == "singleton"
    assert report["daemon"]["owner_pids"] == [27808]
    assert report["processes"] == [
        {
            "pid": 100,
            "parent_pid": 50,
            "parent_live": True,
            "client": "codex",
            "executable_release": "active",
            "state": "healthy",
        }
    ]
    assert report["default_policy"] == "flat"
    assert report["warnings"] == []


def test_process_rows_classify_orphan_and_retired_release(tmp_path):
    runtime_root, _manifest, staged = active_runtime(tmp_path)
    active_executable = staged.path / "venv" / "Scripts" / "python.exe"
    retired_executable = runtime_root / "slots" / "b" / "retired" / "venv" / "Scripts" / "python.exe"

    report = build_doctor_report(
        runtime_root,
        process_provider=lambda: (
            ProcessSnapshot(101, 999, str(active_executable), BUILT_AT),
            ProcessSnapshot(102, 50, str(retired_executable), BUILT_AT),
            ProcessSnapshot(50, 1, "C:/Windows/System32/cmd.exe", BUILT_AT),
        ),
        daemon_probe=lambda: DaemonProbe(True, (1, 2), 4.0),
        python_probe=lambda _path: PythonProbe(True, "3.13.13"),
        mcp_probe=lambda _arguments, _cwd: McpProbe(True, "2.3.0", 17, 30.0),
        generated_at=BUILT_AT,
    ).to_mapping()

    assert report["status"] == "degraded"
    assert {item["state"] for item in report["processes"]} == {
        "orphan",
        "retired_release",
    }
    assert report["daemon"]["state"] == "multiple_owners"
    assert set(report["warnings"]) == {
        "daemon_multiple_owners",
        "mcp_orphan_process",
        "mcp_retired_release_process",
    }


def test_absent_runtime_is_blocked_without_fallback(tmp_path):
    report = build_doctor_report(
        tmp_path / "missing",
        process_provider=lambda: (),
        daemon_probe=lambda: DaemonProbe(False, (), None),
        python_probe=lambda _path: pytest.fail("python probe must not run"),
        mcp_probe=lambda _arguments, _cwd: pytest.fail("mcp probe must not run"),
        generated_at=BUILT_AT,
    ).to_mapping()

    assert report["status"] == "blocked"
    assert report["active_release"] is None
    assert report["integrity"]["status"] == "blocked"
    assert report["warnings"] == ["no_active_release"]


def test_report_never_contains_environment_or_command_lines(tmp_path, monkeypatch):
    sentinel = "synthetic-secret-that-must-not-appear"
    monkeypatch.setenv("COMPASS_API_TOKEN", sentinel)
    runtime_root, _manifest, staged = active_runtime(tmp_path)
    probes = healthy_probes(staged.path / "venv" / "Scripts" / "python.exe")

    encoded = json.dumps(
        build_doctor_report(
            runtime_root,
            process_provider=probes[0],
            daemon_probe=probes[1],
            python_probe=probes[2],
            mcp_probe=probes[3],
            generated_at=BUILT_AT,
        ).to_mapping(),
        sort_keys=True,
    )

    assert sentinel not in encoded
    assert "command_line" not in encoded
    assert "environment" not in encoded
    assert "dsn" not in encoded.casefold()


def test_provenance_only_cli_is_json_and_skips_runtime_probes(tmp_path, capsys):
    runtime_root, manifest, _staged = active_runtime(tmp_path)

    result = main(
        [
            "--runtime-root",
            str(runtime_root),
            "--json",
            "--provenance-only",
            "--generated-at",
            BUILT_AT,
        ]
    )

    output = json.loads(capsys.readouterr().out)
    assert result == 0
    assert output["active_release"]["release_id"] == manifest.release_id
    assert output["mcp"]["status"] == "not_probed"
    assert output["daemon"]["state"] == "not_probed"
    assert output["processes"] == []


def test_process_snapshot_rejects_invalid_types():
    with pytest.raises(ValueError, match="invalid_process_snapshot"):
        ProcessSnapshot(True, 1, "python.exe", BUILT_AT)
    with pytest.raises(ValueError, match="invalid_process_snapshot"):
        ProcessSnapshot(1, -1, "python.exe", BUILT_AT)
