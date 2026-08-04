from __future__ import annotations

import json
import subprocess
from pathlib import Path

from benchmarks.learning_kernel_r0.cli import load_fixture, run_fixture, summarize_results
from benchmarks.learning_kernel_r0.policy import PROTECTED_REGRESSION_FLOOR
from benchmarks.poi_gate2.canonical import hash_bytes, hash_json


ROOT = Path(__file__).parents[2]
FIXTURE_DIR = ROOT / "benchmarks" / "learning_kernel_r0" / "fixtures" / "r0"
SUMMARY_PATH = ROOT / "docs" / "evidence" / "learning_kernel_r0_mechanism_summary_v1.json"
PROTOCOL_PATH = ROOT / "docs" / "evidence" / "learning_kernel_r0_protocol_v1.json"


def test_committed_summary_is_reproducible_and_remains_candidate_only() -> None:
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    supplied_hash = summary.pop("summary_hash")
    assert supplied_hash == hash_json(summary)
    summary["summary_hash"] = supplied_hash

    rebuilt = summarize_results(load_fixture(FIXTURE_DIR), run_fixture(load_fixture(FIXTURE_DIR)))
    assert rebuilt == summary
    assert summary["matrix_runs"] == 336
    assert summary["selectors"] == [
        "flat",
        "semantic",
        "distilled",
        "contextual_utility",
        "current_poi",
        "governed",
    ]
    assert summary["interventions"] == [
        "no_memory",
        "raw",
        "distilled",
        "shuffled",
        "stale",
        "contradictory",
        "poisoned",
    ]
    assert summary["causal"]["candidate_delta"] > summary["causal"]["permutation_p95"]
    assert all(
        delta >= PROTECTED_REGRESSION_FLOOR
        for delta in summary["safety"]["protected_deltas"].values()
    )
    assert summary["safety"]["admitted_poisoned_view_ids"] == []
    assert summary["forgetting"]["regret"] > 0
    assert summary["efficiency"]["latency_p95_ms"] >= summary["efficiency"]["latency_p50_ms"]
    assert summary["efficiency"]["total_input_tokens"] > 0
    assert summary["efficiency"]["total_estimated_cost_usd"] == 0.0
    assert summary["decision"]["candidate_state"] == "candidate_only"
    assert summary["runtime_recommendation"] == "flat"
    assert summary["improvement_claim"] is False


def test_protocol_binds_code_fixture_summary_environment_and_test_gate() -> None:
    protocol = json.loads(PROTOCOL_PATH.read_text(encoding="utf-8"))
    supplied_hash = protocol.pop("protocol_hash")
    assert supplied_hash == hash_json(protocol)
    assert protocol["schema_version"] == "compass.learning_kernel.protocol.v1"
    assert protocol["fixture_manifest_hash"] == hash_bytes(
        (FIXTURE_DIR / "manifest.json").read_bytes()
    )
    assert protocol["mechanism_summary_file_hash"] == hash_bytes(SUMMARY_PATH.read_bytes())
    assert protocol["dependency_lock"] == {
        "path": "pyproject.toml",
        "sha256": hash_bytes((ROOT / "pyproject.toml").read_bytes()),
    }
    assert protocol["python_version"] == "3.13.14"
    assert protocol["local_gate"]["status"] == "passed"
    assert protocol["local_gate"]["runtime_recommendation"] == "flat"
    assert protocol["local_gate"]["improvement_claim"] is False
    assert protocol["independent_review"]["high_findings"] == 0
    assert protocol["independent_review"]["medium_findings"] == 0
    assert subprocess.run(
        ["git", "merge-base", "--is-ancestor", protocol["code_commit"], "HEAD"],
        cwd=ROOT,
        check=False,
    ).returncode == 0
