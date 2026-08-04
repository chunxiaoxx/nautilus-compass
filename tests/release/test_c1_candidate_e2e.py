from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import threading
import venv
from pathlib import Path

from release_manifest import ReleaseManifest
from release_security import scan_release_surfaces, scan_wheel
from runtime_doctor import build_doctor_report
from runtime_release import (
    activate_release,
    rollback_release,
    stage_release,
    verify_slot,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
INSTALLED_PLUGIN = Path.home() / ".claude" / "plugins" / "nautilus-compass"
PACKAGING_INPUT_PATHS = (
    "pyproject.toml",
    "README.md",
    "LICENSE",
    "LICENSE-ANCHORS",
    ":(top,glob)*.py",
    ":(top,glob)anchors*.json",
    ":(top,glob)*.sh",
    "gep",
    "sdk",
    "middleware",
    "storage",
    "proof",
    "drift",
    "recall_pkg",
    "skills_pkg",
    "judges",
    "mcp_durable",
    "benchmarks",
)
BUILT_AT_1 = "2026-08-04T12:00:00Z"
BUILT_AT_2 = "2026-08-04T12:01:00Z"


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 300,
    input_text: str | None = None,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        input=input_text,
        env=env,
        text=True,
        stdin=None if input_text is not None else subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    assert completed.returncode == 0, (
        f"command failed with exit code {completed.returncode}: {command!r}; "
        "captured output omitted"
    )
    return completed


def _venv_python(root: Path) -> Path:
    return root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")


def _source_snapshot(tmp_path: Path) -> tuple[Path, str]:
    status = _run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "status",
            "--porcelain=v1",
            "--untracked-files=all",
            "--",
            *PACKAGING_INPUT_PATHS,
        ],
        cwd=tmp_path,
    )
    assert not status.stdout.strip(), "packaging inputs must be committed before build"
    git_sha = _run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", "HEAD"], cwd=tmp_path
    ).stdout.strip()
    archive = tmp_path / "source.zip"
    source = tmp_path / "source"
    source.mkdir()
    _run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "archive",
            "--format=zip",
            f"--output={archive}",
            "HEAD",
            "--",
            *PACKAGING_INPUT_PATHS,
        ],
        cwd=tmp_path,
    )
    shutil.unpack_archive(archive, source, format="zip")
    assert scan_release_surfaces(source) == ()
    return source, git_sha


def _build_wheel(
    builder_python: Path,
    source: Path,
    wheelhouse: Path,
    source_date_epoch: str,
) -> Path:
    wheelhouse.mkdir()
    env = os.environ.copy()
    env["SOURCE_DATE_EPOCH"] = source_date_epoch
    _run(
        [
            str(builder_python),
            "-m",
            "pip",
            "--disable-pip-version-check",
            "wheel",
            "--no-cache-dir",
            "--no-deps",
            "--wheel-dir",
            str(wheelhouse),
            str(source),
        ],
        cwd=wheelhouse.parent,
        env=env,
    )
    wheels = tuple(wheelhouse.glob("nautilus_compass-*.whl"))
    assert len(wheels) == 1
    assert scan_wheel(wheels[0]) == ()
    return wheels[0]


def _write_manifest(
    directory: Path,
    wheel: Path,
    git_sha: str,
    built_at: str,
) -> tuple[ReleaseManifest, Path]:
    manifest = ReleaseManifest.build("2.3.0", git_sha, wheel, built_at)
    path = directory / "release-manifest.json"
    path.write_bytes(manifest.canonical_bytes())
    return manifest, path


def _assert_installed_imports(binding_path: Path, python: Path) -> dict[str, object]:
    outside = binding_path.parent.parent.parent / "outside"
    outside.mkdir(exist_ok=True)
    script = (
        "import json,gep,nautilus_compass.mcp_server as m;"
        "import benchmarks.learning_kernel_r0.cli as l;"
        "from pathlib import Path;"
        "bundle=l.load_fixture(Path(l.__file__).resolve().parent/'fixtures'/'r0');"
        "summary=l.summarize_results(bundle,l.run_fixture(bundle));"
        "print(json.dumps({'gep':gep.__file__,'mcp':m.__file__,'r0':l.__file__,"
        "'version':m.SERVER_VERSION,'candidate_state':summary['decision']['candidate_state'],"
        "'runtime':summary['runtime_recommendation'],"
        "'improvement_claim':summary['improvement_claim']}))"
    )
    result = _run([str(python), "-I", "-B", "-c", script], cwd=outside, timeout=30)
    paths = json.loads(result.stdout)
    for key in ("gep", "mcp", "r0"):
        resolved = Path(paths[key]).resolve()
        resolved.relative_to(binding_path.resolve())
        assert REPO_ROOT.resolve() not in resolved.parents
        assert INSTALLED_PLUGIN.resolve() not in resolved.parents
    assert paths["version"] == "2.3.0"
    assert paths["candidate_state"] == "candidate_only"
    assert paths["runtime"] == "flat"
    assert paths["improvement_claim"] is False
    return paths


def _serve_one_recall(requests: list[dict]) -> tuple[socket.socket, int, threading.Thread]:
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("127.0.0.1", 0))
    server.listen(1)
    server.settimeout(15)
    port = int(server.getsockname()[1])

    def serve() -> None:
        try:
            connection, _address = server.accept()
            with connection:
                payload = b""
                while not payload.endswith(b"\n"):
                    chunk = connection.recv(65536)
                    if not chunk:
                        break
                    payload += chunk
                request = json.loads(payload.decode("utf-8"))
                requests.append(request)
                response = {
                    "ok": True,
                    "recall": [
                        {
                            "score": 0.99,
                            "age_str": "0s",
                            "path": "c1-candidate-memory.md",
                            "description": "isolated C1 recall marker",
                        }
                    ],
                    "fresh_extra": [],
                }
                connection.sendall((json.dumps(response) + "\n").encode("utf-8"))
        except OSError:
            return
        finally:
            server.close()

    thread = threading.Thread(target=serve, daemon=True)
    thread.start()
    return server, port, thread


def _mcp_recall_smoke(arguments: tuple[str, ...], cwd: Path) -> tuple[int, list[dict]]:
    requests: list[dict] = []
    server, port, thread = _serve_one_recall(requests)
    messages = (
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "c1-e2e", "version": "1"},
            },
        },
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "recall",
                "arguments": {"query": "C1 marker", "project": "c1-e2e", "top_k": 1},
            },
        },
    )
    env = os.environ.copy()
    env.pop("PYTHONPATH", None)
    env["COMPASS_DAEMON_PORT"] = str(port)
    try:
        result = _run(
            list(arguments),
            cwd=cwd,
            timeout=20,
            input_text="".join(json.dumps(message) + "\n" for message in messages),
            env=env,
        )
    finally:
        thread.join(timeout=2)
        server.close()
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    assert len(replies) == 3
    tool_count = len(replies[1]["result"]["tools"])
    recall_text = replies[2]["result"]["content"][0]["text"]
    assert "isolated C1 recall marker" in recall_text
    assert requests == [
        {
            "action": "recall",
            "query": "C1 marker",
            "top_k": 1,
            "scope": "project",
            "project": "c1-e2e",
        }
    ]
    return tool_count, replies


def test_c1_installed_wheel_dual_slot_switch_and_rollback(tmp_path: Path) -> None:
    source, git_sha = _source_snapshot(tmp_path)
    builder = tmp_path / "builder"
    venv.EnvBuilder(with_pip=True).create(builder)
    builder_python = _venv_python(builder)
    wheel_a = _build_wheel(builder_python, source, tmp_path / "wheel-a", "1700000000")
    wheel_b = _build_wheel(builder_python, source, tmp_path / "wheel-b", "1700000004")
    assert wheel_a.read_bytes() != wheel_b.read_bytes()

    manifest_a, manifest_path_a = _write_manifest(
        wheel_a.parent, wheel_a, git_sha, BUILT_AT_1
    )
    manifest_b, manifest_path_b = _write_manifest(
        wheel_b.parent, wheel_b, git_sha, BUILT_AT_2
    )
    assert manifest_a.release_id != manifest_b.release_id
    assert manifest_a.default_policy == manifest_b.default_policy == "flat"

    runtime_root = tmp_path / "runtime"
    staged_a = stage_release(
        runtime_root, manifest_path_a, wheel_a, created_at=BUILT_AT_1
    )
    pointer_a = activate_release(
        runtime_root, staged_a.release_id, created_at=BUILT_AT_1
    )
    binding_a = verify_slot(runtime_root, pointer_a.active_slot, pointer_a.release_id)
    python_a_stat = binding_a.python_executable.stat()
    python_a_identity = (
        python_a_stat.st_size,
        python_a_stat.st_mtime_ns,
        python_a_stat.st_ctime_ns,
    )
    _assert_installed_imports(binding_a.path, binding_a.python_executable)
    from runtime_launcher import resolve_active_command

    tool_count, _replies = _mcp_recall_smoke(
        resolve_active_command(runtime_root).arguments,
        runtime_root,
    )
    assert tool_count == 17

    doctor_a = build_doctor_report(
        runtime_root, generated_at=BUILT_AT_1, provenance_only=True
    ).to_mapping()
    assert doctor_a["status"] == "ok"
    assert doctor_a["active_release"]["git_sha"] == git_sha
    assert doctor_a["active_release"]["release_id"] == manifest_a.release_id
    assert doctor_a["default_policy"] == "flat"

    staged_b = stage_release(
        runtime_root, manifest_path_b, wheel_b, created_at=BUILT_AT_2
    )
    pointer_b = activate_release(
        runtime_root, staged_b.release_id, created_at=BUILT_AT_2
    )
    binding_b = verify_slot(runtime_root, pointer_b.active_slot, pointer_b.release_id)
    _assert_installed_imports(binding_b.path, binding_b.python_executable)
    assert pointer_b.active_slot != pointer_a.active_slot
    assert pointer_b.generation == 2

    rolled_back = rollback_release(runtime_root, created_at="2026-08-04T12:02:00Z")
    assert rolled_back.release_id == manifest_a.release_id
    assert rolled_back.active_slot == pointer_a.active_slot
    assert rolled_back.generation == 3
    restored = verify_slot(runtime_root, rolled_back.active_slot, rolled_back.release_id)
    restored_stat = restored.python_executable.stat()
    assert (
        restored_stat.st_size,
        restored_stat.st_mtime_ns,
        restored_stat.st_ctime_ns,
    ) == python_a_identity
    doctor_rollback = build_doctor_report(
        runtime_root,
        generated_at="2026-08-04T12:02:00Z",
        provenance_only=True,
    ).to_mapping()
    assert doctor_rollback["active_release"]["release_id"] == manifest_a.release_id
    assert doctor_rollback["default_policy"] == "flat"
