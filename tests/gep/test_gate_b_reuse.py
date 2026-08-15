from __future__ import annotations

from pathlib import Path

import pytest

from gep.loop_run import ActionArtifact, ActionExecutionFailure, LoopRunError, run_loop, verify_run
from gep.verdict_packet import VerdictPacket


H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64


def _plan() -> dict[str, object]:
    return {
        "schema_version": "compass.loop.plan.v2",
        "run_id": "gate-b-reuse-1",
        "task": {
            "cases": {
                "source": {
                    "id": "source-normalize",
                    "prompt": "Repair the source parser failure.",
                },
                "transfer": {
                    "id": "transfer-normalize",
                    "prompt": "Repair the related parser failure.",
                },
            }
        },
        "oracle": {
            "cases": {
                "source": {"expected": "source-fixed"},
                "transfer": {"expected": "transfer-fixed"},
            },
            "primary_metric": "verified_success",
            "minimum_utility_delta": 1,
            "protected_failure_classes": ["safety.violation", "oracle.regression"],
        },
        "action_agent_id": 7,
        "verifier_agent_id": 8,
        "verifier_policy_hash": H2,
        "environment_fingerprint_hash": H3,
        "arms": [
            {
                "label": "source",
                "episode_id": "gate-b-source",
                "task_case_id": "source",
                "advice_from_episode_id": None,
                "occurred_at": "2026-08-15T00:00:00Z",
            },
            {
                "label": "control",
                "episode_id": "gate-b-control",
                "task_case_id": "transfer",
                "advice_from_episode_id": None,
                "occurred_at": "2026-08-15T00:01:00Z",
            },
            {
                "label": "treatment",
                "episode_id": "gate-b-treatment",
                "task_case_id": "transfer",
                "advice_from_episode_id": "gate-b-source",
                "occurred_at": "2026-08-15T00:02:00Z",
            },
        ],
    }


class _Action:
    def __init__(self, *, include_reuse_advice: bool = True) -> None:
        self.include_reuse_advice = include_reuse_advice
        self.calls: list[tuple[dict[str, object], str | None]] = []

    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact:
        del work_dir
        self.calls.append((task, advice))
        if task["task_case_id"] == "source":
            content: dict[str, object] = {"answer": "source-fixed"}
            if self.include_reuse_advice:
                content["reuse_advice"] = "normalize parser input before validation"
        elif advice == "normalize parser input before validation":
            content = {"answer": "transfer-fixed"}
        else:
            content = {"answer": "transfer-broken"}
        return ActionArtifact(
            episode_id=str(task["episode_id"]),
            content=content,
            tool_chain=("isolated_edit", "isolated_test"),
        )


class _Verifier:
    def __init__(self) -> None:
        self.tasks: list[dict[str, object]] = []

    def verify(
        self,
        task: dict[str, object],
        artifact: ActionArtifact,
        oracle: dict[str, object],
    ) -> VerdictPacket:
        self.tasks.append(task)
        expected = oracle["cases"][task["task_case_id"]]["expected"]
        outcome = "success" if artifact.content.get("answer") == expected else "failure"
        return VerdictPacket(
            episode_id=artifact.episode_id,
            episode_event_hash=artifact.episode_event_hash or "",
            outcome=outcome,
            verifier_kind="software_test",
            verifier_version="gate-b-fake-oracle-v1",
            verifier_policy_hash=H2,
            evidence_hash=artifact.evidence_hash,
            environment_fingerprint_hash=H3,
            failure_class=artifact.content.get("failure_reason") if outcome == "failure" else None,
        )


def test_gate_b_binds_a_verified_source_experience_to_an_unseen_transfer_comparison(
    tmp_path: Path,
) -> None:
    action = _Action()
    verifier = _Verifier()

    report = run_loop(_plan(), tmp_path / "run", action, verifier)

    assert [advice for _task, advice in action.calls] == [
        None,
        None,
        "normalize parser input before validation",
    ]
    assert all("arm" not in task and "label" not in task for task in verifier.tasks)
    assert report["decision"] == "Gold"
    assert report["reason_code"] == "gate_b_positive_reuse_delta"
    assert report["reuse_evaluation"] == {
        "source_outcome": "success",
        "control_success": 0,
        "treatment_success": 1,
        "utility_delta": 1,
        "minimum_utility_delta": 1,
        "protected_regressions": [],
    }
    assert report["experience_candidate"] == {
        "source_episode_id": "gate-b-source",
        "candidate_state": "candidate_only",
        "capsule_candidate": True,
    }
    assert all(value is False for value in report["promotion"].values())
    assert verify_run(tmp_path / "run") == report


def test_gate_b_records_repair_when_a_source_action_has_no_reusable_experience(
    tmp_path: Path,
) -> None:
    report = run_loop(_plan(), tmp_path / "run", _Action(include_reuse_advice=False), _Verifier())

    assert report["decision"] == "Repair"
    assert report["reason_code"] == "gate_b_delta_not_positive"
    assert report["arms"]["treatment"]["outcome"] == "failure"
    assert verify_run(tmp_path / "run") == report


def test_gate_b_rejects_static_treatment_advice_before_writing_evidence(tmp_path: Path) -> None:
    plan = _plan()
    plan["arms"][2]["advice"] = "smuggled static hint"  # type: ignore[index]

    with pytest.raises(LoopRunError, match="arm keys are invalid"):
        run_loop(plan, tmp_path / "run", _Action(), _Verifier())


class _SourceFailureAction(_Action):
    def execute(
        self,
        task: dict[str, object],
        advice: str | None,
        work_dir: Path,
    ) -> ActionArtifact:
        if task["task_case_id"] == "source":
            self.calls.append((task, advice))
            raise ActionExecutionFailure("provider_timeout")
        return super().execute(task, advice, work_dir)


def test_gate_b_preserves_a_terminal_source_failure_as_replayable_repair_evidence(
    tmp_path: Path,
) -> None:
    action = _SourceFailureAction()
    report = run_loop(_plan(), tmp_path / "run", action, _Verifier())

    assert [task["task_case_id"] for task, _advice in action.calls] == ["source", "transfer"]
    assert report["decision"] == "Repair"
    assert report["reason_code"] == "gate_b_source_not_verified_success"
    assert report["arms"]["source"]["outcome"] == "failure"
    assert report["arms"]["treatment"]["outcome"] == "failure"
    assert verify_run(tmp_path / "run") == report
