from __future__ import annotations

import json
from pathlib import Path

import pytest

from benchmarks.live_agent_c2.cli import main


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_dry_run_is_read_only_and_reports_frozen_schedule(tmp_path, capsys):
    output = tmp_path / "must-not-exist"

    assert main(["--mode", "dry-run", "--output", str(output), "--replicas", "1"]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "dry-run"
    assert report["task_count"] == 8
    assert report["scheduled_pairs"] == 16
    assert report["runtime_recommendation"] == "flat"
    assert report["improvement_claim"] is False
    assert not output.exists()


def test_fake_e2e_writes_replayable_local_evidence_without_claim(tmp_path, capsys):
    output = tmp_path / "synthetic-run"
    args = [
        "--mode",
        "fake",
        "--output",
        str(output),
        "--replicas",
        "1",
        "--limit-pairs",
        "4",
        "--bootstrap-samples",
        "200",
    ]

    assert main(args) == 0
    capsys.readouterr()

    summary = read_json(output / "summary.json")
    assert summary["evidence_tier"] == "synthetic"
    assert summary["total_pairs"] == 4
    assert summary["runtime_recommendation"] == "flat"
    assert summary["candidate_state"] == "candidate_only"
    assert summary["improvement_claim"] is False
    assert summary["promote_recommended"] is False
    assert summary["replay_verified"] is True
    assert len((output / "bundles.jsonl").read_text(encoding="utf-8").splitlines()) == 8
    assert len((output / "outcomes.jsonl").read_text(encoding="utf-8").splitlines()) == 4
    assert len(tuple((output / "raw").glob("*.txt"))) == 8

    before = (output / "bundles.jsonl").read_bytes()
    assert main(args + ["--resume"]) == 0
    capsys.readouterr()
    assert (output / "bundles.jsonl").read_bytes() == before

    assert main(["--mode", "replay", "--output", str(output)]) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["replay_verified"] is True
    assert replay["pairs_hash"] == summary["pairs_hash"]


def test_cli_refuses_unknown_provider_nonempty_output_and_wrong_resume(tmp_path):
    output = tmp_path / "run"
    output.mkdir()
    (output / "foreign.txt").write_text("do not overwrite", encoding="utf-8")
    with pytest.raises(ValueError, match="output directory"):
        main(["--mode", "fake", "--output", str(output)])

    with pytest.raises(SystemExit):
        main(
            [
                "--mode",
                "dry-run",
                "--output",
                str(tmp_path / "dry"),
                "--provider",
                "not-allowed",
            ]
        )


def test_local_raw_run_directory_is_gitignored():
    root = Path(__file__).resolve().parents[2]
    ignored = (root / ".gitignore").read_text(encoding="utf-8")
    assert ".c2_runs/" in ignored
