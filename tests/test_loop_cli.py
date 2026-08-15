from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import gep.live_coding_adapter as live_adapter_module
import loop_cli

from cli import main


H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64
ROOT = Path(__file__).resolve().parents[1]


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


def test_loop_preflight_binds_live_value_suite_without_calling_a_provider(
    monkeypatch, capsys
) -> None:
    monkeypatch.setenv("ARK_API_KEY", "test-only-secret")

    assert (
        main(
            [
                "loop",
                "preflight",
                str(ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite.json"),
            ]
        )
        == 0
    )

    output = capsys.readouterr().out
    assert "Compass live preflight: ready" in output
    assert "zero provider calls: true" in output
    assert "test-only-secret" not in output


def test_loop_live_run_uses_a_bounded_fake_provider_and_independent_oracle(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    class FakeProvider:
        def __init__(self, _suite) -> None:
            self.outputs = [
                '{"answer":"Reject bool before accepting int.","reuse_advice":"Reject bool before accepting int in related validators."}',
                '{"answer":"isinstance(value, int)"}',
                '{"answer":"not isinstance(value, bool) and isinstance(value, int) and 1 <= value <= 65535"}',
            ]

        def invoke(self, prompt: str, *, timeout_seconds: int):
            del prompt
            assert timeout_seconds == 30
            return live_adapter_module.ProviderResult(
                output_text=self.outputs.pop(0),
                reported_model_id="glm-5.2[1m]",
                input_tokens=10,
                output_tokens=4,
                estimated_cost_usd=0.001,
                latency_ms=1,
            )

    monkeypatch.setattr(live_adapter_module.shutil, "which", lambda command: command)
    monkeypatch.setattr(loop_cli, "ClaudeCliProvider", FakeProvider)
    out = tmp_path / "live"

    assert (
        loop_cli.main(
            [
                "live-run",
                str(ROOT / "benchmarks" / "dogfood_mvp_v1" / "value_suite.json"),
                "--out",
                str(out),
            ]
        )
        == 0
    )

    report = json.loads((out / "report.json").read_text(encoding="utf-8"))
    assert report["decision"] == "Gold"
    assert report["experience_candidate"]["capsule_candidate"] is True
    assert all(value is False for value in report["promotion"].values())
    assert "Compass learning loop: Gold" in capsys.readouterr().out
