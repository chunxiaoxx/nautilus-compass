from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_readme_separates_c1_candidate_from_historical_benchmarks() -> None:
    readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

    assert "## C1 · Compass 2.3 trusted-candidate status" in readme
    assert "candidate-only; not installed or deployed" in readme
    assert "Historical end-to-end QA accuracy; not rerun on C1" in readme
    assert "Deterministic mechanism fixture; not real-agent uplift" in readme
    assert "Runtime policy remains `flat`" in readme
    assert "Achieving Zep-SOTA Performance" not in readme
    assert "No C1 SOTA claim" in readme
    assert "docs/evidence/compass_c1_candidate_v1.json" in readme


def test_results_labels_evidence_classes_and_reproduction_limits() -> None:
    results = (REPO_ROOT / "RESULTS.md").read_text(encoding="utf-8")

    assert "## C1 · 2.3 candidate verification" in results
    assert "Historical benchmark results are not C1 reruns" in results
    assert "End-to-end QA accuracy" in results
    assert "Retrieval-only" in results
    assert "Runtime/mechanism" in results
    assert "Learning-kernel mechanism" in results
    assert "provider credentials or model artifacts" in results
    assert "candidate_only" in results
    assert "improvement_claim=false" in results
