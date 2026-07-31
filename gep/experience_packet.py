"""Experience Packet v0 for the Compass S4 Agent Harness flywheel.

An Experience Packet is a side-effect-free record of one agent episode.  It is the
atomic, SFT-like sample that later stages may evaluate with reinforcement signals,
use to update route preferences, or distill into a memory capsule.  This module only
defines the packet boundary; it does not perform any of those later-stage actions.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from typing import Any


@dataclass(frozen=True)
class ExperiencePacket:
    """Optional metadata captured from one agent-harness episode."""

    episode_id: str | None = None
    parent_episode_id: str | None = None
    task: str | None = None
    action_kind: str | None = None
    tool_chain: Sequence[str] | None = None
    outcome: str | None = None
    failure_mode: str | None = None
    reward_delta: float | None = None
    impact: float | None = None
    route_key: str | None = None
    capsule_candidate: bool | None = None
    policy_hint: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "tool_chain", _normalize_tool_chain(self.tool_chain))


_FIELD_NAMES = tuple(field.name for field in fields(ExperiencePacket))


def _normalize_tool_chain(value: Any) -> tuple[str, ...] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return (value,)
    if not isinstance(value, Sequence) or isinstance(value, (bytes, bytearray)):
        raise TypeError("tool_chain must be a string or ordered sequence of strings")
    normalized = tuple(value)
    if any(not isinstance(tool, str) for tool in normalized):
        raise TypeError("tool_chain must be a string or ordered sequence of strings")
    return normalized


def from_args(
    args: Mapping[str, Any] | object | None = None,
    **overrides: Any,
) -> ExperiencePacket:
    """Build a packet from argparse-style arguments or a mapping.

    Only Experience Packet fields are read.  Unrelated arguments are ignored so a
    caller can pass an existing ``argparse.Namespace`` without changing its parser.
    Explicit keyword values override values read from ``args``.
    """

    if args is None:
        source: Mapping[str, Any] = {}
    elif isinstance(args, Mapping):
        source = args
    else:
        try:
            source = vars(args)
        except TypeError as exc:
            raise TypeError("args must be a mapping, namespace-like object, or None") from exc

    unknown_overrides = sorted(set(overrides) - set(_FIELD_NAMES))
    if unknown_overrides:
        label = "field" if len(unknown_overrides) == 1 else "fields"
        names = ", ".join(unknown_overrides)
        raise TypeError(f"unknown Experience Packet {label}: {names}")

    values = {name: source[name] for name in _FIELD_NAMES if name in source}
    values.update(overrides)
    return ExperiencePacket(**values)


def to_frontmatter(packet: ExperiencePacket) -> dict[str, Any]:
    """Return frontmatter-ready metadata, omitting fields that were not supplied."""

    frontmatter = {
        name: getattr(packet, name)
        for name in _FIELD_NAMES
        if getattr(packet, name) is not None
    }
    if "tool_chain" in frontmatter:
        frontmatter["tool_chain"] = list(frontmatter["tool_chain"])
    return frontmatter


__all__ = ["ExperiencePacket", "from_args", "to_frontmatter"]
