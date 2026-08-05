from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from benchmarks.live_agent_c2.schema import (
    AttemptEvidence,
    PairedEpisode,
    attempt_from_mapping,
    pair_from_mapping,
    provider_from_mapping,
    task_from_mapping,
)


HASH_A = "sha256:" + "a" * 64
HASH_B = "sha256:" + "b" * 64


def task_mapping(**overrides):
    raw = {
        "task_id": "c2_task_episodic_01",
        "query_class": "episodic_lookup",
        "route_key": "compass/c2/episodic",
        "action_kind": "answer",
        "prompt": "What temporary codename was assigned to the fictional run?",
        "memory_text": "Verified run note: the temporary codename was KESTREL-17.",
        "expected_answer": "kestrel-17",
        "verifier_kind": "exact_text",
        "protected": False,
    }
    raw.update(overrides)
    return raw


def provider_mapping(**overrides):
    raw = {
        "provider_id": "kimi",
        "model_id": "kimi-k2",
        "adapter_kind": "cli",
        "adapter_version": "0.31.0",
    }
    raw.update(overrides)
    return raw


def attempt_mapping(**overrides):
    raw = {
        "attempt_id": "c2_attempt_alpha_0001",
        "pair_id": "c2_pair_alpha_0001",
        "task_id": "c2_task_episodic_01",
        "arm": "flat",
        "order_index": 0,
        "provider_identity": provider_mapping(),
        "prompt_hash": HASH_A,
        "response_hash": HASH_B,
        "started_at": "2026-08-04T12:00:00Z",
        "latency_ms": 120,
        "input_tokens": 20,
        "output_tokens": 4,
        "estimated_cost_usd": 0.001,
        "valid": True,
        "error_code": None,
    }
    raw.update(overrides)
    return raw


def pair_mapping(**overrides):
    raw = {
        "pair_id": "c2_pair_alpha_0001",
        "task_id": "c2_task_episodic_01",
        "provider_identity": provider_mapping(),
        "replica": 0,
        "first_arm": "flat",
        "flat_attempt_id": "c2_attempt_alpha_0001",
        "governed_attempt_id": "c2_attempt_alpha_0002",
        "task_pack_hash": HASH_A,
    }
    raw.update(overrides)
    return raw


def test_task_schema_is_exact_immutable_and_content_hashed():
    task = task_from_mapping(task_mapping())
    reordered = task_from_mapping(dict(reversed(tuple(task_mapping().items()))))

    assert task == reordered
    assert task.task_hash == reordered.task_hash
    assert task.prompt_hash.startswith("sha256:")
    assert task.verifier_policy_hash.startswith("sha256:")
    assert task.task_hash != task_from_mapping(
        task_mapping(prompt="What was the temporary fictional codename?")
    ).task_hash
    with pytest.raises(FrozenInstanceError):
        task.prompt = "changed"
    with pytest.raises(TypeError, match="unknown LiveTask fields"):
        task_from_mapping(task_mapping(uid="raw-identity"))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("query_class", "future_class", "query_class"),
        ("task_id", "task-1", "task_id"),
        ("prompt", " password=not-allowed ", "prompt"),
        ("memory_text", "See https://example.invalid/raw", "memory_text"),
        ("expected_answer", "C:\\private\\answer", "expected_answer"),
        ("protected", 1, "protected"),
    ],
)
def test_task_rejects_unknown_class_unsafe_text_and_type_coercion(field, value, message):
    with pytest.raises((TypeError, ValueError), match=message):
        task_from_mapping(task_mapping(**{field: value}))


def test_protected_tasks_cannot_receive_memory_and_nonprotected_tasks_require_it():
    with pytest.raises(ValueError, match="protected_noop"):
        task_from_mapping(task_mapping(query_class="protected_noop", protected=False))
    with pytest.raises(ValueError, match="memory_text"):
        task_from_mapping(
            task_mapping(
                query_class="protected_noop",
                protected=True,
                memory_text="An injected hint.",
            )
        )
    with pytest.raises(ValueError, match="memory_text"):
        task_from_mapping(task_mapping(memory_text=None))


def test_provider_attempt_and_pair_schemas_are_strict_and_hashable():
    provider = provider_from_mapping(provider_mapping())
    attempt = attempt_from_mapping(attempt_mapping())
    pair = pair_from_mapping(pair_mapping())

    assert provider.provider_key == "kimi/kimi-k2"
    assert isinstance(attempt, AttemptEvidence)
    assert attempt.attempt_hash.startswith("sha256:")
    assert isinstance(pair, PairedEpisode)
    assert pair.pair_hash.startswith("sha256:")
    with pytest.raises(TypeError, match="unknown ProviderIdentity fields"):
        provider_from_mapping(provider_mapping(account_id="forbidden"))
    with pytest.raises(TypeError, match="unknown AttemptEvidence fields"):
        attempt_from_mapping(attempt_mapping(raw_response="forbidden"))
    with pytest.raises(TypeError, match="unknown PairedEpisode fields"):
        pair_from_mapping(pair_mapping(session_id="forbidden"))


def test_attempt_validity_and_pair_identity_fail_closed():
    unknown_cost = attempt_from_mapping(attempt_mapping(estimated_cost_usd=None))
    assert unknown_cost.estimated_cost_usd is None

    with pytest.raises(ValueError, match="valid attempt"):
        attempt_from_mapping(attempt_mapping(error_code="timeout"))
    with pytest.raises(ValueError, match="invalid attempt"):
        attempt_from_mapping(
            attempt_mapping(valid=False, response_hash=None, error_code=None)
        )
    with pytest.raises(ValueError, match="first_arm"):
        pair_from_mapping(pair_mapping(first_arm="candidate"))
    with pytest.raises(ValueError, match="attempt_id"):
        pair_from_mapping(
            pair_mapping(
                flat_attempt_id="c2_attempt_same_0001",
                governed_attempt_id="c2_attempt_same_0001",
            )
        )
