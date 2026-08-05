"""ExperiencePacket, flywheel verdict, signature, and PoI projection for C2."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from benchmarks.poi_gate2.canonical import canonical_json_bytes, hash_json
from gep.experience_packet import ExperiencePacket, to_frontmatter
from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    EVENT_KIND_VERDICT,
    PAYLOAD_SCHEMA,
    SCHEMA_VERSION,
    VERDICT_PAYLOAD_SCHEMA,
    FlywheelEvent,
    event_from_mapping,
    hash_payload_for_kind,
)
from gep.flywheel_log import FlywheelEventLog
from gep.verdict_packet import VerdictPacket, to_payload as verdict_to_payload

from .runner import ExecutedArm
from .schema import LiveTask, provider_to_mapping
from .verifier import VerificationResult, verify_output


_SIGNATURE_PATTERN = re.compile(r"[0-9a-f]{128}")
_PUBLIC_KEY_PATTERN = re.compile(r"[0-9a-f]{64}")


@dataclass(frozen=True, slots=True)
class PoiSignal:
    reward_delta: float
    impact: float
    verdict_hash: str
    signal_hash: str = field(init=False)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "signal_hash",
            hash_json(
                {
                    "domain": "compass.live_agent_c2.poi_signal.v1",
                    "impact": self.impact,
                    "reward_delta": self.reward_delta,
                    "verdict_hash": self.verdict_hash,
                }
            ),
        )


@dataclass(frozen=True, slots=True)
class EpisodeEvidenceBundle:
    task_hash: str
    task_pack_hash: str
    attempt_hash: str
    selected_view_ids: tuple[str, ...]
    packet: ExperiencePacket
    episode_event: FlywheelEvent
    verification: VerificationResult
    verdict: VerdictPacket
    verdict_event: FlywheelEvent
    verifier_public_key: str
    verdict_signature: str
    poi_signal: PoiSignal
    bundle_hash: str = field(init=False)

    def __post_init__(self) -> None:
        if _PUBLIC_KEY_PATTERN.fullmatch(self.verifier_public_key) is None:
            raise ValueError("verifier_public_key must be 64 lowercase hex characters")
        if _SIGNATURE_PATTERN.fullmatch(self.verdict_signature) is None:
            raise ValueError("verdict_signature must be 128 lowercase hex characters")
        object.__setattr__(self, "bundle_hash", _bundle_hash(self))


def project_episode(
    arm: ExecutedArm,
    *,
    task: LiveTask,
    task_pack_hash: str,
    event_log: FlywheelEventLog,
    action_agent_id: int,
    verifier_agent_id: int,
    signing_key: Any,
) -> EpisodeEvidenceBundle:
    _validate_projection_inputs(
        arm,
        task,
        task_pack_hash,
        event_log,
        action_agent_id,
        verifier_agent_id,
        signing_key,
    )
    verification = verify_output(task, arm.output_text)
    if verification.response_hash != arm.attempt.response_hash:
        raise ValueError("attempt response_hash does not match verifier response_hash")
    packet = _experience_packet(arm, task, verification)
    episode_event = _episode_event(packet, arm, action_agent_id)
    _append_exact(event_log, episode_event)
    verdict = _verdict(task, arm, verification, episode_event, task_pack_hash)
    verdict_event = _verdict_event(verdict, episode_event, arm, verifier_agent_id)
    _append_exact(event_log, verdict_event)
    signature_payload = _signature_payload(verdict, task_pack_hash)
    signature = signing_key.sign(signature_payload).signature.hex()
    public_key = signing_key.verify_key.encode().hex()
    poi_signal = _poi_signal(arm, task, verdict)
    bundle = EpisodeEvidenceBundle(
        task_hash=task.task_hash,
        task_pack_hash=task_pack_hash,
        attempt_hash=arm.attempt.attempt_hash,
        selected_view_ids=arm.selected_view_ids,
        packet=packet,
        episode_event=episode_event,
        verification=verification,
        verdict=verdict,
        verdict_event=verdict_event,
        verifier_public_key=public_key,
        verdict_signature=signature,
        poi_signal=poi_signal,
    )
    verify_episode_bundle(bundle, event_log=event_log)
    return bundle


def verify_episode_bundle(
    bundle: EpisodeEvidenceBundle,
    *,
    event_log: FlywheelEventLog,
) -> bool:
    if not isinstance(bundle, EpisodeEvidenceBundle):
        raise TypeError("bundle must be an EpisodeEvidenceBundle")
    if not isinstance(event_log, FlywheelEventLog):
        raise TypeError("event_log must be a FlywheelEventLog")
    episode = event_log.get(bundle.episode_event.source_event_id)
    verdict_event = event_log.get(bundle.verdict_event.source_event_id)
    if episode is None or episode.event_hash != bundle.episode_event.event_hash:
        raise ValueError("episode event replay mismatch")
    if verdict_event is None or verdict_event.event_hash != bundle.verdict_event.event_hash:
        raise ValueError("verdict event replay mismatch")
    if episode.to_mapping()["payload"] != to_frontmatter(bundle.packet):
        raise ValueError("episode payload replay mismatch")
    if verdict_event.to_mapping()["payload"] != verdict_to_payload(bundle.verdict):
        raise ValueError("verdict payload replay mismatch")
    if bundle.verdict.episode_event_hash != episode.event_hash:
        raise ValueError("verdict episode event binding mismatch")
    _verify_signature(bundle)
    if bundle.poi_signal != _poi_signal_from_values(
        arm=_packet_arm(bundle.packet),
        protected=bundle.packet.route_key == "compass/c2/protected",
        verdict=bundle.verdict,
    ):
        raise ValueError("PoI signal replay mismatch")
    if bundle.bundle_hash != _bundle_hash(bundle):
        raise ValueError("bundle hash replay mismatch")
    return True


def _experience_packet(
    arm: ExecutedArm,
    task: LiveTask,
    verification: VerificationResult,
) -> ExperiencePacket:
    success = verification.success
    reward = 1.0 if success else -1.0
    impact = reward if arm.arm == "governed" and not task.protected else 0.0
    return ExperiencePacket(
        episode_id=_episode_id(arm),
        parent_episode_id=None,
        task=f"{task.task_id}@{task.task_hash}",
        action_kind=task.action_kind,
        tool_chain=(f"provider:{arm.attempt.provider_identity.provider_key}",),
        outcome="success" if success else "failure",
        failure_mode=None if success else verification.verifier_code,
        reward_delta=reward,
        impact=impact,
        route_key=task.route_key,
        capsule_candidate=False,
        policy_hint=(
            "flat baseline" if arm.arm == "flat" else "governed verified view"
        ),
    )


def _episode_event(
    packet: ExperiencePacket,
    arm: ExecutedArm,
    action_agent_id: int,
) -> FlywheelEvent:
    payload = to_frontmatter(packet)
    return event_from_mapping(
        {
            "schema_version": SCHEMA_VERSION,
            "event_kind": EVENT_KIND_EPISODE,
            "source_event_id": f"c2_episode_event_{arm.attempt.attempt_id}",
            "episode_id": packet.episode_id,
            "parent_event_id": None,
            "agent_id": action_agent_id,
            "occurred_at": arm.attempt.started_at,
            "payload_schema": PAYLOAD_SCHEMA,
            "payload": payload,
            "payload_hash": hash_payload_for_kind(EVENT_KIND_EPISODE, payload),
        }
    )


def _verdict(
    task: LiveTask,
    arm: ExecutedArm,
    verification: VerificationResult,
    episode_event: FlywheelEvent,
    task_pack_hash: str,
) -> VerdictPacket:
    evidence_hash = hash_json(
        {
            "attempt_hash": arm.attempt.attempt_hash,
            "domain": "compass.live_agent_c2.verdict_evidence.v1",
            "task_pack_hash": task_pack_hash,
            "verification_evidence_hash": verification.evidence_hash,
        }
    )
    return VerdictPacket(
        episode_id=episode_event.episode_id,
        episode_event_hash=episode_event.event_hash,
        outcome="success" if verification.success else "failure",
        verifier_kind="software_test",
        verifier_version="compass-c2-deterministic-v1",
        verifier_policy_hash=task.verifier_policy_hash,
        evidence_hash=evidence_hash,
        environment_fingerprint_hash=hash_json(
            {
                "domain": "compass.live_agent_c2.provider_environment.v1",
                "provider": provider_to_mapping(arm.attempt.provider_identity),
            }
        ),
        failure_class=None if verification.success else verification.verifier_code,
    )


def _verdict_event(
    verdict: VerdictPacket,
    episode_event: FlywheelEvent,
    arm: ExecutedArm,
    verifier_agent_id: int,
) -> FlywheelEvent:
    payload = verdict_to_payload(verdict)
    return event_from_mapping(
        {
            "schema_version": SCHEMA_VERSION,
            "event_kind": EVENT_KIND_VERDICT,
            "source_event_id": f"c2_verdict_event_{arm.attempt.attempt_id}",
            "episode_id": verdict.episode_id,
            "parent_event_id": episode_event.source_event_id,
            "agent_id": verifier_agent_id,
            "occurred_at": arm.attempt.started_at,
            "payload_schema": VERDICT_PAYLOAD_SCHEMA,
            "payload": payload,
            "payload_hash": hash_payload_for_kind(EVENT_KIND_VERDICT, payload),
        }
    )


def _poi_signal(arm: ExecutedArm, task: LiveTask, verdict: VerdictPacket) -> PoiSignal:
    return _poi_signal_from_values(arm=arm.arm, protected=task.protected, verdict=verdict)


def _poi_signal_from_values(
    *, arm: str, protected: bool, verdict: VerdictPacket
) -> PoiSignal:
    reward = 1.0 if verdict.outcome == "success" else -1.0
    impact = reward if arm == "governed" and not protected else 0.0
    return PoiSignal(
        reward_delta=reward,
        impact=impact,
        verdict_hash=hash_json(verdict_to_payload(verdict)),
    )


def _append_exact(event_log: FlywheelEventLog, event: FlywheelEvent) -> None:
    receipt = event_log.append(event.to_mapping())
    if receipt.status not in {"accepted", "duplicate"} or receipt.event_hash != event.event_hash:
        raise ValueError(f"event admission failed: {receipt.reason_code or receipt.status}")


def _signature_payload(verdict: VerdictPacket, task_pack_hash: str) -> bytes:
    return canonical_json_bytes(
        {
            "domain": "compass.live_agent_c2.verdict_signature.v1",
            "task_pack_hash": task_pack_hash,
            "verdict": verdict_to_payload(verdict),
        }
    )


def _verify_signature(bundle: EpisodeEvidenceBundle) -> None:
    try:
        from nacl.exceptions import BadSignatureError
        from nacl.signing import VerifyKey

        VerifyKey(bytes.fromhex(bundle.verifier_public_key)).verify(
            _signature_payload(bundle.verdict, bundle.task_pack_hash),
            bytes.fromhex(bundle.verdict_signature),
        )
    except (BadSignatureError, ValueError) as exc:
        raise ValueError("verdict signature verification failed") from exc


def _bundle_hash(bundle: EpisodeEvidenceBundle) -> str:
    return hash_json(
        {
            "attempt_hash": bundle.attempt_hash,
            "domain": "compass.live_agent_c2.episode_bundle.v1",
            "episode_event_hash": bundle.episode_event.event_hash,
            "poi_signal_hash": bundle.poi_signal.signal_hash,
            "selected_view_ids": list(bundle.selected_view_ids),
            "task_hash": bundle.task_hash,
            "task_pack_hash": bundle.task_pack_hash,
            "verdict_event_hash": bundle.verdict_event.event_hash,
            "verdict_signature": bundle.verdict_signature,
            "verifier_public_key": bundle.verifier_public_key,
            "verification_evidence_hash": bundle.verification.evidence_hash,
        }
    )


def _episode_id(arm: ExecutedArm) -> str:
    return "c2_episode_" + arm.attempt.attempt_hash.removeprefix("sha256:")[:24]


def _packet_arm(packet: ExperiencePacket) -> str:
    if packet.policy_hint == "flat baseline":
        return "flat"
    if packet.policy_hint == "governed verified view":
        return "governed"
    raise ValueError("packet policy_hint does not identify a C2 arm")


def _validate_projection_inputs(
    arm: ExecutedArm,
    task: LiveTask,
    task_pack_hash: str,
    event_log: FlywheelEventLog,
    action_agent_id: int,
    verifier_agent_id: int,
    signing_key: Any,
) -> None:
    if not isinstance(arm, ExecutedArm) or not arm.attempt.valid or arm.output_text is None:
        raise ValueError("projection requires a valid completed arm")
    if not isinstance(task, LiveTask) or arm.attempt.task_id != task.task_id:
        raise ValueError("task must match completed arm")
    if not isinstance(task_pack_hash, str) or not task_pack_hash.startswith("sha256:"):
        raise ValueError("task_pack_hash must be a prefixed SHA-256 hash")
    if not isinstance(event_log, FlywheelEventLog):
        raise TypeError("event_log must be a FlywheelEventLog")
    if action_agent_id == verifier_agent_id:
        raise ValueError("verdict producer must be independent from action producer")
    if any(isinstance(value, bool) or not isinstance(value, int) or value <= 0 for value in (action_agent_id, verifier_agent_id)):
        raise ValueError("agent IDs must be positive integers")
    if not hasattr(signing_key, "sign") or not hasattr(signing_key, "verify_key"):
        raise TypeError("signing_key must be an Ed25519 SigningKey")


__all__ = [
    "EpisodeEvidenceBundle",
    "PoiSignal",
    "project_episode",
    "verify_episode_bundle",
]
