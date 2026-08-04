"""Deterministic rebuild of context-conditioned experience utility."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_VIEW_ID_PATTERN = re.compile(r"lkr0_view_[a-z0-9_]{1,96}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")

ContextKey = tuple[str, str, str]
UtilityKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class UtilityObservation:
    context_key: ContextKey
    view_id: str
    reward: float
    result_hash: str
    verification_state: str
    verdict_hash: str

    def __post_init__(self) -> None:
        _validate_context_key(self.context_key)
        _validate_view_id(self.view_id)
        if isinstance(self.reward, bool) or not isinstance(self.reward, (int, float)):
            raise TypeError("reward must be a finite number")
        normalized_reward = float(self.reward)
        if not math.isfinite(normalized_reward):
            raise ValueError("reward must be finite")
        object.__setattr__(self, "reward", normalized_reward)
        _validate_hash("result_hash", self.result_hash)
        if self.verification_state != "independent_verified":
            raise ValueError("verification_state must be independent_verified")
        _validate_hash("verdict_hash", self.verdict_hash)


def rebuild_utility(
    observations: tuple[UtilityObservation, ...],
) -> Mapping[UtilityKey, float]:
    """Rebuild exact-context utility means from independent observations."""

    if not isinstance(observations, tuple):
        raise TypeError("observations must be a tuple")
    unique: dict[str, UtilityObservation] = {}
    for observation in observations:
        if not isinstance(observation, UtilityObservation):
            raise TypeError("observations must contain UtilityObservation values")
        previous = unique.get(observation.result_hash)
        if previous is not None and previous != observation:
            raise ValueError("conflicting duplicate result_hash")
        unique[observation.result_hash] = observation

    rewards: defaultdict[UtilityKey, list[float]] = defaultdict(list)
    for result_hash in sorted(unique):
        observation = unique[result_hash]
        key = (*observation.context_key, observation.view_id)
        rewards[key].append(observation.reward)
    means = {
        key: math.fsum(values) / len(values)
        for key, values in sorted(rewards.items())
    }
    return MappingProxyType(means)


def _validate_context_key(value: object) -> None:
    if not isinstance(value, tuple) or len(value) != 3:
        raise TypeError("context_key must be a three-string tuple")
    route_key, query_class, action_kind = value
    if not isinstance(route_key, str) or _ROUTE_PATTERN.fullmatch(route_key) is None:
        raise ValueError("context_key route_key must be a safe route")
    for name, token in (("query_class", query_class), ("action_kind", action_kind)):
        if not isinstance(token, str) or _TOKEN_PATTERN.fullmatch(token) is None:
            raise ValueError(f"context_key {name} must be a safe token")


def _validate_view_id(value: object) -> None:
    if not isinstance(value, str) or _VIEW_ID_PATTERN.fullmatch(value) is None:
        raise ValueError("view_id must be a stable lkr0_view_ identifier")


def _validate_hash(name: str, value: object) -> None:
    if not isinstance(value, str) or _HASH_PATTERN.fullmatch(value) is None:
        raise ValueError(f"{name} must be sha256 followed by 64 lowercase hex characters")


__all__ = ["ContextKey", "UtilityKey", "UtilityObservation", "rebuild_utility"]
