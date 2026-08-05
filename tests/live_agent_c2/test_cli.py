from __future__ import annotations

import json
from pathlib import Path

import pytest

import benchmarks.live_agent_c2.cli as cli_module
from benchmarks.live_agent_c2.cli import main
from benchmarks.live_agent_c2.providers import ProviderCallResult
from benchmarks.live_agent_c2.schema import provider_from_mapping


def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


class LiveOracleAdapter:
    def __init__(self, provider_id: str, model_id: str, adapter_kind: str) -> None:
        self.identity = provider_from_mapping(
            {
                "provider_id": provider_id,
                "model_id": model_id,
                "adapter_kind": adapter_kind,
                "adapter_version": "test-v1",
            }
        )

    @property
    def admissible(self) -> bool:
        return True

    def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
        answers = {
            "route color is amber": "amber",
            "direction is north": "north",
            "codename was KESTREL-17": "KESTREL-17",
            "label was MOSAIC-42": "MOSAIC-42",
            "inspect, then isolate, then retry": "inspect > isolate > retry",
            "observe, then compare, then commit": "observe > compare > commit",
            "17 plus 25": "42",
            "Sort C, A, B": "A,B,C",
        }
        output = next((value for marker, value in answers.items() if marker in prompt), "unknown")
        return ProviderCallResult(
            provider_identity=self.identity,
            output_text=output,
            input_tokens=20,
            output_tokens=3,
            estimated_cost_usd=0.001,
            latency_ms=5,
        )


def live_oracles(_names=None):
    return (
        LiveOracleAdapter("custom-anthropic-proxy", "glm-5.2-1m", "cli"),
        LiveOracleAdapter(
            "volcengine", "doubao-seed-2-0-pro-260215", "openai_compatible"
        ),
    )


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


def test_committed_provider_probe_summary_is_deidentified_and_fail_closed():
    root = Path(__file__).resolve().parents[2]
    path = root / "docs" / "evidence" / "c2" / "provider_probe_summary.json"
    encoded = path.read_text(encoding="utf-8")
    summary = json.loads(encoded)

    assert summary["schema_version"] == "compass.live_agent_c2.provider_probe_summary.v1"
    assert summary["admissible_provider_count"] == 2
    assert summary["credential_source"] == "environment_only"
    assert summary["raw_response_present"] is False
    assert summary["formal_evidence"] is False
    assert summary["improvement_claim"] is False
    assert all(item["verified"] for item in summary["providers"])
    assert "API_KEY" not in encoded


def test_committed_pilot_evidence_keeps_failed_gate_and_replay_binding():
    root = Path(__file__).resolve().parents[2]
    evidence = root / "docs" / "evidence" / "c2"
    summary_encoded = (evidence / "pilot_summary.json").read_text(encoding="utf-8")
    summary = json.loads(summary_encoded)
    replay = read_json(evidence / "pilot_replay_manifest.json")

    assert summary["valid_pairs"] == 7
    assert summary["scheduled_pairs"] == 8
    assert summary["promote_recommended"] is False
    assert summary["improvement_claim"] is False
    assert summary["runtime_recommendation"] == "flat"
    assert summary["policy_reasons"] == [
        "insufficient_pairs",
        "missing_provider_query_coverage",
    ]
    assert replay["bundle_count"] == 2 * replay["outcome_count"] == 14
    assert replay["event_count"] == 2 * replay["bundle_count"] == 28
    assert replay["quarantine_count"] == 0
    assert replay["replay_verified"] is True
    assert summary["raw_response_committed"] is False
    assert replay["raw_response_committed"] is False
    assert "API_KEY" not in summary_encoded


def test_live_probe_is_metered_deidentified_and_does_not_write_raw(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(cli_module, "build_live_adapters", live_oracles)
    output = tmp_path / "probe"

    assert main(["--mode", "probe", "--output", str(output)]) == 0

    report = json.loads(capsys.readouterr().out)
    assert report["mode"] == "probe"
    assert report["admissible_provider_count"] == 2
    assert report["improvement_claim"] is False
    assert all(item["verified"] for item in report["providers"])
    assert all("output_text" not in item for item in report["providers"])
    assert not (output / "raw").exists()
    assert read_json(output / "provider_probe.json") == report


def test_live_pilot_covers_each_query_class_per_provider_and_replays(
    monkeypatch, tmp_path, capsys
):
    monkeypatch.setattr(cli_module, "build_live_adapters", live_oracles)
    output = tmp_path / "pilot"

    assert (
        main(
            [
                "--mode",
                "pilot",
                "--output",
                str(output),
                "--bootstrap-samples",
                "200",
            ]
        )
        == 0
    )
    capsys.readouterr()

    summary = read_json(output / "summary.json")
    assert summary["evidence_tier"] == "live"
    assert summary["total_pairs"] == 8
    assert summary["provider_count"] == 2
    assert len(summary["by_provider_query_class"]) == 8
    assert summary["candidate_state"] == "candidate_only"
    assert summary["improvement_claim"] is False
    assert summary["promote_recommended"] is False
    assert summary["replay_verified"] is True


def test_formal_mode_is_fixed_to_64_pairs_and_rejects_shape_overrides(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(cli_module, "build_live_adapters", live_oracles)
    with pytest.raises(ValueError, match="formal mode fixes replicas at 4"):
        main(
            [
                "--mode",
                "formal",
                "--output",
                str(tmp_path / "formal"),
                "--replicas",
                "1",
            ]
        )
    with pytest.raises(ValueError, match="limit-pairs"):
        main(
            [
                "--mode",
                "formal",
                "--output",
                str(tmp_path / "formal"),
                "--limit-pairs",
                "8",
            ]
        )


def test_live_resume_skips_completed_and_interrupted_pairs_without_double_calling(
    monkeypatch, tmp_path, capsys
):
    output = tmp_path / "resumable-pilot"
    interrupted_calls = {"count": 0}

    class InterruptingOracle(LiveOracleAdapter):
        def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
            interrupted_calls["count"] += 1
            if interrupted_calls["count"] == 3:
                raise KeyboardInterrupt
            return super().invoke(prompt, timeout_seconds=timeout_seconds)

    def interrupted_oracles(_names=None):
        return (
            InterruptingOracle("custom-anthropic-proxy", "glm-5.2-1m", "cli"),
            LiveOracleAdapter(
                "volcengine", "doubao-seed-2-0-pro-260215", "openai_compatible"
            ),
        )

    monkeypatch.setattr(cli_module, "build_live_adapters", interrupted_oracles)
    with pytest.raises(KeyboardInterrupt):
        main(
            [
                "--mode",
                "pilot",
                "--output",
                str(output),
                "--bootstrap-samples",
                "200",
            ]
        )

    assert len(tuple((output / "checkpoints").glob("*.json"))) == 1

    resumed_calls = {"count": 0}

    class CountingOracle(LiveOracleAdapter):
        def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
            resumed_calls["count"] += 1
            return super().invoke(prompt, timeout_seconds=timeout_seconds)

    def resumed_oracles(_names=None):
        return (
            CountingOracle("custom-anthropic-proxy", "glm-5.2-1m", "cli"),
            CountingOracle(
                "volcengine", "doubao-seed-2-0-pro-260215", "openai_compatible"
            ),
        )

    monkeypatch.setattr(cli_module, "build_live_adapters", resumed_oracles)
    assert (
        main(
            [
                "--mode",
                "pilot",
                "--output",
                str(output),
                "--bootstrap-samples",
                "200",
                "--resume",
            ]
        )
        == 0
    )
    capsys.readouterr()

    summary = read_json(output / "summary.json")
    progress = [
        json.loads(line)
        for line in (output / "progress.jsonl").read_text(encoding="utf-8").splitlines()
    ]
    assert resumed_calls["count"] == 12
    assert summary["total_pairs"] == 7
    assert summary["invalid_attempt_count"] == 1
    assert summary["replay_verified"] is True
    assert any(item["status"] == "interrupted" for item in progress)
    assert len(tuple((output / "checkpoints").glob("*.json"))) == 8
