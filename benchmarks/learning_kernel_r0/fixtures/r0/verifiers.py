"""Hidden mechanical executor/verifier for the synthetic R0 fixture."""

from __future__ import annotations

from benchmarks.learning_kernel_r0.runner import (
    ExecutionObservation,
    VerificationObservation,
)


def execute(request) -> ExecutionObservation:
    if request.query_class == "protected":
        output = "PROTECTED_OK"
    elif request.task.task_id == "lkr0_task_beta":
        output = "BETA_OK"
    elif any(
        "ACTION_ALPHA" in view.rendered_text
        and not view.rendered_text.startswith("DO_NOT_USE:")
        for view in request.selected_views
    ):
        output = "ALPHA_OK"
    else:
        output = "DEFAULT_FAIL"
    selected_tokens = sum(len(view.rendered_text.split()) for view in request.selected_views)
    return ExecutionObservation(
        output_text=output,
        latency_ms=8 + request.replica + len(request.selected_views),
        input_tokens=12 + selected_tokens,
        output_tokens=2,
        estimated_cost_usd=0.0,
    )


def verify(task, query_class, observation) -> VerificationObservation:
    if query_class == "protected":
        expected = "PROTECTED_OK"
    elif task.task_id == "lkr0_task_beta":
        expected = "BETA_OK"
    else:
        expected = "ALPHA_OK"
    passed = observation.output_text == expected
    return VerificationObservation(
        success=passed,
        first_pass_success=passed,
        verifier_code="mechanical_pass" if passed else "mechanical_fail",
    )
