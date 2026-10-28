"""Pure unique-executor selection for the bounded R1a synthetic repair path."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from platform_protocol.contracts import ProtocolViolation
from platform_protocol.m1_r1a_runtime_admission import R1aRuntimeAdmissionDecision

R1A_CAPABILITY = "synthetic_code_repair_v1"
R1A_EXECUTOR_ID = "exec_r1a_synthetic_01"
R1A_EXECUTOR_RELEASE = "rel_r1a_ephemeral_v3"
R1A_EXECUTOR_KEY_ID = "key_r1a_ephemeral_v3"
R1A_POLICY_VERSION = "pol_r1a_synthetic_repair_v1"
R1A_TOOL_POLICY_HASH = (
    "8ee996ea414ea5abf87ce88393e817563a94dc5203f5af48ddb133218a4410fb"
)
_ADMITTED_STATUS = "admitted_for_local_r1a_synthetic_repair"


@dataclass(frozen=True, slots=True)
class R1aExecutorCandidateV1:
    """One source-derived candidate before the unique selection is frozen."""

    identity_id: str
    release: str
    role: str
    key_id: str
    capability: str
    policy_version: str
    tool_policy_hash: str
    active: bool


@dataclass(frozen=True, slots=True)
class R1aExecutorSelectionV1:
    """The complete immutable result accepted by the R1a attempt command."""

    executor_id: str
    executor_release: str
    executor_key_id: str
    capability: str
    policy_version: str
    tool_policy_hash: str


def select_unique_executor(
    candidates: Sequence[R1aExecutorCandidateV1],
    *,
    capability: str,
    executor_release: str,
    policy_version: str,
    tool_policy_hash: str,
    owner_admission: R1aRuntimeAdmissionDecision,
) -> R1aExecutorSelectionV1:
    """Return the only exact admitted candidate or fail closed."""
    expected_candidate = R1aExecutorCandidateV1(
        identity_id=R1A_EXECUTOR_ID,
        release=R1A_EXECUTOR_RELEASE,
        role="executor",
        key_id=R1A_EXECUTOR_KEY_ID,
        capability=R1A_CAPABILITY,
        policy_version=R1A_POLICY_VERSION,
        tool_policy_hash=R1A_TOOL_POLICY_HASH,
        active=True,
    )
    if (
        owner_admission
        != R1aRuntimeAdmissionDecision(status=_ADMITTED_STATUS, reason_codes=())
        or capability != R1A_CAPABILITY
        or executor_release != R1A_EXECUTOR_RELEASE
        or policy_version != R1A_POLICY_VERSION
        or tool_policy_hash != R1A_TOOL_POLICY_HASH
        or len(candidates) != 1
        or candidates[0] != expected_candidate
    ):
        raise ProtocolViolation("executor_selection_required")
    return R1aExecutorSelectionV1(
        executor_id=expected_candidate.identity_id,
        executor_release=expected_candidate.release,
        executor_key_id=expected_candidate.key_id,
        capability=expected_candidate.capability,
        policy_version=expected_candidate.policy_version,
        tool_policy_hash=expected_candidate.tool_policy_hash,
    )
