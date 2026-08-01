from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import venv
import zipfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
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
)
SNAPSHOT_EXCLUDED_NAMES = frozenset(
    {
        ".cache",
        ".git",
        ".pytest_cache",
        ".venv",
        "__pycache__",
        "build",
        "dist",
        "tests",
        "venv",
    }
)
SENSITIVE_NAME = re.compile(
    r"(?:password|passwd|pwd|secret|token|api_?key|credential)",
    re.IGNORECASE,
)
PRIVATE_KEY_MARKER = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
DATABASE_CREDENTIAL_URL = re.compile(
    r"(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://"
    r"[^\s/:@]+:[^\s/@]+@",
    re.IGNORECASE,
)
GIT_TIMEOUT_SECONDS = 30
BUILD_TIMEOUT_SECONDS = 300
INSTALL_TIMEOUT_SECONDS = 180
SMOKE_TIMEOUT_SECONDS = 30

SMOKE_SCRIPT = r"""
import json
import sys
from pathlib import Path

import gep
import mcp_durable.event_store
from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    EVENT_KIND_VERDICT,
    PAYLOAD_SCHEMA,
    SCHEMA_VERSION,
    VERDICT_PAYLOAD_SCHEMA,
    event_from_mapping,
    hash_payload,
    hash_payload_for_kind,
)
from gep.flywheel_log import CompassS4AgentHarness, FlywheelEventLog
from gep.flywheel_state import reduce_episode_states
from gep.verdict_packet import VerdictPacket, to_payload


EPISODE_ID = "wheel-episode-1"
FORBIDDEN_MODULE_STEMS = (
    "chat",
    "feishu",
    "robot",
    "daemon",
    "recall",
    "capsule",
    "proof",
    "poi",
)


def is_forbidden_module(module_name):
    parts = module_name.casefold().split(".")
    return any(
        part == stem or part.startswith(stem + "_")
        for part in parts
        for stem in FORBIDDEN_MODULE_STEMS
    )


database_path = Path(sys.argv[1])
repo_root = Path(sys.argv[2]).resolve()
package_path = Path(next(iter(gep.__path__))).resolve()
assert sys.flags.isolated == 1
assert Path.cwd().resolve() != repo_root
assert repo_root not in package_path.parents

episode_payload = {"episode_id": EPISODE_ID, "task": "prove installed verdict wheel"}
episode = {
    "schema_version": SCHEMA_VERSION,
    "event_kind": EVENT_KIND_EPISODE,
    "source_event_id": "wheel-episode-source-1",
    "episode_id": EPISODE_ID,
    "parent_event_id": None,
    "agent_id": 7,
    "occurred_at": "2026-08-01T12:00:00Z",
    "payload_schema": PAYLOAD_SCHEMA,
    "payload": episode_payload,
    "payload_hash": hash_payload(episode_payload),
}
episode_event = event_from_mapping(episode)

verdict_packet = VerdictPacket(
    episode_id=EPISODE_ID,
    episode_event_hash=episode_event.event_hash,
    outcome="success",
    verifier_kind="software_test",
    verifier_version="wheel-smoke-v1",
    verifier_policy_hash="sha256:" + "2" * 64,
    evidence_hash="sha256:" + "3" * 64,
    environment_fingerprint_hash="sha256:" + "4" * 64,
)
verdict_payload = to_payload(verdict_packet)
verdict = {
    "schema_version": SCHEMA_VERSION,
    "event_kind": EVENT_KIND_VERDICT,
    "source_event_id": "wheel-verdict-source-1",
    "episode_id": EPISODE_ID,
    "parent_event_id": episode["source_event_id"],
    "agent_id": 8,
    "occurred_at": "2026-08-01T12:01:00Z",
    "payload_schema": VERDICT_PAYLOAD_SCHEMA,
    "payload": verdict_payload,
    "payload_hash": hash_payload_for_kind(EVENT_KIND_VERDICT, verdict_payload),
}

event_log = FlywheelEventLog(
    database_path,
    registered_agent_ids={7, 8},
    registered_verifier_ids={8},
)
try:
    harness = CompassS4AgentHarness(event_log)
    assert harness.record(episode).status == "accepted"
    assert harness.record(verdict).status == "accepted"
finally:
    event_log.close()

reopened = FlywheelEventLog(
    database_path,
    registered_agent_ids={7, 8},
    registered_verifier_ids={8},
)
try:
    events = reopened.list_events()
    state = reduce_episode_states(events)[EPISODE_ID]
    assert len(events) == 2
    assert state.state == "verified"
    assert state.verified_outcome == "success"
finally:
    reopened.close()

forbidden_modules = sorted(name for name in sys.modules if is_forbidden_module(name))
assert not forbidden_modules, forbidden_modules
print(
    json.dumps(
        {
            "event_count": len(events),
            "state": state.state,
            "verified_outcome": state.verified_outcome,
        },
        sort_keys=True,
    )
)
"""


def run(
    command: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=False,
            timeout=timeout_seconds,
        )
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(
            f"command timed out after {timeout_seconds} seconds: {command!r}"
        ) from exc
    assert result.returncode == 0, (
        f"command failed with exit code {result.returncode}: {command!r}; "
        "captured output omitted by the packaging security boundary"
    )
    return result


def assert_packaging_inputs_clean(status_output: str) -> None:
    dirty_paths = tuple(
        line[3:] if len(line) > 3 else line
        for line in status_output.splitlines()
        if line.strip()
    )
    assert not dirty_paths, (
        "packaging inputs are dirty; git archive HEAD would ignore these changes: "
        + ", ".join(dirty_paths)
    )


def _assigned_names(node: object) -> tuple[str, ...]:
    if isinstance(node, ast.Assign):
        targets = node.targets
    elif isinstance(node, ast.AnnAssign):
        targets = (node.target,)
    else:
        return ()
    return tuple(target.id for target in targets if isinstance(target, ast.Name))


def plaintext_secret_findings(label: str, source: str) -> tuple[str, ...]:
    findings: list[str] = []
    if PRIVATE_KEY_MARKER.search(source):
        findings.append(f"{label}: private-key marker")
    if DATABASE_CREDENTIAL_URL.search(source):
        findings.append(f"{label}: credential-bearing database URL")

    try:
        tree = ast.parse(source, filename=label)
    except SyntaxError as exc:
        findings.append(f"{label}:{exc.lineno or 1}: invalid Python source")
        return tuple(findings)

    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            value = node.value
            if (
                isinstance(value, ast.Constant)
                and isinstance(value.value, str)
                and value.value
                and any(SENSITIVE_NAME.search(name) for name in _assigned_names(node))
            ):
                findings.append(
                    f"{label}:{node.lineno}: plaintext sensitive assignment"
                )
        elif isinstance(node, ast.Call):
            for keyword in node.keywords:
                value = keyword.value
                if (
                    keyword.arg
                    and SENSITIVE_NAME.search(keyword.arg)
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                    and value.value
                ):
                    findings.append(
                        f"{label}:{value.lineno}: plaintext sensitive call argument"
                    )
    return tuple(findings)


def assert_no_plaintext_secrets_in_tree(root: Path) -> None:
    findings: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        label = path.relative_to(root).as_posix()
        if path.suffix == ".py":
            findings.extend(plaintext_secret_findings(label, source))
        else:
            if PRIVATE_KEY_MARKER.search(source):
                findings.append(f"{label}: private-key marker")
            if DATABASE_CREDENTIAL_URL.search(source):
                findings.append(f"{label}: credential-bearing database URL")
    assert findings == [], "packaging source contains secret markers: " + ", ".join(findings)


def assert_no_plaintext_secrets_in_wheel(wheel: Path) -> None:
    findings: list[str] = []
    with zipfile.ZipFile(wheel) as archive:
        for name in sorted(archive.namelist()):
            if name.endswith("/"):
                continue
            try:
                source = archive.read(name).decode("utf-8")
            except UnicodeDecodeError:
                continue
            if name.endswith(".py"):
                findings.extend(plaintext_secret_findings(name, source))
            else:
                if PRIVATE_KEY_MARKER.search(source):
                    findings.append(f"{name}: private-key marker")
                if DATABASE_CREDENTIAL_URL.search(source):
                    findings.append(f"{name}: credential-bearing database URL")
    assert findings == [], "wheel contains secret markers: " + ", ".join(findings)


def assert_wheel_metadata_is_clean(wheel: Path) -> None:
    with zipfile.ZipFile(wheel) as archive:
        top_level_names = {
            name.split("/", 1)[0]
            for name in archive.namelist()
            if name and not name.startswith("/")
        }
    egg_info = sorted(name for name in top_level_names if name.endswith(".egg-info"))
    dist_info = sorted(name for name in top_level_names if name.endswith(".dist-info"))
    assert not egg_info, "wheel contains stale egg-info directories: " + ", ".join(egg_info)
    assert len(dist_info) == 1, (
        "wheel must contain exactly one dist-info directory, found: "
        + ", ".join(dist_info)
    )


def venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def source_snapshot(tmp_path: Path) -> Path:
    archive_path = tmp_path / "source.zip"
    source_path = tmp_path / "source"
    source_path.mkdir()
    status = run(
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
        timeout_seconds=GIT_TIMEOUT_SECONDS,
    )
    assert_packaging_inputs_clean(status.stdout)
    run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "archive",
            "--format=zip",
            f"--output={archive_path}",
            "HEAD",
            "--",
            *PACKAGING_INPUT_PATHS,
        ],
        cwd=tmp_path,
        timeout_seconds=GIT_TIMEOUT_SECONDS,
    )
    shutil.unpack_archive(archive_path, source_path, format="zip")

    snapshot_members = tuple(source_path.rglob("*"))
    assert not any(path.name in SNAPSHOT_EXCLUDED_NAMES for path in snapshot_members)
    assert not any(path.name.endswith(".egg-info") for path in snapshot_members)
    assert not any(
        path.name == ".env" or path.name.startswith(".env.")
        for path in snapshot_members
    )
    assert_no_plaintext_secrets_in_tree(source_path)
    return source_path


def build_wheel(tmp_path: Path) -> Path:
    source_path = source_snapshot(tmp_path)
    builder_path = tmp_path / "builder-venv"
    venv.EnvBuilder(with_pip=True).create(builder_path)
    builder_python = venv_python(builder_path)
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    run(
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
            str(source_path),
        ],
        cwd=tmp_path,
        timeout_seconds=BUILD_TIMEOUT_SECONDS,
    )
    wheels = tuple(wheelhouse.glob("nautilus_compass-*.whl"))
    assert len(wheels) == 1, wheels
    assert_wheel_metadata_is_clean(wheels[0])
    assert_no_plaintext_secrets_in_wheel(wheels[0])
    return wheels[0]


def install_wheel(tmp_path: Path, wheel: Path) -> Path:
    venv_path = tmp_path / "venv"
    venv.EnvBuilder(with_pip=True).create(venv_path)
    python = venv_python(venv_path)
    run(
        [
            str(python),
            "-m",
            "pip",
            "--disable-pip-version-check",
            "install",
            "--no-deps",
            str(wheel),
        ],
        cwd=tmp_path,
        timeout_seconds=INSTALL_TIMEOUT_SECONDS,
    )
    return python


def run_smoke(tmp_path: Path, python: Path) -> subprocess.CompletedProcess[str]:
    outside_repo = (tmp_path / "outside-repo").resolve()
    outside_repo.mkdir()
    assert outside_repo != REPO_ROOT
    assert REPO_ROOT not in outside_repo.parents
    return run(
        [
            str(python),
            "-I",
            "-c",
            SMOKE_SCRIPT,
            str(outside_repo / "flywheel.sqlite3"),
            str(REPO_ROOT),
        ],
        cwd=outside_repo,
        timeout_seconds=SMOKE_TIMEOUT_SECONDS,
    )


def test_installed_wheel_runs_verified_verdict_flow_outside_repo(tmp_path: Path) -> None:
    wheel = build_wheel(tmp_path)
    python = install_wheel(tmp_path, wheel)
    result = run_smoke(tmp_path, python)

    assert json.loads(result.stdout) == {
        "event_count": 2,
        "state": "verified",
        "verified_outcome": "success",
    }


def test_packaging_input_guard_rejects_dirty_rows_without_file_contents() -> None:
    status_output = " M gep/flywheel_event.py\n?? middleware/local_override.py\n"

    with pytest.raises(AssertionError, match="packaging inputs are dirty") as exc_info:
        assert_packaging_inputs_clean(status_output)

    message = str(exc_info.value)
    assert "gep/flywheel_event.py" in message
    assert "local_override.py" in message
    assert "payload" not in message


def test_secret_scanner_reports_location_without_secret_value(tmp_path: Path) -> None:
    unsafe = tmp_path / "unsafe.py"
    fake_secret = "not-a-real-secret-value"
    unsafe.write_text(f'DATABASE_PASSWORD = "{fake_secret}"\n', encoding="utf-8")

    findings = plaintext_secret_findings("unsafe.py", unsafe.read_text(encoding="utf-8"))

    assert findings == ("unsafe.py:1: plaintext sensitive assignment",)
    assert fake_secret not in "\n".join(findings)


def test_run_reports_bounded_timeout_without_subprocess_output(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    def raise_timeout(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(
            cmd=["python", "-m", "build"],
            timeout=kwargs["timeout"],
            output="not-a-real-secret-output",
        )

    monkeypatch.setattr(subprocess, "run", raise_timeout)

    with pytest.raises(AssertionError, match="timed out after 7 seconds") as exc_info:
        run(["python", "-m", "build"], cwd=tmp_path, timeout_seconds=7)

    assert "not-a-real-secret-output" not in str(exc_info.value)


def test_wheel_metadata_guard_rejects_stale_egg_info(tmp_path: Path) -> None:
    wheel = tmp_path / "contaminated.whl"
    with zipfile.ZipFile(wheel, "w") as archive:
        archive.writestr("gep/__init__.py", "")
        archive.writestr("nautilus_compass-2.3.0.dist-info/METADATA", "")
        archive.writestr("nautilus_compass-2.3.0-py3.9.egg-info/PKG-INFO", "")

    with pytest.raises(AssertionError, match="egg-info"):
        assert_wheel_metadata_is_clean(wheel)
