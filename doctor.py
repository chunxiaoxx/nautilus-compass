"""Read-only readiness probe for the installed Compass runtime."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import os
import re
import socket
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "compass.doctor.v2"
_PACKAGE_NAME = "nautilus-compass"
_DAEMON_FILE = "daemon.py"

PackageProbe = Callable[[], tuple[bool, str, str]]
DependencyProbe = Callable[[str], tuple[bool, str | None]]
RepositoryProbe = Callable[[Path], str | None]
DaemonProbe = Callable[[str], dict[str, object]]


def collect_doctor_report(
    *,
    repo_root: Path | None = None,
    plugin_root: Path | None = None,
    python_executable: str | None = None,
    package_probe: PackageProbe | None = None,
    dependency_probe: DependencyProbe | None = None,
    repository_probe: RepositoryProbe | None = None,
    daemon_probe: DaemonProbe | None = None,
) -> dict[str, object]:
    """Collect exact runtime facts without changing files or processes."""

    repository = (repo_root or Path(__file__).resolve().parent).resolve()
    plugin = (
        plugin_root
        or Path(
            os.environ.get(
                "COMPASS_PLUGIN_DIR",
                Path.home() / ".claude" / "plugins" / "nautilus-compass",
            )
        )
    ).resolve()
    interpreter = python_executable or sys.executable

    installed, package_version, module_path = (package_probe or _probe_package)()
    dependency_ok, _dependency_error = (dependency_probe or _probe_dependencies)(interpreter)
    repository_commit = (repository_probe or _probe_repository)(repository)
    repository_hash = _hash_file(repository / _DAEMON_FILE)
    plugin_hash = _hash_file(plugin / _DAEMON_FILE)
    source_authority_match = (
        repository_hash is not None and plugin_hash is not None and repository_hash == plugin_hash
    )
    probe = daemon_probe or _probe_daemon
    ping_response = probe("ping")
    ping_ok = ping_response.get("ok") is True and ping_response.get("pong") is True
    model_response = probe("score") if ping_ok else {}
    scores = model_response.get("scores")
    model_ok = (
        model_response.get("ok") is True
        and isinstance(scores, list)
        and len(scores) == 1
        and isinstance(scores[0], (int, float))
    )
    runtime_hash = _optional_string(ping_response.get("daemon_hash"))
    runtime_python = _optional_string(ping_response.get("python_executable"))
    runtime_source_root = _optional_string(ping_response.get("source_root"))
    runtime_pid = ping_response.get("pid") if isinstance(ping_response.get("pid"), int) else None
    runtime_authority_match = (
        ping_ok
        and plugin_hash is not None
        and runtime_hash == plugin_hash
        and _same_path(runtime_python, interpreter)
        and _same_path(runtime_source_root, str(plugin))
    )
    authority_match = source_authority_match and runtime_authority_match

    reasons = []
    if not installed:
        reasons.append("package_not_installed")
    if not dependency_ok:
        reasons.append("dependency_import_failed")
    if repository_commit is None:
        reasons.append("repository_unavailable")
    if plugin_hash is None:
        reasons.append("plugin_runtime_missing")
    elif not source_authority_match or (ping_ok and not runtime_authority_match):
        reasons.append("runtime_authority_mismatch")
    if not ping_ok:
        reasons.append("daemon_ping_failed")
    elif not model_ok:
        reasons.append("functional_model_failed")

    return {
        "schema_version": SCHEMA_VERSION,
        "ready": not reasons,
        "package_installed": installed,
        "package_version": package_version,
        "module_path": module_path,
        "python_executable": interpreter,
        "dependency_import_ok": dependency_ok,
        "repository_commit": repository_commit,
        "repository_daemon_hash": repository_hash,
        "plugin_daemon_hash": plugin_hash,
        "runtime_daemon_hash": runtime_hash,
        "runtime_python_executable": runtime_python,
        "runtime_pid": runtime_pid,
        "runtime_source_root": runtime_source_root,
        "authority_match": authority_match,
        "daemon_ping_ok": ping_ok,
        "functional_model_ok": model_ok,
        "reason_codes": reasons,
    }


def _optional_string(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _same_path(left: str | None, right: str | None) -> bool:
    if not left or not right:
        return False
    try:
        return os.path.normcase(os.path.realpath(left)) == os.path.normcase(os.path.realpath(right))
    except OSError:
        return False


def _probe_package() -> tuple[bool, str, str]:
    module_path = str(Path(__file__).resolve())
    try:
        return True, importlib.metadata.version(_PACKAGE_NAME), module_path
    except importlib.metadata.PackageNotFoundError:
        return False, _source_version(), module_path


def _source_version() -> str:
    init_path = Path(__file__).resolve().parent / "__init__.py"
    try:
        match = re.search(
            r'__version__\s*=\s*["\']([^"\']+)',
            init_path.read_text(encoding="utf-8"),
        )
    except OSError:
        return "unknown"
    return match.group(1) if match else "unknown"


def _probe_dependencies(interpreter: str) -> tuple[bool, str | None]:
    try:
        completed = subprocess.run(
            [
                interpreter,
                "-c",
                "import torch; import sentence_transformers",
            ],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return False, type(exc).__name__
    if completed.returncode == 0:
        return True, None
    error = (completed.stderr or completed.stdout).strip().splitlines()
    return False, error[-1] if error else "dependency_import_failed"


def _probe_repository(repo_root: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo_root), "rev-parse", "HEAD"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    commit = completed.stdout.strip()
    return commit if completed.returncode == 0 and re.fullmatch(r"[0-9a-f]{40}", commit) else None


def _hash_file(path: Path) -> str | None:
    try:
        return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"
    except OSError:
        return None


def _probe_daemon(action: str) -> dict[str, object]:
    payload: dict[str, Any] = {"action": action}
    if action == "score":
        payload.update(
            {
                "query": "compass doctor functional model probe",
                "candidates": ["compass doctor functional model probe"],
            }
        )
    try:
        with socket.create_connection(("127.0.0.1", 9876), timeout=3) as connection:
            connection.settimeout(30)
            connection.sendall(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n")
            response = b""
            while b"\n" not in response and len(response) <= 1024 * 1024:
                chunk = connection.recv(8192)
                if not chunk:
                    break
                response += chunk
        decoded = json.loads(response.partition(b"\n")[0].decode("utf-8"))
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
        return {"ok": False, "error": type(exc).__name__}
    return decoded if isinstance(decoded, dict) else {"ok": False, "error": "invalid_response"}


def _print_human(report: dict[str, object]) -> None:
    state = "READY" if report["ready"] else "NOT READY"
    print(f"Compass doctor: {state}")
    print(f"  package: {report['package_version']} installed={report['package_installed']}")
    print(f"  python: {report['python_executable']}")
    print(f"  daemon: ping={report['daemon_ping_ok']} model={report['functional_model_ok']}")
    print(f"  authority_match: {report['authority_match']}")
    if report["reason_codes"]:
        print(f"  blockers: {', '.join(report['reason_codes'])}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="nautilus-compass doctor")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    report = collect_doctor_report()
    if args.as_json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        _print_human(report)
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["SCHEMA_VERSION", "collect_doctor_report", "main"]
