from argparse import Namespace
from dataclasses import FrozenInstanceError, fields

import pytest

from gep.experience_packet import ExperiencePacket, from_args, to_frontmatter

EXPECTED_FIELDS = (
    "episode_id",
    "parent_episode_id",
    "task",
    "action_kind",
    "tool_chain",
    "outcome",
    "failure_mode",
    "reward_delta",
    "impact",
    "route_key",
    "capsule_candidate",
    "policy_hint",
)


def test_all_fields_are_optional():
    packet = ExperiencePacket()

    assert tuple(field.name for field in fields(packet)) == EXPECTED_FIELDS
    assert all(getattr(packet, name) is None for name in EXPECTED_FIELDS)


def test_packet_is_immutable():
    packet = ExperiencePacket(episode_id="episode-1")

    with pytest.raises(FrozenInstanceError):
        packet.episode_id = "episode-2"


def test_direct_construction_normalizes_tool_chain_to_immutable_tuple():
    tools = ["search", "verify"]
    packet = ExperiencePacket(tool_chain=tools)
    tools.append("mutate_after_construction")

    assert packet.tool_chain == ("search", "verify")


def test_to_frontmatter_serializes_complete_packet():
    packet = ExperiencePacket(
        episode_id="episode-2",
        parent_episode_id="episode-1",
        task="Diagnose a failing retrieval route",
        action_kind="tool_assisted_diagnosis",
        tool_chain=("recall", "inspect_trace", "run_test"),
        outcome="fixed",
        failure_mode="stale_route",
        reward_delta=0.75,
        impact=1.25,
        route_key="retrieval/diagnosis",
        capsule_candidate=True,
        policy_hint="prefer trace inspection before route mutation",
    )

    assert to_frontmatter(packet) == {
        "episode_id": "episode-2",
        "parent_episode_id": "episode-1",
        "task": "Diagnose a failing retrieval route",
        "action_kind": "tool_assisted_diagnosis",
        "tool_chain": ["recall", "inspect_trace", "run_test"],
        "outcome": "fixed",
        "failure_mode": "stale_route",
        "reward_delta": 0.75,
        "impact": 1.25,
        "route_key": "retrieval/diagnosis",
        "capsule_candidate": True,
        "policy_hint": "prefer trace inspection before route mutation",
    }


def test_to_frontmatter_omits_none_but_keeps_explicit_zero_and_false():
    packet = ExperiencePacket(
        reward_delta=0.0,
        impact=0.0,
        capsule_candidate=False,
    )

    assert to_frontmatter(packet) == {
        "reward_delta": 0.0,
        "impact": 0.0,
        "capsule_candidate": False,
    }


def test_from_args_accepts_namespace_and_ignores_unrelated_fields():
    args = Namespace(
        episode_id="episode-3",
        tool_chain=["search", "verify"],
        route_key="research/verify",
        verbose=True,
    )

    packet = from_args(args)

    assert packet.episode_id == "episode-3"
    assert packet.tool_chain == ("search", "verify")
    assert packet.route_key == "research/verify"
    assert not hasattr(packet, "verbose")


def test_from_args_accepts_mapping_and_explicit_overrides():
    packet = from_args(
        {
            "episode_id": "episode-4",
            "outcome": "retry",
            "unknown_future_field": "ignored",
        },
        outcome="succeeded",
        impact=2,
    )

    assert packet == ExperiencePacket(
        episode_id="episode-4",
        outcome="succeeded",
        impact=2,
    )


def test_from_args_treats_a_string_tool_as_one_tool():
    packet = from_args({"tool_chain": "single_tool"})

    assert packet.tool_chain == ("single_tool",)


def test_from_args_with_no_values_or_none_tool_chain_is_empty():
    assert from_args() == ExperiencePacket()
    assert from_args({"tool_chain": None}) == ExperiencePacket()


def test_from_args_rejects_values_that_are_not_namespace_like():
    with pytest.raises(TypeError, match="mapping, namespace-like object, or None"):
        from_args(42)


def test_from_args_rejects_unknown_explicit_override():
    with pytest.raises(TypeError, match="unknown Experience Packet field: policy_hnit"):
        from_args(policy_hnit="typo must not disappear")


@pytest.mark.parametrize(
    "tool_chain",
    [
        {"search", "verify"},
        {"first": "search"},
        b"search",
        ["search", 7],
    ],
)
def test_tool_chain_rejects_unordered_or_non_string_values(tool_chain):
    with pytest.raises(TypeError, match="tool_chain must be a string or ordered sequence"):
        ExperiencePacket(tool_chain=tool_chain)
