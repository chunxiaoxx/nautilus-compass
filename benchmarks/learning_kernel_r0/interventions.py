"""Pure, hash-bound memory interventions for Learning Kernel R0."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import Any

from benchmarks.poi_gate2.canonical import hash_json
from gep.experience_packet import ExperiencePacket, to_frontmatter
from gep.verdict_packet import VerdictPacket

from .schema import INTERVENTIONS, MemoryView, memory_view_from_mapping


def build_memory_views(
    packets: tuple[ExperiencePacket, ...],
    *,
    intervention: str,
    query_class: str,
    now_iso: str,
    packet_hashes: Mapping[str, str],
    source_query_classes: Mapping[str, str],
    semantic_scores: Mapping[str, float],
    independent_verdicts: Mapping[str, VerdictPacket | None],
) -> tuple[MemoryView, ...]:
    """Return deterministic evaluation views without mutating source packets."""

    if intervention not in INTERVENTIONS:
        raise ValueError("intervention is unsupported")
    episode_ids = _episode_ids(packets)
    _require_exact_keys("packet_hashes", packet_hashes, episode_ids)
    _require_exact_keys("source_query_classes", source_query_classes, episode_ids)
    _require_exact_keys("semantic_scores", semantic_scores, episode_ids)
    _require_exact_keys("independent_verdicts", independent_verdicts, episode_ids)
    _validate_query_class(query_class)
    _validate_now(now_iso)
    _validate_packet_hashes(packets, packet_hashes)
    _validate_verdicts(packet_hashes, independent_verdicts)

    if intervention == "no_memory":
        return ()

    query_classes = _intervention_query_classes(
        episode_ids,
        source_query_classes,
        intervention,
    )
    representation = "raw" if intervention == "raw" else "distilled"
    views = [
        _build_view(
            packet,
            packet_hash=packet_hashes[_required_episode_id(packet)],
            query_class=query_classes[_required_episode_id(packet)],
            semantic_score=semantic_scores[_required_episode_id(packet)],
            verdict=independent_verdicts[_required_episode_id(packet)],
            representation=representation,
            now_iso=now_iso,
            stale=intervention == "stale",
        )
        for packet in packets
    ]
    if intervention == "contradictory":
        views.extend(_contradictory_view(view) for view in tuple(views))
    return tuple(sorted(views, key=lambda view: view.view_id))


def _episode_ids(packets: tuple[ExperiencePacket, ...]) -> tuple[str, ...]:
    if not isinstance(packets, tuple):
        raise TypeError("packets must be a tuple")
    if not packets:
        raise ValueError("packets must not be empty")
    episode_ids = tuple(_required_episode_id(packet) for packet in packets)
    if len(set(episode_ids)) != len(episode_ids):
        raise ValueError("packet episode_id values must be unique")
    return episode_ids


def _required_episode_id(packet: ExperiencePacket) -> str:
    if not isinstance(packet, ExperiencePacket):
        raise TypeError("packets must contain ExperiencePacket values")
    if not packet.episode_id or not packet.episode_id.strip():
        raise ValueError("packet episode_id must not be blank")
    return packet.episode_id


def _require_exact_keys(
    name: str,
    values: Mapping[str, Any],
    episode_ids: tuple[str, ...],
) -> None:
    if not isinstance(values, Mapping):
        raise TypeError(f"{name} must be a mapping")
    expected = set(episode_ids)
    actual = set(values)
    if actual != expected:
        raise ValueError(f"{name} must contain exactly the packet episode_id keys")


def _validate_packet_hashes(
    packets: tuple[ExperiencePacket, ...],
    packet_hashes: Mapping[str, str],
) -> None:
    for packet in packets:
        episode_id = _required_episode_id(packet)
        expected = hash_json(to_frontmatter(packet))
        if packet_hashes[episode_id] != expected:
            raise ValueError(f"packet hash mismatch for {episode_id}")


def _validate_verdicts(
    packet_hashes: Mapping[str, str],
    verdicts: Mapping[str, VerdictPacket | None],
) -> None:
    for episode_id, verdict in verdicts.items():
        if verdict is None:
            continue
        if not isinstance(verdict, VerdictPacket):
            raise TypeError("independent_verdicts values must be VerdictPacket or None")
        if verdict.episode_id != episode_id:
            raise ValueError(f"verdict episode mismatch for {episode_id}")
        if verdict.episode_event_hash != packet_hashes[episode_id]:
            raise ValueError(f"verdict hash mismatch for {episode_id}")


def _intervention_query_classes(
    episode_ids: tuple[str, ...],
    source_query_classes: Mapping[str, str],
    intervention: str,
) -> dict[str, str]:
    for value in source_query_classes.values():
        _validate_query_class(value)
    if intervention != "shuffled" or len(episode_ids) < 2:
        return dict(source_query_classes)
    ordered = sorted(episode_ids)
    rotated = ordered[1:] + ordered[:1]
    return {
        episode_id: source_query_classes[source_id]
        for episode_id, source_id in zip(ordered, rotated, strict=True)
    }


def _build_view(
    packet: ExperiencePacket,
    *,
    packet_hash: str,
    query_class: str,
    semantic_score: float,
    verdict: VerdictPacket | None,
    representation: str,
    now_iso: str,
    stale: bool,
) -> MemoryView:
    episode_id = _required_episode_id(packet)
    rendered_text = _render_raw(packet) if representation == "raw" else _render_distilled(packet)
    raw = {
        "view_id": "lkr0_view_pending",
        "source_packet_hash": packet_hash,
        "route_key": packet.route_key or "unrouted",
        "query_class": query_class,
        "action_kind": packet.action_kind or "unspecified",
        "representation": representation,
        "rendered_text": rendered_text,
        "semantic_score": semantic_score,
        "verification_state": "blocked" if verdict is None else "independent_verified",
        "verdict": None if verdict is None else verdict.outcome,
        "lifecycle_state": "cooling" if stale else "active",
        "expires_at": now_iso if stale else None,
    }
    digest = hash_json({key: value for key, value in raw.items() if key != "view_id"})
    raw["view_id"] = f"lkr0_view_{episode_id}_{digest.removeprefix('sha256:')[:12]}"
    return memory_view_from_mapping(raw)


def _render_raw(packet: ExperiencePacket) -> str:
    parts = (
        f"task={packet.task or 'unspecified'}",
        f"action={packet.action_kind or 'unspecified'}",
        f"tools={','.join(packet.tool_chain or ()) or 'none'}",
        f"outcome={packet.outcome or 'unknown'}",
        f"failure={packet.failure_mode or 'none'}",
        f"lesson={packet.policy_hint or 'none'}",
    )
    return "; ".join(parts)


def _render_distilled(packet: ExperiencePacket) -> str:
    return packet.policy_hint or packet.task or "No distilled lesson supplied."


def _contradictory_view(view: MemoryView) -> MemoryView:
    rendered_text = f"DO_NOT_USE: {view.rendered_text}"
    digest = hash_json(
        {
            "source_view_id": view.view_id,
            "rendered_text": rendered_text,
            "intervention": "contradictory",
        }
    )
    return replace(
        view,
        view_id=f"{view.view_id.rsplit('_', 1)[0]}_{digest.removeprefix('sha256:')[:12]}",
        rendered_text=rendered_text,
    )


def _validate_query_class(value: Any) -> None:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ValueError("query_class must be a normalized non-blank string")


def _validate_now(value: Any) -> None:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError("now_iso must be an explicit UTC timestamp ending in Z")


__all__ = ["build_memory_views"]
