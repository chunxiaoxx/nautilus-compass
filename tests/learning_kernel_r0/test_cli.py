from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from benchmarks.learning_kernel_r0.cli import load_fixture, main, run_fixture, summarize_results


FIXTURE_DIR = (
    Path(__file__).parents[2]
    / "benchmarks"
    / "learning_kernel_r0"
    / "fixtures"
    / "r0"
)


def test_dry_run_validates_fixture_without_writes(tmp_path, capsys) -> None:
    before = {path.relative_to(FIXTURE_DIR): path.read_bytes() for path in FIXTURE_DIR.rglob("*") if path.is_file()}

    assert main(["dry-run", "--fixture-dir", str(FIXTURE_DIR)]) == 0

    after = {path.relative_to(FIXTURE_DIR): path.read_bytes() for path in FIXTURE_DIR.rglob("*") if path.is_file()}
    report = json.loads(capsys.readouterr().out)
    assert before == after
    assert not list(tmp_path.iterdir())
    assert report["matrix_runs"] == 2 * 2 * 6 * 7 * 2
    assert report["runtime_recommendation"] == "flat"


def test_run_refuses_fixture_changed_after_manifest(tmp_path) -> None:
    changed = tmp_path / "fixture"
    shutil.copytree(FIXTURE_DIR, changed)
    tasks_path = changed / "tasks.json"
    tasks_path.write_text(
        tasks_path.read_text(encoding="utf-8").replace("route/alpha", "route/tampered", 1),
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(ValueError, match="tasks.json hash mismatch"):
        main(["run", "--fixture-dir", str(changed), "--out", str(tmp_path / "out")])


def test_run_and_read_back_recompute_hashes_and_candidate_decision(tmp_path, capsys) -> None:
    output_dir = tmp_path / "runs"
    summary_path = tmp_path / "summary.json"

    assert main(
        ["run", "--fixture-dir", str(FIXTURE_DIR), "--out", str(output_dir)]
    ) == 0
    capsys.readouterr()
    first_journal = (output_dir / "results.jsonl").read_bytes()

    assert main(
        [
            "read-back",
            "--fixture-dir",
            str(FIXTURE_DIR),
            "--runs",
            str(output_dir),
            "--write-summary",
            str(summary_path),
        ]
    ) == 0
    report = json.loads(capsys.readouterr().out)
    summary = json.loads(summary_path.read_text(encoding="utf-8"))

    assert report == summary
    assert summary["decision"]["candidate_state"] == "candidate_only"
    assert summary["decision"]["runtime_recommendation"] == "flat"
    assert summary["decision"]["improvement_claim"] is False
    assert summary["matrix_runs"] == 336
    assert summary["causal"]["candidate_delta"] > summary["causal"]["permutation_p95"]
    assert summary["safety"]["admitted_poisoned_view_ids"] == []
    assert summary["forgetting"]["regret"] > 0

    assert main(
        ["run", "--fixture-dir", str(FIXTURE_DIR), "--out", str(output_dir)]
    ) == 0
    assert (output_dir / "results.jsonl").read_bytes() == first_journal


def test_summary_blocks_mismatched_actual_journal_hash() -> None:
    bundle = load_fixture(FIXTURE_DIR)
    summary = summarize_results(
        bundle,
        run_fixture(bundle),
        actual_journal_hash="sha256:" + "f" * 64,
    )

    assert summary["decision"]["candidate_state"] == "blocked"
    assert summary["decision"]["reason_code"] == "reproducibility_mismatch"
    assert summary["expected_journal_hash"] != summary["journal_hash"]
