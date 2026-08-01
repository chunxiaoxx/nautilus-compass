from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import venv
from pathlib import Path


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

SMOKE_SCRIPT = r"""
import json
import sys
from pathlib import Path

import gep
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


def run(command: list[str], *, cwd: Path) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"command failed: {command!r}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    return result


def venv_python(venv_path: Path) -> Path:
    if os.name == "nt":
        return venv_path / "Scripts" / "python.exe"
    return venv_path / "bin" / "python"


def source_snapshot(tmp_path: Path) -> Path:
    archive_path = tmp_path / "source.zip"
    source_path = tmp_path / "source"
    source_path.mkdir()
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
    )
    shutil.unpack_archive(archive_path, source_path, format="zip")

    snapshot_members = tuple(source_path.rglob("*"))
    assert not any(path.name in SNAPSHOT_EXCLUDED_NAMES for path in snapshot_members)
    assert not any(path.name.endswith(".egg-info") for path in snapshot_members)
    assert not any(
        path.name == ".env" or path.name.startswith(".env.")
        for path in snapshot_members
    )
    return source_path


def build_wheel(tmp_path: Path) -> Path:
    source_path = source_snapshot(tmp_path)
    wheelhouse = tmp_path / "wheelhouse"
    wheelhouse.mkdir()
    run(
        [
            sys.executable,
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
    )
    wheels = tuple(wheelhouse.glob("nautilus_compass-*.whl"))
    assert len(wheels) == 1, wheels
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
