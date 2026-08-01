from argparse import Namespace
from dataclasses import FrozenInstanceError, fields

import pytest

from gep.verdict_packet import (
    OUTCOMES,
    VERIFIER_KINDS,
    VerdictPacket,
    from_args,
    to_payload,
)


H1 = "sha256:" + "1" * 64
H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64
H4 = "sha256:" + "4" * 64

EXPECTED_FIELDS = (
    "episode_id",
    "episode_event_hash",
    "outcome",
    "verifier_kind",
    "verifier_version",
    "verifier_policy_hash",
    "evidence_hash",
    "environment_fingerprint_hash",
    "failure_class",
)


def valid_values(**overrides):
    values = {
        "episode_id": "episode-1",
        "episode_event_hash": H1,
        "outcome": "success",
        "verifier_kind": "software_test",
        "verifier_version": "pytest-8.4",
        "verifier_policy_hash": H2,
        "evidence_hash": H3,
        "environment_fingerprint_hash": H4,
        "failure_class": "test.assertion_failure",
    }
    values.update(overrides)
    return values


def test_public_enums_are_exact_frozensets():
    assert type(OUTCOMES) is frozenset
    assert OUTCOMES == frozenset({"success", "failure", "partial", "inconclusive"})
    assert type(VERIFIER_KINDS) is frozenset
    assert VERIFIER_KINDS == frozenset(
        {
            "physical",
            "software_test",
            "human_review",
            "external_acceptance",
            "simulation",
        }
    )


def test_verdict_packet_round_trip_is_exact_and_immutable():
    packet = from_args(**valid_values())

    assert tuple(field.name for field in fields(packet)) == EXPECTED_FIELDS
    assert to_payload(packet) == valid_values()
    with pytest.raises(FrozenInstanceError):
        packet.outcome = "failure"


def test_to_payload_includes_optional_fields_when_absent_and_is_detached():
    packet = VerdictPacket(
        **valid_values(environment_fingerprint_hash=None, failure_class=None)
    )

    first = to_payload(packet)
    second = to_payload(packet)
    first["episode_id"] = "mutated"

    assert first is not second
    assert second == valid_values(environment_fingerprint_hash=None, failure_class=None)
    assert packet.episode_id == "episode-1"


@pytest.mark.parametrize("value", [None, {}, object()])
def test_to_payload_rejects_non_packets(value):
    with pytest.raises(TypeError, match="packet must be a VerdictPacket"):
        to_payload(value)


@pytest.mark.parametrize(
    "factory",
    [
        pytest.param(VerdictPacket, id="direct"),
        pytest.param(from_args, id="from_args"),
    ],
)
@pytest.mark.parametrize(
    ("field_name", "value", "error_type"),
    [
        ("episode_id", None, TypeError),
        ("episode_id", 7, TypeError),
        ("episode_id", "", ValueError),
        ("episode_id", " \t", ValueError),
        ("episode_event_hash", None, TypeError),
        ("episode_event_hash", False, TypeError),
        ("episode_event_hash", "", ValueError),
        ("episode_event_hash", "1" * 64, ValueError),
        ("episode_event_hash", "sha256:" + "A" * 64, ValueError),
        ("episode_event_hash", "sha256:" + "1" * 63, ValueError),
        ("episode_event_hash", H1 + "0", ValueError),
        ("outcome", None, TypeError),
        ("outcome", 1, TypeError),
        ("outcome", "", ValueError),
        ("outcome", "Success", ValueError),
        ("outcome", "succeeded", ValueError),
        ("verifier_kind", None, TypeError),
        ("verifier_kind", 1, TypeError),
        ("verifier_kind", "", ValueError),
        ("verifier_kind", "Software_test", ValueError),
        ("verifier_kind", "llm_judge", ValueError),
        ("verifier_version", None, TypeError),
        ("verifier_version", 8.4, TypeError),
        ("verifier_version", "", ValueError),
        ("verifier_version", " \n", ValueError),
        ("verifier_policy_hash", None, TypeError),
        ("verifier_policy_hash", 2, TypeError),
        ("verifier_policy_hash", "2" * 64, ValueError),
        ("verifier_policy_hash", "sha256:" + "B" * 64, ValueError),
        ("verifier_policy_hash", "sha512:" + "2" * 64, ValueError),
        ("evidence_hash", None, TypeError),
        ("evidence_hash", [], TypeError),
        ("evidence_hash", "3" * 64, ValueError),
        ("evidence_hash", "sha256:" + "3" * 65, ValueError),
        ("evidence_hash", H3 + " ", ValueError),
        ("environment_fingerprint_hash", 4, TypeError),
        ("environment_fingerprint_hash", "", ValueError),
        ("environment_fingerprint_hash", "4" * 64, ValueError),
        ("environment_fingerprint_hash", "sha256:" + "C" * 64, ValueError),
        ("environment_fingerprint_hash", "sha256:" + "4" * 63, ValueError),
        ("failure_class", 1, TypeError),
        ("failure_class", "", ValueError),
        ("failure_class", "Failure", ValueError),
        ("failure_class", "-timeout", ValueError),
        ("failure_class", "timeout/io", ValueError),
        ("failure_class", "a" * 65, ValueError),
    ],
)
def test_direct_construction_and_from_args_reject_invalid_values_identically(
    factory,
    field_name,
    value,
    error_type,
):
    with pytest.raises(error_type) as error:
        factory(**valid_values(**{field_name: value}))

    assert field_name in str(error.value)


@pytest.mark.parametrize("outcome", sorted(OUTCOMES))
def test_failure_class_does_not_infer_or_restrict_outcome(outcome):
    packet = VerdictPacket(**valid_values(outcome=outcome, failure_class="timeout.io"))

    assert packet.outcome == outcome
    assert packet.failure_class == "timeout.io"


@pytest.mark.parametrize("failure_class", [None, "a", "a" * 64, "timeout.io-error_2"])
def test_optional_failure_class_accepts_safe_boundaries(failure_class):
    packet = VerdictPacket(**valid_values(failure_class=failure_class))

    assert packet.failure_class == failure_class


def test_from_args_accepts_exact_mapping_and_namespace_values():
    expected = VerdictPacket(**valid_values())

    assert from_args(valid_values()) == expected
    assert from_args(Namespace(**valid_values())) == expected


def test_from_args_rejects_non_namespace_like_input():
    with pytest.raises(TypeError, match="mapping, namespace-like object, or None"):
        from_args(42)


@pytest.mark.parametrize("field_name", ["reason", "evidence", "content"])
@pytest.mark.parametrize("source_kind", ["direct", "mapping", "override"])
def test_unknown_or_raw_content_fields_fail_closed(field_name, source_kind):
    values = valid_values()
    values[field_name] = "raw content must not enter the packet"

    with pytest.raises(TypeError):
        if source_kind == "direct":
            VerdictPacket(**values)
        elif source_kind == "mapping":
            from_args(values)
        else:
            from_args(valid_values(), **{field_name: values[field_name]})
