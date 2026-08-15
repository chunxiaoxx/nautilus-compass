from __future__ import annotations

import json
import sqlite3
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pytest

from gep.loop_run import ActionArtifact, LoopRunError, run_loop, verify_run
from gep.verdict_packet import VerdictPacket


H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64
H4 = "sha256:" + "4" * 64


def plan(*, duplicate_episode: bool = False) -> dict[str, object]:
    treatment_episode = "repair-run-1-treatment"
    if duplicate_episode:
        treatment_episode = "repair-run-1-control"
    return {
        "schema_version": "compass.loop.plan.v1",
        "run_id": "repair-run-1",
        "task": {"id": "repair-1", "description": "repair the bounded fixture"},
        "oracle": {"expected": "fixed"},
        "action_agent_id": 7,
        "verifier_agent_id": 8,
        "verifier_policy_hash": H2,
        "environment_fingerprint_hash": H3,
        "arms": [
            {
                "label": "control",
                "episode_id": "repair-run-1-control",
                "advice": None,
                "occurred_at": "2026-08-15T00:00:00Z",
            },
            {
                "label": "treatment",
                "episode_id": treatment_episode,
                "advice": "apply the checked fix",
                "occurred_at": "2026-08-15T00:01:00Z",
            },
        ],
    }


@dataclass
class FakeAction:
    calls: list[tuple[str, str | None]] = field(default_factory=list)

    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact:
        del work_dir
        self.calls.append((str(task["episode_id"]), advice))
        answer = "fixed" if advice else "broken"
        return ActionArtifact(
            episode_id=str(task["episode_id"]),
            content={"answer": answer},
            tool_chain=("edit", "test"),
        )


@dataclass
class FakeVerifier:
    calls: list[str] = field(default_factory=list)

    def verify(
        self,
        task: dict[str, object],
        artifact: ActionArtifact,
        oracle: dict[str, object],
    ) -> VerdictPacket:
        del task
        self.calls.append(artifact.episode_id)
        outcome = "success" if artifact.content["answer"] == oracle["expected"] else "failure"
        return VerdictPacket(
            episode_id=artifact.episode_id,
            episode_event_hash=artifact.episode_event_hash or "",
            outcome=outcome,
            verifier_kind="software_test",
            verifier_version="fake-verifier-v1",
            verifier_policy_hash=H2,
            evidence_hash=artifact.evidence_hash,
            environment_fingerprint_hash=H3,
            failure_class=None if outcome == "success" else "oracle.mismatch",
        )


def _run(tmp_path: Path) -> tuple[Path, dict[str, object], FakeAction, FakeVerifier]:
    out = tmp_path / "run"
    action = FakeAction()
    verifier = FakeVerifier()
    report = run_loop(plan(), out, action, verifier)
    return out, report, action, verifier


def test_run_records_two_independently_verified_episodes_and_never_promotes(tmp_path: Path) -> None:
    out, report, action, verifier = _run(tmp_path)

    assert action.calls == [
        ("repair-run-1-control", None),
        ("repair-run-1-treatment", "apply the checked fix"),
    ]
    assert verifier.calls == ["repair-run-1-control", "repair-run-1-treatment"]
    assert (out / "plan.json").is_file()
    assert (out / "events.sqlite3").is_file()
    assert (out / "artifacts" / "repair-run-1-control.json").is_file()
    assert (out / "artifacts" / "repair-run-1-treatment.json").is_file()
    assert (out / "independent_receipt.json").is_file()
    assert (out / "report.json").is_file()
    assert report["decision"] == "Repair"
    assert report["reason_code"] == "gate_a_operational_only"
    assert report["arms"]["control"]["outcome"] == "failure"
    assert report["arms"]["treatment"]["outcome"] == "success"
    assert report["experience_candidate"]["source_episode_id"] == "repair-run-1-control"
    assert report["experience_candidate"]["capsule_candidate"] is False
    assert report["promotion"] == {
        "automatic_promotion_authorized": False,
        "capsule_distilled": False,
        "poi_updated": False,
        "recall_updated": False,
        "policy_updated": False,
        "source_write": False,
    }
    assert json.loads((out / "report.json").read_text(encoding="utf-8")) == report
    assert not (out / "status.json").exists()


def test_rerun_is_idempotent_and_clean_process_reproduces_report_bytes(tmp_path: Path) -> None:
    out, report, _action, _verifier = _run(tmp_path)
    expected_bytes = (out / "report.json").read_bytes()
    no_call_action = FakeAction()
    no_call_verifier = FakeVerifier()

    assert run_loop(plan(), out, no_call_action, no_call_verifier) == report
    assert no_call_action.calls == []
    assert no_call_verifier.calls == []
    assert (out / "report.json").read_bytes() == expected_bytes

    command = [
        sys.executable,
        "-c",
        (
            "import json,sys; from gep.loop_run import verify_run; "
            "print(json.dumps(verify_run(sys.argv[1]),sort_keys=True,separators=(',',':')))"
        ),
        str(out),
    ]
    completed = subprocess.run(command, check=True, capture_output=True, text=True)
    assert completed.stdout.encode("utf-8") == expected_bytes + b"\n"


@pytest.mark.parametrize("target", ["plan", "artifact", "verdict", "missing_verdict"])
def test_tampering_or_missing_independent_verdict_fails_closed(tmp_path: Path, target: str) -> None:
    out, _report, _action, _verifier = _run(tmp_path)

    if target == "plan":
        (out / "plan.json").write_text('{"tampered":true}', encoding="utf-8")
    elif target == "artifact":
        (out / "artifacts" / "repair-run-1-control.json").write_text(
            '{"tampered":true}', encoding="utf-8"
        )
    else:
        with sqlite3.connect(out / "events.sqlite3") as connection:
            connection.execute("DROP TRIGGER flywheel_events_immutable_update")
            connection.execute("DROP TRIGGER flywheel_events_immutable_delete")
            if target == "verdict":
                connection.execute(
                    "UPDATE flywheel_events SET envelope_json = ? WHERE event_kind = 'verdict'",
                    (b"{}",),
                )
            else:
                connection.execute("DELETE FROM flywheel_events WHERE event_kind = 'verdict'")

    with pytest.raises(LoopRunError):
        verify_run(out)


def test_duplicate_episode_ids_are_rejected_before_writing_any_run_state(tmp_path: Path) -> None:
    out = tmp_path / "duplicate"

    with pytest.raises(LoopRunError, match="duplicate episode_id"):
        run_loop(plan(duplicate_episode=True), out, FakeAction(), FakeVerifier())

    assert not out.exists()


def test_run_directory_contains_only_the_single_journal_and_declared_artifacts(
    tmp_path: Path,
) -> None:
    out, _report, _action, _verifier = _run(tmp_path)

    assert sorted(
        path.relative_to(out).as_posix() for path in out.rglob("*") if path.is_file()
    ) == [
        "artifacts/repair-run-1-control.json",
        "artifacts/repair-run-1-treatment.json",
        "events.sqlite3",
        "independent_receipt.json",
        "plan.json",
        "report.json",
    ]
