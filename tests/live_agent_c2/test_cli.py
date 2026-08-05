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


def write_json(path: Path, value) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def read_jsonl(path: Path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def write_jsonl(path: Path, values) -> None:
    path.write_text(
        "".join(
            json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
            + "\n"
            for value in values
        ),
        encoding="utf-8",
    )


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
    receipt = read_json(output / "run_receipt.json")
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
    assert receipt["schema_version"] == "compass.live_agent_c2.run_receipt.v1"
    assert len(receipt["signature"]) == 128
    assert not (output / ".verifier_signing_key").exists()

    before = (output / "bundles.jsonl").read_bytes()
    assert main(args + ["--resume"]) == 0
    capsys.readouterr()
    assert (output / "bundles.jsonl").read_bytes() == before

    assert main(["--mode", "replay", "--output", str(output)]) == 0
    replay = json.loads(capsys.readouterr().out)
    assert replay["replay_verified"] is True
    assert replay["pairs_hash"] == summary["pairs_hash"]


@pytest.mark.parametrize("mutation", ("provider", "bundle_hash"))
def test_replay_rejects_rehashed_outcome_evidence_binding_tamper(
    tmp_path, capsys, mutation
):
    output = tmp_path / "tampered-outcome"
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

    outcomes = read_jsonl(output / "outcomes.jsonl")
    bundles = read_jsonl(output / "bundles.jsonl")
    manifest = read_json(output / "run_manifest.json")
    summary = read_json(output / "summary.json")
    if mutation == "provider":
        providers = [item["provider_id"] + "/" + item["model_id"] for item in manifest["providers"]]
        outcomes[0]["provider_key"] = next(
            provider for provider in providers if provider != outcomes[0]["provider_key"]
        )
    else:
        outcomes[0]["flat_bundle_hash"] = next(
            item["bundle_hash"]
            for item in bundles
            if item["bundle_hash"] != outcomes[0]["flat_bundle_hash"]
        )
    parsed = tuple(cli_module.outcome_from_mapping(item) for item in outcomes)
    metrics = cli_module.compute_metrics(
        parsed,
        seed=manifest["seed"],
        bootstrap_samples=manifest["bootstrap_samples"],
        invalid_attempt_count=summary["invalid_attempt_count"],
        retry_count=summary["retry_count"],
    )
    summary["pairs_hash"] = metrics.pairs_hash
    write_jsonl(output / "outcomes.jsonl", outcomes)
    write_json(output / "summary.json", summary)

    with pytest.raises(ValueError, match="outcome evidence binding"):
        cli_module.replay_run(output)


@pytest.mark.parametrize(
    ("field", "value"),
    (("improvement_claim", True), ("runtime_recommendation", "governed"), ("invalid_attempt_count", 99)),
)
def test_replay_rejects_mutable_summary_and_counter_tamper(
    tmp_path, capsys, field, value
):
    output = tmp_path / f"tampered-summary-{field}"
    assert (
        main(
            [
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
        )
        == 0
    )
    capsys.readouterr()
    summary = read_json(output / "summary.json")
    summary[field] = value
    write_json(output / "summary.json", summary)

    with pytest.raises(ValueError, match="run summary replay mismatch"):
        cli_module.replay_run(output)


def test_replay_rejects_tampered_signed_run_receipt(tmp_path, capsys):
    output = tmp_path / "tampered-receipt"
    assert (
        main(
            [
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
        )
        == 0
    )
    capsys.readouterr()
    receipt = read_json(output / "run_receipt.json")
    receipt["retry_count"] += 1
    write_json(output / "run_receipt.json", receipt)

    with pytest.raises(ValueError, match="run receipt signature"):
        cli_module.replay_run(output)


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


def test_committed_formal_evidence_is_deidentified_replay_bound_and_not_promoted():
    root = Path(__file__).resolve().parents[2]
    evidence = root / "docs" / "evidence" / "c2"
    summary_path = evidence / "formal_summary.json"
    replay_path = evidence / "formal_replay_manifest.json"
    decision_path = evidence / "decision.md"
    summary_encoded = summary_path.read_text(encoding="utf-8")
    replay_encoded = replay_path.read_text(encoding="utf-8")
    decision = decision_path.read_text(encoding="utf-8")
    summary = json.loads(summary_encoded)
    replay = json.loads(replay_encoded)

    assert summary["schema_version"] == "compass.live_agent_c2.formal_summary.v1"
    assert summary["scheduled_pairs"] == 80
    assert summary["valid_pairs"] == 73
    assert summary["valid_pairs"] >= 60
    assert summary["provider_count"] == 2
    assert len(summary["by_provider_query_class"]) == 8
    assert summary["overall"]["ci_low"] > 0
    assert summary["protected_delta"] == 0
    assert summary["overall"]["poison_admissions"] == 0
    assert summary["promote_recommended"] is True
    assert summary["candidate_state"] == "candidate_only"
    assert summary["runtime_recommendation"] == "flat"
    assert summary["improvement_claim"] is False
    assert summary["raw_response_committed"] is False

    assert replay["schema_version"] == "compass.live_agent_c2.formal_replay_manifest.v1"
    assert replay["outcome_count"] == 73
    assert replay["bundle_count"] == replay["raw_response_count"] == 146
    assert replay["event_count"] == 292
    assert replay["checkpoint_count"] == 80
    assert replay["private_signing_key_present"] is False
    assert replay["replay_verified"] is True
    assert replay["raw_response_committed"] is False

    encoded = summary_encoded + replay_encoded + decision
    assert "API_KEY" not in encoded
    assert ".verifier_signing_key" not in encoded
    assert "output_text" not in encoded
    assert "runtime remains flat" in decision


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
    manifest = read_json(output / "run_manifest.json")
    assert summary["evidence_tier"] == "live"
    assert summary["total_pairs"] == 8
    assert summary["provider_count"] == 2
    assert len(summary["by_provider_query_class"]) == 8
    assert summary["candidate_state"] == "candidate_only"
    assert summary["improvement_claim"] is False
    assert summary["promote_recommended"] is False
    assert summary["replay_verified"] is True
    assert manifest["schema_version"] == "compass.live_agent_c2.run_manifest.v3"
    assert manifest["provider_protocol_version"] == "compass.live_agent_c2.provider.v2"
    assert manifest["providers"] == [
        {
            "adapter_kind": "cli",
            "adapter_version": "test-v1",
            "model_id": "glm-5.2-1m",
            "provider_id": "custom-anthropic-proxy",
        },
        {
            "adapter_kind": "openai_compatible",
            "adapter_version": "test-v1",
            "model_id": "doubao-seed-2-0-pro-260215",
            "provider_id": "volcengine",
        },
    ]


@pytest.mark.parametrize(
    "mutation",
    (
        "provider_protocol_version",
        "model_id",
        "model_id_rehashed",
        "adapter_version",
        "unknown_field",
        "missing_field",
    ),
)
def test_replay_and_resume_reject_tampered_provider_manifest(
    monkeypatch, tmp_path, mutation
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
    manifest_path = output / "run_manifest.json"
    manifest = read_json(manifest_path)
    if mutation == "provider_protocol_version":
        manifest["provider_protocol_version"] = "compass.live_agent_c2.provider.tampered"
    elif mutation in {"model_id", "model_id_rehashed"}:
        manifest["providers"][0]["model_id"] = "tampered-model"
    elif mutation == "adapter_version":
        manifest["providers"][0]["adapter_version"] = "tampered-adapter"
    elif mutation == "unknown_field":
        manifest["unknown"] = "forbidden"
    else:
        manifest.pop("mode")
    if mutation == "model_id_rehashed":
        manifest["config_hash"] = cli_module.hash_json(
            {field: manifest[field] for field in cli_module.RUN_CONFIG_FIELDS}
        )
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="run manifest"):
        cli_module.replay_run(output)
    with pytest.raises(ValueError, match="run manifest"):
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


def test_formal_mode_is_fixed_to_80_pairs_and_rejects_shape_overrides(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(cli_module, "build_live_adapters", live_oracles)
    args = cli_module.build_parser().parse_args(
        ["--mode", "formal", "--output", str(tmp_path / "formal")]
    )
    providers = tuple(adapter.identity for adapter in live_oracles())
    replicas = cli_module._effective_replicas(args)
    assignments = cli_module.schedule_pairs(
        cli_module.read_task_pack(), providers, replicas=replicas
    )

    assert replicas == 5
    assert len(assignments) == 80

    with pytest.raises(ValueError, match="formal mode fixes replicas at 5"):
        main(
            [
                "--mode",
                "formal",
                "--output",
                str(tmp_path / "formal"),
                "--replicas",
                "4",
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


def test_live_resume_rejects_mismatched_signing_key_before_calls_or_checkpoint_writes(
    monkeypatch, tmp_path
):
    output = tmp_path / "resume-key-mismatch"
    first_calls = {"count": 0}

    class InterruptingOracle(LiveOracleAdapter):
        def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
            first_calls["count"] += 1
            if first_calls["count"] == 3:
                raise KeyboardInterrupt
            return super().invoke(prompt, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(
        cli_module,
        "build_live_adapters",
        lambda _names=None: (
            InterruptingOracle("custom-anthropic-proxy", "glm-5.2-1m", "cli"),
            LiveOracleAdapter(
                "volcengine", "doubao-seed-2-0-pro-260215", "openai_compatible"
            ),
        ),
    )
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

    durable_paths = tuple(sorted((output / "checkpoints").glob("*.json"))) + (
        output / "progress.jsonl",
    )
    before = {path: path.read_bytes() for path in durable_paths}
    (output / ".verifier_signing_key").write_text("00" * 32, encoding="ascii")
    resumed_calls = {"count": 0}

    class CountingOracle(LiveOracleAdapter):
        def invoke(self, prompt: str, *, timeout_seconds: float) -> ProviderCallResult:
            resumed_calls["count"] += 1
            return super().invoke(prompt, timeout_seconds=timeout_seconds)

    monkeypatch.setattr(
        cli_module,
        "build_live_adapters",
        lambda _names=None: (
            CountingOracle("custom-anthropic-proxy", "glm-5.2-1m", "cli"),
            CountingOracle(
                "volcengine", "doubao-seed-2-0-pro-260215", "openai_compatible"
            ),
        ),
    )

    with pytest.raises(ValueError, match="resume verifier signing key mismatch"):
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

    assert resumed_calls["count"] == 0
    assert {path: path.read_bytes() for path in durable_paths} == before
