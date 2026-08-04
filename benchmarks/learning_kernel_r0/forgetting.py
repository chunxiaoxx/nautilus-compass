"""Reversible lifecycle selection for Compass Learning Kernel experience."""

from __future__ import annotations

from dataclasses import dataclass, replace

from .schema import LIFECYCLE_STATES, MemoryView


@dataclass(frozen=True, slots=True)
class ForgettingPolicy:
    min_active_support: int
    archive_harm_threshold: int
    recovery_support: int

    def __post_init__(self) -> None:
        _positive_int("min_active_support", self.min_active_support)
        _positive_int("archive_harm_threshold", self.archive_harm_threshold)
        _positive_int("recovery_support", self.recovery_support)
        if self.recovery_support < self.min_active_support:
            raise ValueError("recovery_support must be at least min_active_support")


def reduce_lifecycle(
    current: str,
    *,
    independent_support: int,
    verified_harm: int,
    protected_harm: bool,
    expired: bool,
    policy: ForgettingPolicy,
) -> str:
    """Return active/cooling/archived without deleting source experience."""

    if current not in LIFECYCLE_STATES:
        raise ValueError("current must be active, cooling, or archived")
    _nonnegative_int("independent_support", independent_support)
    _nonnegative_int("verified_harm", verified_harm)
    _strict_bool("protected_harm", protected_harm)
    _strict_bool("expired", expired)
    if not isinstance(policy, ForgettingPolicy):
        raise TypeError("policy must be a ForgettingPolicy")

    if protected_harm or verified_harm >= policy.archive_harm_threshold:
        return "archived"
    if current == "archived":
        if expired or independent_support < policy.recovery_support:
            return "archived"
        return "active"
    if expired or independent_support < policy.min_active_support:
        return "cooling"
    return "active"


def apply_lifecycle(
    view: MemoryView,
    *,
    independent_support: int,
    verified_harm: int,
    protected_harm: bool,
    expired: bool,
    policy: ForgettingPolicy,
) -> MemoryView:
    """Return a new view carrying reduced lifecycle state."""

    if not isinstance(view, MemoryView):
        raise TypeError("view must be a MemoryView")
    lifecycle_state = reduce_lifecycle(
        view.lifecycle_state,
        independent_support=independent_support,
        verified_harm=verified_harm,
        protected_harm=protected_harm,
        expired=expired,
        policy=policy,
    )
    return replace(view, lifecycle_state=lifecycle_state)


def forgetting_regret(
    selected_outcomes: tuple[bool, ...],
    oracle_outcomes: tuple[bool, ...],
) -> float:
    """Return non-negative success-rate regret against a matched oracle replay."""

    _bool_outcomes("selected_outcomes", selected_outcomes)
    _bool_outcomes("oracle_outcomes", oracle_outcomes)
    if len(selected_outcomes) != len(oracle_outcomes):
        raise ValueError("selected_outcomes and oracle_outcomes must have equal length")
    selected_rate = sum(selected_outcomes) / len(selected_outcomes)
    oracle_rate = sum(oracle_outcomes) / len(oracle_outcomes)
    return max(0.0, oracle_rate - selected_rate)


def _positive_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a positive integer")
    if value <= 0:
        raise ValueError(f"{name} must be positive")


def _nonnegative_int(name: str, value: object) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be a non-negative integer")
    if value < 0:
        raise ValueError(f"{name} must be non-negative")


def _strict_bool(name: str, value: object) -> None:
    if not isinstance(value, bool):
        raise TypeError(f"{name} must be a boolean")


def _bool_outcomes(name: str, values: object) -> None:
    if not isinstance(values, tuple) or not values:
        raise ValueError(f"{name} must be a non-empty tuple")
    if any(not isinstance(value, bool) for value in values):
        raise TypeError(f"{name} must contain booleans")


__all__ = [
    "ForgettingPolicy",
    "apply_lifecycle",
    "forgetting_regret",
    "reduce_lifecycle",
]
