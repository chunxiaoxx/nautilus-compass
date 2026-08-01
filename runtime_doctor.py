"""Read-only provenance, integrity, and process diagnostics for Compass."""

from __future__ import annotations

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Sequence, Tuple

from release_manifest import ReleaseManifest, ReleaseManifestError
from runtime_launcher import RuntimeLauncherError, resolve_active_command
from runtime_release import RuntimeReleaseError, load_pointer, verify_slot


DOCTOR_SCHEMA_VERSION = "compass.runtime.doctor.v1"
_UTC_RFC3339_PATTERN = re.compile(
    r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]+)?Z"
)
_PYTHON_VERSION_PATTERN = re.compile(r"Python\s+([0-9]+\.[0-9]+\.[0-9]+)")


@dataclass(frozen=True)
class ProcessSnapshot:
    pid: int
    parent_pid: int
    executable: str
    created_at: Optional[str]

    def __post_init__(self) -> None:
        if (
            isinstance(self.pid, bool)
            or not isinstance(self.pid, int)
            or self.pid <= 0
            or isinstance(self.parent_pid, bool)
            or not isinstance(self.parent_pid, int)
            or self.parent_pid < 0
            or not isinstance(self.executable, str)
            or not self.executable.strip()
            or (self.created_at is not None and not isinstance(self.created_at, str))
        ):
            raise ValueError("invalid_process_snapshot")


@dataclass(frozen=True)
class DaemonProbe:
    reachable: bool
    owner_pids: Tuple[int, ...]
    latency_ms: Optional[float]


@dataclass(frozen=True)
class PythonProbe:
    supported: bool
    version: Optional[str]


@dataclass(frozen=True)
class McpProbe:
    success: bool
    server_version: Optional[str]
    tool_count: Optional[int]
    latency_ms: Optional[float]


@dataclass(frozen=True)
class DoctorReport:
    status: str
    active_release: Optional[Dict[str, Any]]
    integrity: Dict[str, Any]
    python: Dict[str, Any]
    mcp: Dict[str, Any]
    daemon: Dict[str, Any]
    processes: Tuple[Dict[str, Any], ...]
    default_policy: Optional[str]
    warnings: Tuple[str, ...]
    generated_at: str

    def to_mapping(self) -> Dict[str, Any]:
        return {
            "schema_version": DOCTOR_SCHEMA_VERSION,
            "status": self.status,
            "active_release": self.active_release,
            "integrity": self.integrity,
            "python": self.python,
            "mcp": self.mcp,
            "daemon": self.daemon,
            "processes": [dict(item) for item in self.processes],
            "default_policy": self.default_policy,
            "warnings": list(self.warnings),
            "generated_at": self.generated_at,
        }


ProcessProvider = Callable[[], Tuple[ProcessSnapshot, ...]]
DaemonProvider = Callable[[], DaemonProbe]
PythonProvider = Callable[[Path], PythonProbe]
McpProvider = Callable[[Sequence[str], Path], McpProbe]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _validated_timestamp(value: str) -> str:
    if not isinstance(value, str) or _UTC_RFC3339_PATTERN.fullmatch(value) is None:
        raise ValueError("invalid_generated_at")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ValueError("invalid_generated_at") from exc
    if parsed.tzinfo != timezone.utc:
        raise ValueError("invalid_generated_at")
    return value


def _windows_process_provider(max_records: int, timeout: float) -> Tuple[ProcessSnapshot, ...]:
    command = [
        "powershell.exe",
        "-NoProfile",
        "-NonInteractive",
        "-Command",
        "Get-CimInstance Win32_Process | "
        "Select-Object ProcessId,ParentProcessId,ExecutablePath,CreationDate | "
        "ConvertTo-Json -Compress",
    ]
    completed = subprocess.run(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        timeout=timeout,
        check=False,
    )
    if completed.returncode != 0 or len(completed.stdout) > 2 * 1024 * 1024:
        return ()
    try:
        decoded = json.loads(completed.stdout or "[]")
    except json.JSONDecodeError:
        return ()
    rows = decoded if isinstance(decoded, list) else [decoded]
    snapshots = []
    for row in rows[:max_records]:
        if not isinstance(row, dict) or not row.get("ExecutablePath"):
            continue
        try:
            snapshots.append(
                ProcessSnapshot(
                    int(row["ProcessId"]),
                    int(row["ParentProcessId"]),
                    str(row["ExecutablePath"]),
                    str(row["CreationDate"]) if row.get("CreationDate") else None,
                )
            )
        except (KeyError, TypeError, ValueError):
            continue
    return tuple(snapshots)


def _proc_process_provider(max_records: int) -> Tuple[ProcessSnapshot, ...]:
    snapshots = []
    for entry in sorted(Path("/proc").glob("[0-9]*"))[:max_records]:
        try:
            pid = int(entry.name)
            stat = (entry / "stat").read_text(encoding="utf-8").split()
            parent_pid = int(stat[3])
            executable = str((entry / "exe").resolve(strict=True))
            snapshots.append(ProcessSnapshot(pid, parent_pid, executable, None))
        except (OSError, ValueError, IndexError):
            continue
    return tuple(snapshots)


def default_process_provider(
    max_records: int = 4096,
    timeout: float = 5.0,
) -> Tuple[ProcessSnapshot, ...]:
    if os.name == "nt":
        try:
            return _windows_process_provider(max_records, timeout)
        except (OSError, subprocess.SubprocessError):
            return ()
    return _proc_process_provider(max_records)


def _windows_listener_pids(port: int) -> Tuple[int, ...]:
    try:
        completed = subprocess.run(
            ["netstat.exe", "-ano", "-p", "TCP"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return ()
    if completed.returncode != 0:
        return ()
    pids = set()
    suffix = ":{}".format(port)
    for line in completed.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 5 and parts[1].endswith(suffix) and parts[3].upper() == "LISTENING":
            try:
                pids.add(int(parts[4]))
            except ValueError:
                continue
    return tuple(sorted(pids))


def default_daemon_probe(host: str = "127.0.0.1", port: int = 9876) -> DaemonProbe:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=0.75):
            reachable = True
    except OSError:
        reachable = False
    latency = round((time.perf_counter() - started) * 1000, 3)
    owners = _windows_listener_pids(port) if os.name == "nt" else ()
    return DaemonProbe(reachable, owners, latency)


def default_python_probe(executable: Path) -> PythonProbe:
    try:
        completed = subprocess.run(
            [str(executable), "--version"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return PythonProbe(False, None)
    match = _PYTHON_VERSION_PATTERN.search(completed.stdout + completed.stderr)
    if completed.returncode != 0 or match is None:
        return PythonProbe(False, None)
    version = match.group(1)
    major, minor, _patch = (int(part) for part in version.split("."))
    return PythonProbe((major, minor) >= (3, 9), version)


def default_mcp_probe(arguments: Sequence[str], cwd: Path) -> McpProbe:
    requests = (
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "compass-doctor", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
    )
    payload = "".join(json.dumps(item) + "\n" for item in requests)
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            list(arguments),
            input=payload,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=str(cwd),
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return McpProbe(False, None, None, None)
    latency = round((time.perf_counter() - started) * 1000, 3)
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    if completed.returncode != 0 or len(lines) < 2:
        return McpProbe(False, None, None, latency)
    try:
        initialized = json.loads(lines[0])
        listing = json.loads(lines[1])
        version = initialized["result"]["serverInfo"]["version"]
        tools = listing["result"]["tools"]
    except (KeyError, TypeError, json.JSONDecodeError):
        return McpProbe(False, None, None, latency)
    return McpProbe(True, str(version), len(tools), latency)


def _client_name(parent: Optional[ProcessSnapshot]) -> str:
    if parent is None:
        return "unknown"
    name = Path(parent.executable).name.casefold()
    if "codex" in name:
        return "codex"
    if "claude" in name:
        return "claude"
    if name in {"code.exe", "code", "node.exe", "node"}:
        return "vscode"
    if name in {"cmd.exe", "powershell.exe", "pwsh.exe", "bash", "zsh", "sh"}:
        return "shell"
    return "unknown"


def _is_under(path: str, parent: Path) -> bool:
    try:
        Path(path).resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _process_rows(
    runtime_root: Path,
    active_executable: Path,
    snapshots: Tuple[ProcessSnapshot, ...],
) -> Tuple[Dict[str, Any], ...]:
    by_pid = {snapshot.pid: snapshot for snapshot in snapshots}
    slots_root = Path(runtime_root) / "slots"
    active_norm = os.path.normcase(os.path.abspath(str(active_executable)))
    rows = []
    for snapshot in snapshots:
        if not _is_under(snapshot.executable, slots_root):
            continue
        executable_norm = os.path.normcase(os.path.abspath(snapshot.executable))
        parent = by_pid.get(snapshot.parent_pid)
        parent_live = parent is not None
        release_state = "active" if executable_norm == active_norm else "retired"
        if release_state == "retired":
            state = "retired_release"
        elif parent_live:
            state = "healthy"
        else:
            state = "orphan"
        rows.append(
            {
                "pid": snapshot.pid,
                "parent_pid": snapshot.parent_pid,
                "parent_live": parent_live,
                "client": _client_name(parent),
                "executable_release": release_state,
                "state": state,
            }
        )
    return tuple(sorted(rows, key=lambda item: item["pid"]))


def _blocked_report(generated_at: str, reason_code: str) -> DoctorReport:
    return DoctorReport(
        status="blocked",
        active_release=None,
        integrity={"status": "blocked", "reason_code": reason_code},
        python={"supported": False, "version": None},
        mcp={"status": "not_probed", "server_version": None, "tool_count": None, "latency_ms": None},
        daemon={"state": "not_probed", "reachable": None, "owner_pids": [], "latency_ms": None},
        processes=(),
        default_policy=None,
        warnings=(reason_code,),
        generated_at=generated_at,
    )


def build_doctor_report(
    runtime_root: Path,
    process_provider: ProcessProvider = default_process_provider,
    daemon_probe: DaemonProvider = default_daemon_probe,
    python_probe: PythonProvider = default_python_probe,
    mcp_probe: McpProvider = default_mcp_probe,
    generated_at: Optional[str] = None,
    provenance_only: bool = False,
) -> DoctorReport:
    timestamp = _validated_timestamp(generated_at or _now())
    root = Path(runtime_root)
    try:
        resolved = resolve_active_command(root)
        pointer = load_pointer(root)
        if pointer is None:
            return _blocked_report(timestamp, "no_active_release")
        binding = verify_slot(root, pointer.active_slot, pointer.release_id)
        manifest = ReleaseManifest.from_json_bytes(
            (binding.path / "release-manifest.json").read_bytes()
        )
    except RuntimeLauncherError as exc:
        return _blocked_report(timestamp, exc.reason_code)
    except (RuntimeReleaseError, ReleaseManifestError, OSError):
        return _blocked_report(timestamp, "integrity_check_failed")

    active_release = {
        "release_id": manifest.release_id,
        "version": manifest.version,
        "git_sha": manifest.git_sha,
        "manifest_sha256": binding.manifest_sha256,
        "wheel_sha256": manifest.wheel_sha256,
        "active_slot": pointer.active_slot,
        "generation": pointer.generation,
    }
    integrity = {
        "status": "ok",
        "pointer": "ok",
        "manifest": "ok",
        "wheel": "ok",
        "manifest_sha256": binding.manifest_sha256,
    }
    if provenance_only:
        return DoctorReport(
            status="ok",
            active_release=active_release,
            integrity=integrity,
            python={"supported": None, "version": None},
            mcp={"status": "not_probed", "server_version": None, "tool_count": None, "latency_ms": None},
            daemon={"state": "not_probed", "reachable": None, "owner_pids": [], "latency_ms": None},
            processes=(),
            default_policy=manifest.default_policy,
            warnings=(),
            generated_at=timestamp,
        )

    warnings = set()
    python_result = python_probe(binding.python_executable)
    if not python_result.supported:
        warnings.add("python_unsupported")
    mcp_result = mcp_probe(resolved.arguments, root)
    if not mcp_result.success:
        warnings.add("mcp_probe_failed")
        mcp_status = "failed"
    else:
        mcp_status = "ok"
        if mcp_result.tool_count != 17:
            warnings.add("mcp_tool_count_unexpected")
    daemon_result = daemon_probe()
    if not daemon_result.reachable:
        daemon_state = "absent"
        warnings.add("daemon_absent")
    elif len(daemon_result.owner_pids) == 1:
        daemon_state = "singleton"
    elif len(daemon_result.owner_pids) > 1:
        daemon_state = "multiple_owners"
        warnings.add("daemon_multiple_owners")
    else:
        daemon_state = "owner_unknown"
        warnings.add("daemon_owner_unknown")
    try:
        snapshots = process_provider()
    except Exception:
        snapshots = ()
        warnings.add("process_probe_failed")
    process_rows = _process_rows(root, binding.python_executable, tuple(snapshots))
    if any(item["state"] == "orphan" for item in process_rows):
        warnings.add("mcp_orphan_process")
    if any(item["state"] == "retired_release" for item in process_rows):
        warnings.add("mcp_retired_release_process")

    return DoctorReport(
        status="degraded" if warnings else "ok",
        active_release=active_release,
        integrity=integrity,
        python={"supported": python_result.supported, "version": python_result.version},
        mcp={
            "status": mcp_status,
            "server_version": mcp_result.server_version,
            "tool_count": mcp_result.tool_count,
            "latency_ms": mcp_result.latency_ms,
        },
        daemon={
            "state": daemon_state,
            "reachable": daemon_result.reachable,
            "owner_pids": list(daemon_result.owner_pids),
            "latency_ms": daemon_result.latency_ms,
        },
        processes=process_rows,
        default_policy=manifest.default_policy,
        warnings=tuple(sorted(warnings)),
        generated_at=timestamp,
    )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nautilus-compass doctor")
    parser.add_argument("--runtime-root")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--provenance-only", action="store_true")
    parser.add_argument("--generated-at", help=argparse.SUPPRESS)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(list(argv) if argv is not None else None)
    root = Path(
        args.runtime_root
        or os.environ.get("COMPASS_RUNTIME_ROOT", "").strip()
        or (Path.home() / ".nautilus-compass" / "runtime")
    )
    report = build_doctor_report(
        root,
        generated_at=args.generated_at,
        provenance_only=args.provenance_only,
    )
    mapping = report.to_mapping()
    if args.json:
        sys.stdout.write(
            json.dumps(mapping, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
        )
    else:
        release_id = (report.active_release or {}).get("release_id", "none")
        sys.stdout.write("compass_doctor:{}:{}\n".format(report.status, release_id))
    return 2 if report.status == "blocked" else 0


if __name__ == "__main__":
    sys.exit(main())


__all__ = [
    "DOCTOR_SCHEMA_VERSION",
    "DaemonProbe",
    "DoctorReport",
    "McpProbe",
    "ProcessSnapshot",
    "PythonProbe",
    "build_doctor_report",
    "default_daemon_probe",
    "default_mcp_probe",
    "default_process_provider",
    "default_python_probe",
    "main",
]
