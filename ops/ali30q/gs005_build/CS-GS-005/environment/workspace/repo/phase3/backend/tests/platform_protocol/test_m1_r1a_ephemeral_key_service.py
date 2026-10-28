from __future__ import annotations

import inspect

import platform_protocol
import platform_protocol.service as service_module
from platform_protocol.m1_r1a_ephemeral_key_admission import (
    EPHEMERAL_EXECUTOR_ID,
    EPHEMERAL_EXECUTOR_KEY_ID,
    EPHEMERAL_EXECUTOR_RELEASE,
    R1aEphemeralExecutorAdmissionV1,
)
from platform_protocol.m1_r1a_routing import (
    R1A_EXECUTOR_ID,
    R1A_EXECUTOR_KEY_ID,
    R1A_EXECUTOR_RELEASE,
)
from platform_protocol.service import ProtocolService


def test_r1a_routing_uses_the_source_bound_ephemeral_executor_identity() -> None:
    assert R1A_EXECUTOR_RELEASE == "rel_r1a_ephemeral_v3"
    assert R1A_EXECUTOR_KEY_ID == "key_r1a_ephemeral_v3"
    assert R1A_EXECUTOR_ID == EPHEMERAL_EXECUTOR_ID
    assert R1A_EXECUTOR_RELEASE == EPHEMERAL_EXECUTOR_RELEASE
    assert R1A_EXECUTOR_KEY_ID == EPHEMERAL_EXECUTOR_KEY_ID
    assert not hasattr(service_module, "R1A_EXECUTOR_PUBLIC_KEY_MATERIAL")


def test_service_requires_the_challenge_transcript_and_exposes_registration() -> None:
    constructor = inspect.signature(ProtocolService).parameters
    registration = inspect.signature(
        ProtocolService.register_r1a_ephemeral_executor_key
    ).parameters

    assert "r1a_ephemeral_challenge" in constructor
    assert "r1a_ephemeral_announcement_bytes" in constructor
    assert tuple(registration) == ("self", "now")
    assert (
        platform_protocol.R1aEphemeralExecutorAdmissionV1
        is R1aEphemeralExecutorAdmissionV1
    )
