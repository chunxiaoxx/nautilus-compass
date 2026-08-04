from __future__ import annotations

import hashlib
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path

from benchmarks.learning_kernel_r0.cli import load_fixture, run_fixture, summarize_results
from release_manifest import ReleaseManifest


REPO_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_PATH = REPO_ROOT / "docs" / "evidence" / "compass_c1_candidate_v1.json"
MANIFEST_PATH = REPO_ROOT / "docs" / "evidence" / "compass_c1_release_manifest_v1.json"
FIXTURE_DIR = REPO_ROOT / "benchmarks" / "learning_kernel_r0" / "fixtures" / "r0"
HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")


def _sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def test_c1_evidence_is_bound_to_manifest_and_recomputed_learning_summary() -> None:
    evidence_bytes = EVIDENCE_PATH.read_bytes()
    evidence = json.loads(evidence_bytes)
    assert evidence_bytes == (
        json.dumps(evidence, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode(
            "utf-8"
        )
        + b"\n"
    )
    assert evidence["schema_version"] == "compass.c1.candidate.evidence.v1"
    assert evidence["candidate_state"] == "candidate_only"
    assert evidence["runtime_recommendation"] == "flat"
    assert evidence["improvement_claim"] is False
    assert evidence["production_adoption"] is False
    assert HASH_PATTERN.fullmatch(evidence["release"]["manifest_sha256"])
    assert evidence["release"]["manifest_sha256"] == _sha256(MANIFEST_PATH)

    manifest_bytes = MANIFEST_PATH.read_bytes()
    manifest = ReleaseManifest.from_json_bytes(manifest_bytes)
    assert manifest_bytes == manifest.canonical_bytes()
    assert manifest.git_sha == evidence["candidate_source_commit"]
    assert manifest.release_id == evidence["release"]["release_id"]
    assert manifest.wheel_sha256 == evidence["release"]["wheel_sha256"]
    assert manifest.default_policy == "flat"
    assert evidence["release"]["manifest_filename"] == "release-manifest.json"
    source_committed_at = subprocess.run(
        ["git", "show", "-s", "--format=%cI", evidence["candidate_source_commit"]],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=10,
        check=True,
    ).stdout.strip()
    assert datetime.fromisoformat(manifest.built_at.replace("Z", "+00:00")) >= datetime.fromisoformat(
        source_committed_at
    )

    bundle = load_fixture(FIXTURE_DIR)
    summary = summarize_results(bundle, run_fixture(bundle))
    recorded = evidence["learning_kernel"]
    assert recorded["fixture_manifest_hash"] == bundle.manifest_hash
    assert recorded["summary_hash"] == summary["summary_hash"]
    assert recorded["candidate_delta"] == summary["causal"]["candidate_delta"]
    assert recorded["protected_deltas"] == summary["safety"]["protected_deltas"]
    assert recorded["admitted_poisoned_view_ids"] == []
    assert summary["decision"]["candidate_state"] == "candidate_only"
    assert summary["runtime_recommendation"] == "flat"
    assert summary["improvement_claim"] is False


def test_c1_evidence_keeps_claim_classes_separate() -> None:
    evidence = json.loads(EVIDENCE_PATH.read_text(encoding="utf-8"))

    assert evidence["verification"]["source_test_count"] == 556
    assert evidence["verification"]["installed_wheel_e2e_count"] == 1
    assert evidence["verification"]["combined_test_count"] == 557
    assert evidence["verification"]["source_security_findings"] == 0
    assert evidence["verification"]["wheel_security_findings"] == 0
    assert evidence["release_rehearsal"] == {
        "doctor_daemon_port_aligned": True,
        "doctor_provenance_read_back": True,
        "installed_code_wheel_bound": True,
        "installed_extra_code_rejected": True,
        "installed_import_isolated": True,
        "installed_learning_kernel": True,
        "installed_python_bound": True,
        "launcher_isolated": True,
        "mcp_tool_count": 17,
        "recall_backend_isolated": True,
        "reproducible_wheel": True,
        "rollback_without_reinstall": True,
        "runtime_bytecode_write_disabled": True,
        "slots_exercised": ["a", "b"],
        "structured_secret_scan": True,
        "switch_generation": 2,
        "rollback_generation": 3,
        "transition_locked": True,
    }
    assert evidence["claim_boundary"]["external_baseline_run"] is False
    assert evidence["claim_boundary"]["real_agent_uplift_proven"] is False
    assert evidence["claim_boundary"]["sota_claim"] is False
