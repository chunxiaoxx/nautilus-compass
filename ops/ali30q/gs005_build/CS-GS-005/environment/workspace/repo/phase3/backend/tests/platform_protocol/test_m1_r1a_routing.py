"""Pure, fail-closed executor selection for the one admitted R1a capability."""

from __future__ import annotations

from dataclasses import replace

import pytest

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.m1_r1a_routing import (
    R1A_CAPABILITY,
    R1A_EXECUTOR_ID,
    R1A_EXECUTOR_KEY_ID,
    R1A_EXECUTOR_RELEASE,
    R1A_POLICY_VERSION,
    R1A_TOOL_POLICY_HASH,
    R1aExecutorCandidateV1,
    R1aExecutorSelectionV1,
    select_unique_executor,
)
from platform_protocol.m1_r1a_runtime_admission import R1aRuntimeAdmissionDecision


def _admission() -> R1aRuntimeAdmissionDecision:
    return R1aRuntimeAdmissionDecision(
        status="admitted_for_local_r1a_synthetic_repair",
        reason_codes=(),
    )


def _candidate() -> R1aExecutorCandidateV1:
    return R1aExecutorCandidateV1(
        identity_id=R1A_EXECUTOR_ID,
        release=R1A_EXECUTOR_RELEASE,
        role="executor",
        key_id=R1A_EXECUTOR_KEY_ID,
        capability=R1A_CAPABILITY,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        active=True,
    )


def _select(
    candidates: tuple[R1aExecutorCandidateV1, ...],
    *,
    owner_admission: R1aRuntimeAdmissionDecision | None = None,
) -> R1aExecutorSelectionV1:
    return select_unique_executor(
        candidates,
        capability=R1A_CAPABILITY,
        executor_release=R1A_EXECUTOR_RELEASE,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        owner_admission=owner_admission or _admission(),
    )


def test_selects_the_one_exact_source_admitted_executor() -> None:
    selected = _select((_candidate(),))

    assert selected == R1aExecutorSelectionV1(
        executor_id=R1A_EXECUTOR_ID,
        executor_release=R1A_EXECUTOR_RELEASE,
        executor_key_id=R1A_EXECUTOR_KEY_ID,
        capability=R1A_CAPABILITY,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
    )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("identity_id", "exec_other_01"),
        ("release", "rel_other_01"),
        ("role", "verifier"),
        ("key_id", "key_other_01"),
        ("capability", "other_capability"),
        ("policy_version", "pol_other_01"),
        ("tool_policy_hash", "f" * 64),
        ("active", False),
    ],
)
def test_changed_candidate_binding_fails_closed(field: str, value: object) -> None:
    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        _select((replace(_candidate(), **{field: value}),))


def test_zero_or_multiple_candidates_fail_closed() -> None:
    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        _select(())
    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        _select((_candidate(), _candidate()))


@pytest.mark.parametrize(
    "admission",
    [
        R1aRuntimeAdmissionDecision(
            status="blocked",
            reason_codes=("v5_executor_owner_input_missing",),
        ),
        R1aRuntimeAdmissionDecision(
            status="admitted_for_local_r1a_synthetic_repair",
            reason_codes=("unexpected",),
        ),
    ],
)
def test_blocked_or_inconsistent_owner_admission_fails_closed(
    admission: R1aRuntimeAdmissionDecision,
) -> None:
    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        _select((_candidate(),), owner_admission=admission)


@pytest.mark.parametrize(
    ("argument", "value"),
    [
        ("capability", "other_capability"),
        ("executor_release", "rel_other_01"),
        ("policy_version", "pol_other_01"),
        ("tool_policy_hash", "f" * 64),
    ],
)
def test_changed_requested_binding_fails_closed(argument: str, value: str) -> None:
    kwargs = {
        "capability": R1A_CAPABILITY,
        "executor_release": R1A_EXECUTOR_RELEASE,
        "policy_version": R1A_POLICY_VERSION,
        "tool_policy_hash": R1A_TOOL_POLICY_HASH,
    }
    kwargs[argument] = value

    with pytest.raises(ProtocolViolation, match="executor_selection_required"):
        select_unique_executor(
            (_candidate(),),
            owner_admission=_admission(),
            **kwargs,
        )
