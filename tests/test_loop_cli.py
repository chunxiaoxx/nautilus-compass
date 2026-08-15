from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cli import main


H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64


def _suite(path: Path) -> Path:
    suite = {
        "schema_version": "compass.loop.plan.v1",
        "run_id": "gate-a-1",
        "task": {"id": "gate-a-repair", "description": "repair the fixed fixture"},
        "oracle": {"expected": "fixed"},
        "action_agent_id": 7,
        "verifier_agent_id": 8,
        "verifier_policy_hash": H2,
        "environment_fingerprint_hash": H3,
        "arms": [
            {
                "label": "control",
                "episode_id": "gate-a-control",
                "advice": None,
                "occurred_at": "2026-08-15T00:00:00Z",
            },
            {
                "label": "treatment",
                "episode_id": "gate-a-treatment",
                "advice": "apply the checked fix",
                "occurred_at": "2026-08-15T00:01:00Z",
            },
        ],
    }
    path.write_text(json.dumps(suite), encoding="utf-8")
    return path


def test_help_lists_loop_subcommand(capsys) -> None:
    assert main(["--help"]) == 0
    assert "loop" in capsys.readouterr().out


def test_loop_run_and_verify_emit_a_visible_repair_report(tmp_path: Path, capsys) -> None:
    suite = _suite(tmp_path / "suite.json")
    out = tmp_path / "run"

    assert main(["loop", "run", str(suite), "--out", str(out)]) == 0
    run_output = capsys.readouterr().out
    assert "Compass learning loop: Repair" in run_output
    assert "gate_a_operational_only" in run_output
    assert "automatic promotion: false" in run_output
    assert (out / "report.json").is_file()

    assert main(["loop", "verify", str(out)]) == 0
    verify_output = capsys.readouterr().out
    assert "Compass learning loop: Repair" in verify_output
    assert "control: failure" in verify_output
    assert "treatment: success" in verify_output


def test_loop_run_rejects_nonempty_output_directory(tmp_path: Path, capsys) -> None:
    suite = _suite(tmp_path / "suite.json")
    out = tmp_path / "occupied"
    out.mkdir()
    (out / "unrelated.txt").write_text("keep", encoding="utf-8")

    assert main(["loop", "run", str(suite), "--out", str(out)]) == 2
    assert "must be new or empty" in capsys.readouterr().err
    assert (out / "unrelated.txt").read_text(encoding="utf-8") == "keep"


def test_loop_verify_replays_from_a_fresh_console_process(tmp_path: Path) -> None:
    suite = _suite(tmp_path / "suite.json")
    out = tmp_path / "run"
    assert main(["loop", "run", str(suite), "--out", str(out)]) == 0

    console = Path(sys.executable).with_name("nautilus-compass.exe")
    completed = subprocess.run(
        [str(console), "loop", "verify", str(out)],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "Compass learning loop: Repair" in completed.stdout
    assert "automatic promotion: false" in completed.stdout
