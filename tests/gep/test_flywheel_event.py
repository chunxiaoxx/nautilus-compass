import hashlib
import json
from dataclasses import FrozenInstanceError, fields

import pytest

import gep.flywheel_event as flywheel_event_module
from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    PAYLOAD_SCHEMA,
    SCHEMA_VERSION,
    FlywheelEvent,
    FlywheelEventError,
    canonical_event_bytes,
    canonical_payload_bytes,
    event_from_mapping,
    hash_payload,
    to_mapping,
)


ENVELOPE_KEYS = (
    "schema_version",
    "event_kind",
    "source_event_id",
    "episode_id",
    "parent_event_id",
    "agent_id",
    "occurred_at",
    "payload_schema",
    "payload",
    "payload_hash",
)

H1 = "sha256:" + "1" * 64
H2 = "sha256:" + "2" * 64
H3 = "sha256:" + "3" * 64
H4 = "sha256:" + "4" * 64

GOLDEN_EPISODE_PAYLOAD_HASH = (
    "sha256:dd818cfb40c10d869eecdecb2fd819cec7cc024a998d8d0180a17cbf5e7faefe"
)
GOLDEN_EPISODE_CANONICAL_BYTES = (
    b'{"agent_id":7,"episode_id":"episode-1","event_kind":"episode",'
    b'"occurred_at":"2026-07-31T12:00:00Z","parent_event_id":null,'
    b'"payload":{"episode_id":"episode-1","task":"verify a fix"},'
    b'"payload_hash":"sha256:dd818cfb40c10d869eecdecb2fd819cec7cc024a998d8d0180a17cbf5e7faefe",'
    b'"payload_schema":"compass.experience_packet.v0",'
    b'"schema_version":"compass.flywheel.event.v1",'
    b'"source_event_id":"source-1"}'
)
GOLDEN_EPISODE_EVENT_HASH = (
    "sha256:330df63cc70d74c495adfbb8c76331f5b3ab0f2820900902b7ea9bc40d69cbf9"
)


def canonical_json_bytes(value):
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def hash_canonical_json(value):
    return f"sha256:{hashlib.sha256(canonical_json_bytes(value)).hexdigest()}"


def valid_verdict_payload(**overrides):
    payload = {
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
    payload.update(overrides)
    return payload


def valid_verdict_mapping(**overrides):
    payload = overrides.pop("payload", valid_verdict_payload())
    if "payload_hash" in overrides:
        payload_hash = overrides.pop("payload_hash")
    else:
        payload_hash = hash_canonical_json(payload)
    event = {
        "schema_version": "compass.flywheel.event.v1",
        "event_kind": "verdict",
        "source_event_id": "verdict-source-1",
        "episode_id": "episode-1",
        "parent_event_id": "episode-source-1",
        "agent_id": 8,
        "occurred_at": "2026-08-01T01:00:00Z",
        "payload_schema": "compass.verdict_packet.v0",
        "payload": payload,
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


def valid_mapping(**overrides):
    payload = overrides.pop(
        "payload",
        {"episode_id": "episode-1", "task": "verify a fix"},
    )
    if "payload_hash" in overrides:
        payload_hash = overrides.pop("payload_hash")
    else:
        payload_hash = hash_payload(payload)
    event = {
        "schema_version": SCHEMA_VERSION,
        "event_kind": EVENT_KIND_EPISODE,
        "source_event_id": "source-1",
        "episode_id": "episode-1",
        "parent_event_id": None,
        "agent_id": 7,
        "occurred_at": "2026-07-31T12:00:00Z",
        "payload_schema": PAYLOAD_SCHEMA,
        "payload": payload,
        "payload_hash": payload_hash,
    }
    event.update(overrides)
    return event


def assert_rejected(mapping, reason_code=None):
    with pytest.raises(FlywheelEventError) as exc_info:
        event_from_mapping(mapping)

    assert exc_info.value.reason_code
    if reason_code is not None:
        assert exc_info.value.reason_code == reason_code


def test_constants_and_envelope_fields_are_exact():
    event = event_from_mapping(valid_mapping())

    assert SCHEMA_VERSION == "compass.flywheel.event.v1"
    assert EVENT_KIND_EPISODE == "episode"
    assert PAYLOAD_SCHEMA == "compass.experience_packet.v0"
    assert flywheel_event_module.EVENT_KIND_VERDICT == "verdict"
    assert (
        flywheel_event_module.VERDICT_PAYLOAD_SCHEMA
        == "compass.verdict_packet.v0"
    )
    assert tuple(field.name for field in fields(FlywheelEvent)) == ENVELOPE_KEYS
    assert tuple(to_mapping(event)) == ENVELOPE_KEYS


def test_s4_2_episode_canonical_bytes_and_event_hash_are_unchanged():
    event = event_from_mapping(
        valid_mapping(payload_hash=GOLDEN_EPISODE_PAYLOAD_HASH)
    )

    assert canonical_event_bytes(event) == GOLDEN_EPISODE_CANONICAL_BYTES
    assert event.event_hash == GOLDEN_EPISODE_EVENT_HASH


def test_valid_episode_round_trips_through_canonical_normalized_json():
    raw = valid_mapping(
        parent_event_id="source-0",
        payload={
            "episode_id": "episode-1",
            "task": "验证修复",
            "tool_chain": ["inspect", "验证"],
            "capsule_candidate": False,
            "failure_mode": None,
        },
    )

    event = event_from_mapping(raw)
    normalized = to_mapping(event)
    expected_payload = {
        "capsule_candidate": False,
        "episode_id": "episode-1",
        "task": "验证修复",
        "tool_chain": ["inspect", "验证"],
    }

    assert normalized["payload"] == expected_payload
    assert normalized["payload_hash"] == hash_payload(expected_payload)
    assert event.to_mapping() == normalized
    assert canonical_event_bytes(event) == json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    assert canonical_event_bytes(raw) == canonical_event_bytes(event)


def test_payload_bytes_and_hash_use_canonical_utf8_json():
    payload = {
        "task": "验证修复",
        "episode_id": "episode-1",
        "tool_chain": ("search", "验证"),
    }
    expected = (
        '{"episode_id":"episode-1","task":"验证修复",'
        '"tool_chain":["search","验证"]}'
    ).encode("utf-8")

    assert canonical_payload_bytes(payload) == expected
    assert hash_payload(payload) == f"sha256:{hashlib.sha256(expected).hexdigest()}"


def test_valid_verdict_round_trips_through_canonical_normalized_json():
    raw = valid_verdict_mapping()

    event = event_from_mapping(raw)
    normalized = to_mapping(event)
    expected_bytes = canonical_json_bytes(normalized)

    assert normalized["payload"] == valid_verdict_payload()
    assert normalized["payload_hash"] == hash_canonical_json(
        valid_verdict_payload()
    )
    assert event.to_mapping() == normalized
    assert canonical_event_bytes(event) == expected_bytes
    assert canonical_event_bytes(raw) == expected_bytes
    assert event.event_hash == hash_canonical_json(normalized)


def test_verdict_payload_normalization_includes_absent_optional_fields():
    payload = valid_verdict_payload()
    payload.pop("environment_fingerprint_hash")
    payload.pop("failure_class")
    expected_payload = {
        **payload,
        "environment_fingerprint_hash": None,
        "failure_class": None,
    }
    raw = valid_verdict_mapping(
        payload=payload,
        payload_hash=hash_canonical_json(expected_payload),
    )

    assert to_mapping(event_from_mapping(raw))["payload"] == expected_payload


def test_kind_aware_payload_hash_preserves_episode_callers_and_hashes_verdicts():
    episode_payload = {"episode_id": "episode-1", "task": "verify a fix"}
    verdict_payload = valid_verdict_payload()

    assert (
        flywheel_event_module.hash_payload_for_kind("episode", episode_payload)
        == hash_payload(episode_payload)
    )
    assert flywheel_event_module.hash_payload_for_kind(
        "verdict", verdict_payload
    ) == hash_canonical_json(verdict_payload)


def test_unknown_kind_fails_closed_in_kind_aware_payload_hash():
    with pytest.raises(FlywheelEventError) as exc_info:
        flywheel_event_module.hash_payload_for_kind(
            "future-kind",
            {"episode_id": "episode-1"},
        )

    assert exc_info.value.reason_code == "invalid_schema"


def test_event_hash_is_deterministic_and_derived_from_normalized_envelope():
    first = event_from_mapping(valid_mapping())
    second = event_from_mapping(valid_mapping())
    expected = f"sha256:{hashlib.sha256(canonical_event_bytes(first)).hexdigest()}"

    assert first.event_hash == expected
    assert second.event_hash == expected
    assert "event_hash" not in to_mapping(first)

    changed = event_from_mapping(valid_mapping(source_event_id="source-2"))
    assert changed.event_hash != first.event_hash


def test_event_hash_is_not_accepted_as_input():
    raw = valid_mapping()
    raw["event_hash"] = "sha256:" + "0" * 64

    assert_rejected(raw, "invalid_schema")


@pytest.mark.parametrize("key", ENVELOPE_KEYS)
def test_missing_envelope_key_fails_closed(key):
    raw = valid_mapping()
    raw.pop(key)

    assert_rejected(raw, "invalid_schema")


def test_unknown_envelope_key_fails_closed():
    raw = valid_mapping()
    raw["future_field"] = "must not disappear"

    assert_rejected(raw, "invalid_schema")


def test_unknown_payload_key_fails_closed():
    raw = valid_mapping(
        payload={
            "episode_id": "episode-1",
            "task": "verify a fix",
            "future_field": "must not disappear",
        },
        payload_hash="sha256:" + "0" * 64,
    )

    assert_rejected(raw, "invalid_schema")


def test_unknown_verdict_payload_key_fails_closed():
    payload = valid_verdict_payload(future_field="must not disappear")

    assert_rejected(valid_verdict_mapping(payload=payload), "invalid_schema")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("schema_version", "compass.flywheel.event.v0"),
        ("event_kind", "future-kind"),
        ("payload_schema", "compass.experience_packet.v1"),
    ],
)
def test_wrong_constants_fail_closed(field, value):
    assert_rejected(valid_mapping(**{field: value}), "invalid_schema")


@pytest.mark.parametrize(
    "mapping",
    [
        valid_mapping(payload_schema="compass.verdict_packet.v0"),
        valid_verdict_mapping(payload_schema="compass.experience_packet.v0"),
        valid_verdict_mapping(payload_schema="compass.verdict_packet.v1"),
    ],
    ids=["episode-verdict-schema", "verdict-episode-schema", "unknown-schema"],
)
def test_only_exact_event_kind_and_payload_schema_pairs_are_allowed(mapping):
    assert_rejected(mapping, "invalid_schema")


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("source_event_id", ""),
        ("source_event_id", "   "),
        ("source_event_id", None),
        ("episode_id", ""),
        ("episode_id", "   "),
        ("episode_id", 9),
        ("parent_event_id", ""),
        ("parent_event_id", "   "),
        ("parent_event_id", 9),
    ],
)
def test_invalid_ids_are_rejected(field, value):
    assert_rejected(valid_mapping(**{field: value}), "invalid_id")


def test_verdict_requires_non_null_parent_event_id():
    assert_rejected(valid_verdict_mapping(parent_event_id=None), "invalid_id")


@pytest.mark.parametrize("agent_id", [True, False, 0, -1, 1.5, "7", None])
def test_agent_id_must_be_a_positive_non_bool_integer(agent_id):
    assert_rejected(valid_mapping(agent_id=agent_id), "invalid_agent_id")


@pytest.mark.parametrize(
    "occurred_at",
    [
        "2026-07-31T12:00:00+00:00",
        "2026-07-31T06:00:00-06:00",
        "2026-07-31 12:00:00Z",
        "2026-07-31T12:00:00z",
        "2026-07-31T12:00Z",
        "2026-02-29T12:00:00Z",
        "",
        None,
    ],
)
def test_occurred_at_requires_strict_utc_rfc3339_ending_z(occurred_at):
    assert_rejected(valid_mapping(occurred_at=occurred_at), "invalid_occurred_at")


def test_fractional_seconds_are_valid_utc_rfc3339():
    event = event_from_mapping(valid_mapping(occurred_at="2026-07-31T12:00:00.123456Z"))

    assert event.occurred_at == "2026-07-31T12:00:00.123456Z"


@pytest.mark.parametrize(
    "payload_hash",
    [
        "",
        "0" * 64,
        "sha256:" + "0" * 63,
        "sha256:" + "A" * 64,
        "SHA256:" + "0" * 64,
        None,
    ],
)
def test_payload_hash_format_is_strict(payload_hash):
    assert_rejected(valid_mapping(payload_hash=payload_hash), "invalid_payload_hash")


def test_payload_hash_must_match_canonical_normalized_payload():
    assert_rejected(
        valid_mapping(payload_hash="sha256:" + "0" * 64),
        "payload_hash_mismatch",
    )


def test_verdict_payload_hash_must_match_canonical_normalized_payload():
    assert_rejected(
        valid_verdict_mapping(payload_hash="sha256:" + "0" * 64),
        "payload_hash_mismatch",
    )


def test_payload_must_be_a_mapping():
    assert_rejected(
        valid_mapping(payload=[("episode_id", "episode-1")], payload_hash="sha256:" + "0" * 64),
        "invalid_payload",
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("task", 123),
        ("capsule_candidate", "yes"),
        ("reward_delta", True),
        ("impact", "high"),
        ("route_key", []),
    ],
)
def test_invalid_experience_packet_field_types_map_to_invalid_payload(field_name, value):
    payload = {"episode_id": "episode-1", field_name: value}

    assert_rejected(
        valid_mapping(payload=payload, payload_hash="sha256:" + "0" * 64),
        "invalid_payload",
    )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("episode_event_hash", 1),
        ("outcome", 1),
        ("verifier_kind", "llm_judge"),
        ("verifier_version", ""),
        ("evidence_hash", []),
    ],
)
def test_invalid_verdict_packet_fields_map_to_invalid_payload(field_name, value):
    payload = valid_verdict_payload(**{field_name: value})

    assert_rejected(valid_verdict_mapping(payload=payload), "invalid_payload")


def test_payload_must_include_episode_id():
    payload = {"task": "verify a fix"}

    assert_rejected(valid_mapping(payload=payload), "episode_id_mismatch")


def test_payload_episode_id_must_match_envelope():
    payload = {"episode_id": "episode-2", "task": "verify a fix"}

    assert_rejected(valid_mapping(payload=payload), "episode_id_mismatch")


def test_verdict_payload_episode_id_must_match_envelope():
    payload = valid_verdict_payload(episode_id="episode-2")

    assert_rejected(valid_verdict_mapping(payload=payload), "episode_id_mismatch")


def test_nan_is_rejected_by_payload_and_event_canonicalization():
    payload = {"episode_id": "episode-1", "reward_delta": float("nan")}

    with pytest.raises(FlywheelEventError) as exc_info:
        canonical_payload_bytes(payload)
    assert exc_info.value.reason_code == "invalid_payload"

    assert_rejected(
        valid_mapping(payload=payload, payload_hash="sha256:" + "0" * 64),
        "invalid_payload",
    )


def test_event_and_payload_are_immutable_deep_copies():
    tools = ["inspect", "verify"]
    raw = valid_mapping(
        payload={
            "episode_id": "episode-1",
            "task": "verify a fix",
            "tool_chain": tools,
        }
    )
    event = event_from_mapping(raw)

    tools.append("caller-mutation")
    raw["source_event_id"] = "caller-mutated-source"
    raw["payload"]["task"] = "caller-mutated-task"

    assert event.source_event_id == "source-1"
    assert event.payload["task"] == "verify a fix"
    assert event.payload["tool_chain"] == ("inspect", "verify")

    with pytest.raises(FrozenInstanceError):
        event.source_event_id = "cannot-mutate"
    with pytest.raises(TypeError):
        event.payload["task"] = "cannot-mutate"

    exported = to_mapping(event)
    exported["payload"]["tool_chain"].append("export-mutation")
    assert event.payload["tool_chain"] == ("inspect", "verify")


def test_direct_construction_applies_the_same_validation_and_copying():
    raw = valid_mapping()
    event = FlywheelEvent(**raw)
    raw["payload"]["task"] = "caller-mutated-task"

    assert event == event_from_mapping(valid_mapping())
    assert event.payload["task"] == "verify a fix"


def test_direct_verdict_construction_applies_the_same_validation_and_copying():
    raw = valid_verdict_mapping()
    event = FlywheelEvent(**raw)
    raw["payload"]["outcome"] = "failure"

    assert event == event_from_mapping(valid_verdict_mapping())
    assert event.payload["outcome"] == "success"


@pytest.mark.parametrize(
    ("overrides", "reason_code"),
    [
        ({"parent_event_id": None}, "invalid_id"),
        (
            {"payload": valid_verdict_payload(episode_id="episode-2")},
            "episode_id_mismatch",
        ),
        ({"payload_hash": "sha256:" + "0" * 64}, "payload_hash_mismatch"),
        ({"payload_schema": "compass.experience_packet.v0"}, "invalid_schema"),
    ],
)
def test_direct_verdict_construction_enforces_envelope_invariants(
    overrides,
    reason_code,
):
    with pytest.raises(FlywheelEventError) as exc_info:
        FlywheelEvent(**valid_verdict_mapping(**overrides))

    assert exc_info.value.reason_code == reason_code


def test_event_from_mapping_rejects_non_mapping_input():
    with pytest.raises(FlywheelEventError) as exc_info:
        event_from_mapping([])

    assert exc_info.value.reason_code == "invalid_schema"
