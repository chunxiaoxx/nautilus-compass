"""Pure derived state for already validated and admitted flywheel events.

Callers must supply ``FlywheelEvent`` facts that journal admission has already
validated and admitted. Verifier authority and verdict cardinality remain
journal-admission responsibilities; this module only derives state from facts.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Literal

from gep.flywheel_event import (
    EVENT_KIND_EPISODE,
    EVENT_KIND_VERDICT,
    FlywheelEvent,
)
from gep.verdict_packet import VerdictOutcome


@dataclass(frozen=True)
class EpisodeState:
    """Derived state for one admitted episode event."""

    episode_id: str
    state: Literal["awaiting_verdict", "verified", "verdict_conflict"]
    source_event_id: str
    event_hash: str
    verified_outcome: VerdictOutcome | None = None
    verdict_event_hashes: tuple[str, ...] = ()


def reduce_episode_states(events: Iterable[FlywheelEvent]) -> dict[str, EpisodeState]:
    """Purely derive deterministic episode states from admitted event facts."""

    materialized_events = tuple(events)
    episodes_by_id: dict[str, FlywheelEvent] = {}
    events_by_source_id: dict[str, FlywheelEvent] = {}
    for event in materialized_events:
        if event.source_event_id in events_by_source_id:
            raise ValueError(f"duplicate source_event_id: {event.source_event_id}")
        events_by_source_id[event.source_event_id] = event
        if event.event_kind == EVENT_KIND_EPISODE:
            if event.episode_id in episodes_by_id:
                raise ValueError(f"duplicate episode_id: {event.episode_id}")
            episodes_by_id[event.episode_id] = event
        elif event.event_kind != EVENT_KIND_VERDICT:
            raise ValueError(f"unsupported event_kind: {event.event_kind}")

    verdicts_by_episode_id = {episode_id: [] for episode_id in episodes_by_id}
    for event in materialized_events:
        if event.event_kind == EVENT_KIND_EPISODE:
            continue
        parent = _verdict_parent_episode(event, events_by_source_id)
        verdicts_by_episode_id[parent.episode_id].append(event)

    return {
        episode_id: _derive_episode_state(
            episodes_by_id[episode_id],
            verdicts_by_episode_id[episode_id],
        )
        for episode_id in sorted(episodes_by_id)
    }


def _verdict_parent_episode(
    verdict: FlywheelEvent,
    events_by_source_id: Mapping[str, FlywheelEvent],
) -> FlywheelEvent:
    parent = events_by_source_id.get(verdict.parent_event_id)
    if parent is None:
        raise ValueError(f"orphan verdict: {verdict.source_event_id}")
    if parent.event_kind != EVENT_KIND_EPISODE:
        raise ValueError(f"verdict parent is not an episode: {verdict.source_event_id}")
    if verdict.episode_id != parent.episode_id:
        raise ValueError(f"verdict episode_id does not match parent: {verdict.source_event_id}")
    if verdict.payload["episode_event_hash"] != parent.event_hash:
        raise ValueError(
            f"verdict episode_event_hash does not match parent: {verdict.source_event_id}"
        )
    return parent


def _derive_episode_state(
    episode: FlywheelEvent,
    verdicts: Iterable[FlywheelEvent],
) -> EpisodeState:
    conclusive_outcomes = {
        verdict.payload["outcome"]
        for verdict in verdicts
        if verdict.payload["outcome"] != "inconclusive"
    }
    verified_outcome: VerdictOutcome | None = None
    if not conclusive_outcomes:
        state: Literal["awaiting_verdict", "verified", "verdict_conflict"] = (
            "awaiting_verdict"
        )
    elif len(conclusive_outcomes) == 1:
        state = "verified"
        verified_outcome = next(iter(conclusive_outcomes))
    else:
        state = "verdict_conflict"
    return EpisodeState(
        episode_id=episode.episode_id,
        state=state,
        source_event_id=episode.source_event_id,
        event_hash=episode.event_hash,
        verified_outcome=verified_outcome,
        verdict_event_hashes=tuple(sorted(verdict.event_hash for verdict in verdicts)),
    )
