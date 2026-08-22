from __future__ import annotations

import hashlib
import json
from pathlib import Path

from doctor import collect_doctor_report, main


_SAME_DAEMON_BYTES = b"same\n"


EXPECTED_KEYS = {
    "schema_version",
    "ready",
    "package_installed",
    "package_version",
    "module_path",
    "python_executable",
    "dependency_import_ok",
    "repository_commit",
    "repository_daemon_hash",
    "plugin_daemon_hash",
    "runtime_daemon_hash",
    "runtime_python_executable",
    "runtime_pid",
    "runtime_source_root",
    "authority_match",
    "daemon_ping_ok",
    "functional_model_ok",
    "reason_codes",
}


def _roots(tmp_path: Path, *, same_bytes: bool = True) -> tuple[Path, Path]:
    repo = tmp_path / "repo"
    plugin = tmp_path / "plugin"
    repo.mkdir()
    plugin.mkdir()
    (repo / "daemon.py").write_bytes(_SAME_DAEMON_BYTES)
    plugin_text = _SAME_DAEMON_BYTES if same_bytes else b"different\n"
    (plugin / "daemon.py").write_bytes(plugin_text)
    return repo, plugin


def _collect(
    tmp_path: Path,
    *,
    same_bytes: bool = True,
    ping_ok: bool = True,
    model_ok: bool = True,
    runtime_hash_matches: bool = True,
) -> dict[str, object]:
    repo, plugin = _roots(tmp_path, same_bytes=same_bytes)
    plugin_hash = f"sha256:{hashlib.sha256((plugin / 'daemon.py').read_bytes()).hexdigest()}"

    def daemon_probe(action: str) -> dict[str, object]:
        if action == "ping":
            return {
                "ok": ping_ok,
                "pong": ping_ok,
                "daemon_hash": plugin_hash if runtime_hash_matches else f"sha256:{'0' * 64}",
                "python_executable": "python-for-test",
                "pid": 123,
                "source_root": str(plugin.resolve()),
            }
        return {"ok": model_ok, "scores": [1.0] if model_ok else []}

    return collect_doctor_report(
        repo_root=repo,
        plugin_root=plugin,
        python_executable="python-for-test",
        package_probe=lambda: (True, "2.3.1", "/installed/nautilus_compass"),
        dependency_probe=lambda _python: (True, None),
        repository_probe=lambda _repo: "a" * 40,
        daemon_probe=daemon_probe,
    )


def test_report_has_exact_schema_and_is_ready_when_all_checks_pass(tmp_path: Path) -> None:
    report = _collect(tmp_path)

    assert set(report) == EXPECTED_KEYS
    assert report["schema_version"] == "compass.doctor.v2"
    assert report["ready"] is True
    assert report["reason_codes"] == []


def test_ping_without_functional_model_is_not_ready(tmp_path: Path) -> None:
    report = _collect(tmp_path, ping_ok=True, model_ok=False)

    assert report["daemon_ping_ok"] is True
    assert report["functional_model_ok"] is False
    assert report["ready"] is False
    assert report["reason_codes"] == ["functional_model_failed"]


def test_repository_and_plugin_hash_mismatch_is_not_ready(tmp_path: Path) -> None:
    report = _collect(tmp_path, same_bytes=False)

    assert report["authority_match"] is False
    assert report["ready"] is False
    assert report["reason_codes"] == ["runtime_authority_mismatch"]


def test_runtime_hash_mismatch_is_not_ready(tmp_path: Path) -> None:
    report = _collect(tmp_path, runtime_hash_matches=False)

    assert report["authority_match"] is False
    assert report["ready"] is False
    assert report["reason_codes"] == ["runtime_authority_mismatch"]


def test_probe_does_not_modify_daemon_files(tmp_path: Path) -> None:
    repo, plugin = _roots(tmp_path)
    before = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (repo / "daemon.py", plugin / "daemon.py")
    }

    collect_doctor_report(
        repo_root=repo,
        plugin_root=plugin,
        python_executable="python-for-test",
        package_probe=lambda: (True, "2.3.1", "/installed/nautilus_compass"),
        dependency_probe=lambda _python: (True, None),
        repository_probe=lambda _repo: "a" * 40,
        daemon_probe=lambda action: (
            {
                "ok": True,
                "pong": True,
                "daemon_hash": f"sha256:{hashlib.sha256(_SAME_DAEMON_BYTES).hexdigest()}",
                "python_executable": "python-for-test",
                "pid": 123,
                "source_root": str(plugin.resolve()),
            }
            if action == "ping"
            else {"ok": True, "scores": [1.0]}
        ),
    )

    after = {
        path: (path.read_bytes(), path.stat().st_mtime_ns)
        for path in (repo / "daemon.py", plugin / "daemon.py")
    }
    assert after == before


def test_json_cli_returns_nonzero_for_unready_report(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "doctor.collect_doctor_report",
        lambda: (
            {key: ([] if key == "reason_codes" else None) for key in EXPECTED_KEYS}
            | {
                "schema_version": "compass.doctor.v2",
                "ready": False,
                "reason_codes": ["functional_model_failed"],
            }
        ),
    )

    assert main(["--json"]) == 1
    report = json.loads(capsys.readouterr().out)
    assert report["ready"] is False
    assert report["reason_codes"] == ["functional_model_failed"]
