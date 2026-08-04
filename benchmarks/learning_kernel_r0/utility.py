"""Deterministic rebuild of context-conditioned experience utility."""

from __future__ import annotations

import math
import re
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from nacl.exceptions import BadSignatureError
from nacl.signing import VerifyKey

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json
from gep.verdict_packet import VerdictPacket, to_payload


_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_VIEW_ID_PATTERN = re.compile(r"lkr0_view_[a-z0-9_]{1,96}")
_TOKEN_PATTERN = re.compile(r"[a-z0-9][a-z0-9_.-]{0,127}")
_ROUTE_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_./-]{0,255}")
_SIGNATURE_PATTERN = re.compile(r"[0-9a-f]{128}")

R0_SIGNER_KEY_ID = "lkr0_verifier_r0"
R0_TRUSTED_PUBLIC_KEYS: Mapping[str, str] = MappingProxyType(
    {
        R0_SIGNER_KEY_ID: (
            "a2844201db7ce6fe93e77554b688361687a1e88a24ac177e7c41bc30643af1b4"
        )
    }
)
R0_VERIFIER_POLICY_HASH = hash_json(
    {
        "domain": "compass.learning_kernel.utility_trust_anchor.v1",
        "signer_key_id": R0_SIGNER_KEY_ID,
        "public_key": R0_TRUSTED_PUBLIC_KEYS[R0_SIGNER_KEY_ID],
    }
)

ContextKey = tuple[str, str, str]
UtilityKey = tuple[str, str, str, str]


@dataclass(frozen=True, slots=True)
class SignedVerdictBinding:
    """One verdict authenticated by the R0 kernel's pinned public trust root."""

    verdict: VerdictPacket
    signer_key_id: str
    signature: str
    verdict_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if not isinstance(self.verdict, VerdictPacket):
            raise TypeError("verdict must be a VerdictPacket")
        if self.verdict.verifier_policy_hash != R0_VERIFIER_POLICY_HASH:
            raise ValueError("verdict does not bind the trusted verifier policy")
        public_key = R0_TRUSTED_PUBLIC_KEYS.get(self.signer_key_id)
        if public_key is None:
            raise ValueError("untrusted signer_key_id")
        if not isinstance(self.signature, str) or _SIGNATURE_PATTERN.fullmatch(
            self.signature
        ) is None:
            raise ValueError("verdict signature must be 128 lowercase hex characters")
        payload = canonical_json_bytes(
            {
                "domain": "compass.learning_kernel.utility_verdict.v1",
                "verdict": to_payload(self.verdict),
            }
        )
        try:
            VerifyKey(bytes.fromhex(public_key)).verify(
                payload,
                bytes.fromhex(self.signature),
            )
        except BadSignatureError as exc:
            raise ValueError("verdict signature does not match the pinned trust anchor") from exc
        object.__setattr__(self, "verdict_hash", hash_json(to_payload(self.verdict)))


@dataclass(frozen=True, slots=True)
class UtilityObservation:
    context_key: ContextKey
    view_id: str
    reward: float
    result_hash: str
    signed_verdict: SignedVerdictBinding
    verdict_hash: str = field(init=False)

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
        if not isinstance(self.signed_verdict, SignedVerdictBinding):
            raise TypeError("signed_verdict must be a SignedVerdictBinding")
        verdict = self.signed_verdict.verdict
        if verdict.episode_event_hash != self.result_hash:
            raise ValueError("verdict episode_event_hash must bind the exact result_hash")
        reward_by_outcome = {"success": 1.0, "partial": 0.0, "failure": -1.0}
        expected_reward = reward_by_outcome.get(verdict.outcome)
        if expected_reward is None:
            raise ValueError("inconclusive verdict cannot update utility")
        if normalized_reward != expected_reward:
            raise ValueError("reward must match the independent verdict outcome")
        object.__setattr__(self, "verdict_hash", self.signed_verdict.verdict_hash)


def rebuild_utility(
    observations: tuple[UtilityObservation, ...],
) -> Mapping[UtilityKey, float]:
    """Rebuild exact-context utility means from authenticated observations."""

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


__all__ = [
    "ContextKey",
    "R0_SIGNER_KEY_ID",
    "R0_TRUSTED_PUBLIC_KEYS",
    "R0_VERIFIER_POLICY_HASH",
    "SignedVerdictBinding",
    "UtilityKey",
    "UtilityObservation",
    "rebuild_utility",
]
