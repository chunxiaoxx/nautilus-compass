from __future__ import annotations

from dataclasses import replace

import pytest

from benchmarks.learning_kernel_r0.runner import (
    EvaluationTask,
    ExecutionObservation,
    VerificationObservation,
    read_result_journal,
    run_mechanism_matrix,
    write_result_journal,
)
from benchmarks.learning_kernel_r0.schema import MemoryView


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def _tasks() -> tuple[EvaluationTask, ...]:
    return (
        EvaluationTask("lkr0_task_alpha", HASH_A, "route/alpha", "repair"),
        EvaluationTask("lkr0_task_beta", HASH_B, "route/beta", "repair"),
    )


def _view_provider(
    task: EvaluationTask,
    query_class: str,
    intervention: str,
) -> tuple[MemoryView, ...]:
    if intervention == "no_memory":
        return ()
    return (
        MemoryView(
            view_id=f"lkr0_view_{task.task_id.removeprefix('lkr0_task_')}_{query_class}",
            source_packet_hash=HASH_A,
            route_key=task.route_key,
            query_class=query_class,
            action_kind=task.action_kind,
            representation="distilled",
            rendered_text="Apply the independently verified repair.",
            semantic_score=0.9,
            verification_state="independent_verified",
            verdict="success",
            lifecycle_state="active",
        ),
    )


def _executor(request) -> ExecutionObservation:
    return ExecutionObservation(
        output_text=f"observed:{request.task.task_id}:{request.query_class}",
        latency_ms=10 + request.replica,
        input_tokens=20,
        output_tokens=4,
        estimated_cost_usd=0.001,
    )


def _verifier(task, query_class, observation) -> VerificationObservation:
    expected = f"observed:{task.task_id}:{query_class}"
    return VerificationObservation(
        success=observation.output_text == expected,
        first_pass_success=observation.output_text == expected,
        verifier_code="mechanical_pass",
    )


def _run_matrix(*, executor=_executor):
    return run_mechanism_matrix(
        tasks=_tasks(),
        query_classes=("ordinary", "protected"),
        selectors=("flat", "semantic"),
        interventions=("no_memory", "distilled"),
        replicas=2,
        view_provider=_view_provider,
        executor=executor,
        verifier=_verifier,
        protected_query_classes=frozenset({"protected"}),
    )


def test_runner_produces_complete_deterministic_cartesian_product() -> None:
    first = _run_matrix()
    second = _run_matrix()

    assert first == second
    assert len(first) == 2 * 2 * 2 * 2 * 2
    assert len({row.run_id for row in first}) == len(first)
    assert len({row.result_hash for row in first}) == len(first)
    assert {row.task_hash for row in first} == {HASH_A, HASH_B}
    assert {row.replica for row in first} == {0, 1}
    assert {row.query_class for row in first} == {"ordinary", "protected"}
    assert {row.selector for row in first} == {"flat", "semantic"}
    assert {row.intervention for row in first} == {"no_memory", "distilled"}
    assert all(row.success for row in first)


def test_runner_rejects_duplicate_axes_and_invalid_observations() -> None:
    with pytest.raises(ValueError, match="query_classes must not contain duplicates"):
        run_mechanism_matrix(
            tasks=_tasks(),
            query_classes=("ordinary", "ordinary"),
            selectors=("flat",),
            interventions=("no_memory",),
            replicas=1,
            view_provider=_view_provider,
            executor=_executor,
            verifier=_verifier,
        )

    def invalid_executor(request):
        del request
        return {"latency_ms": -1}

    with pytest.raises(TypeError, match="ExecutionObservation"):
        run_mechanism_matrix(
            tasks=_tasks()[:1],
            query_classes=("ordinary",),
            selectors=("flat",),
            interventions=("no_memory",),
            replicas=1,
            view_provider=_view_provider,
            executor=invalid_executor,
            verifier=_verifier,
        )


def test_result_journal_is_canonical_idempotent_and_fails_on_conflict(tmp_path) -> None:
    results = _run_matrix()
    output_dir = tmp_path / "isolated"

    path = write_result_journal(output_dir, results)
    first_bytes = path.read_bytes()
    assert read_result_journal(output_dir) == results

    assert write_result_journal(output_dir, results) == path
    assert path.read_bytes() == first_bytes

    def changed_executor(request) -> ExecutionObservation:
        observation = _executor(request)
        return replace(observation, input_tokens=observation.input_tokens + 1)

    with pytest.raises(ValueError, match="conflicting run_id"):
        write_result_journal(output_dir, _run_matrix(executor=changed_executor))


def test_result_journal_rejects_tampered_hash(tmp_path) -> None:
    output_dir = tmp_path / "tampered"
    path = write_result_journal(output_dir, _run_matrix())
    path.write_text(
        path.read_text(encoding="utf-8").replace('"success":true', '"success":false', 1),
        encoding="utf-8",
        newline="\n",
    )

    with pytest.raises(ValueError, match="result_hash"):
        read_result_journal(output_dir)
