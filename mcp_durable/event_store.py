"""Pure in-memory EventStore for durable MCP replay.

The server appends every outbound frame here. Each frame is tagged with a
strictly-increasing global id (starting at 1) and a timestamp (read only from
``now_fn``, the single point where real time enters the module). History is
bounded two ways:

  · size  — never retain more than ``max_events`` frames
  · ttl   — never retain frames older than ``ttl_seconds``

On reconnect a client sends the last id it observed; ``replay_since`` returns
the frames it missed, or ``None`` when those frames have already been evicted
(the gap is unfillable → caller must full-resync).

This module is self-contained: no sockets, no I/O, never raises on bad input.
It is also thread-safe — a single store is shared across the OS threads of
parallel connections that resolve to the same session key.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Optional


class EventStore:
    """Bounded, monotonically-indexed ring buffer of outbound frames."""

    def __init__(
        self,
        max_events: int,
        ttl_seconds: float,
        now_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        if max_events < 0:
            raise ValueError(
                f"max_events must be >= 0 (0 = retain nothing), got {max_events}"
            )
        self._max_events = max_events
        self._ttl_seconds = ttl_seconds
        # The ONLY place real time is read. Injectable for deterministic tests.
        self._now_fn: Callable[[], float] = now_fn or time.monotonic
        # Each entry: {"id": int, "ts": float, "frame": dict}, ascending id.
        self._events: list[dict] = []
        self._next_id = 1  # first append() returns 1
        # A session-scoped store is shared across OS threads (the same
        # session_key driving parallel connections). The id read-modify-write
        # in append() and the list iteration in replay_since() vs the pop(0)s
        # in _evict() are not atomic across GIL release points, so guard the
        # full public-method bodies with this lock to keep the
        # strictly-ascending-unique-id invariant that resume relies on.
        self._lock = threading.Lock()

    def append(self, frame: dict) -> int:
        """Store ``frame``, return its assigned global id. Thread-safe."""
        with self._lock:
            event_id = self._next_id
            self._next_id += 1
            self._events.append(
                {"id": event_id, "ts": self._now_fn(), "frame": frame}
            )
            self._evict()
            return event_id

    def _evict(self) -> None:
        """Drop oldest entries beyond the size cap or past the ttl window.

        Caller MUST already hold ``self._lock`` (invoked only from within
        ``append``'s locked body) — it does not acquire the lock itself, so it
        never double-acquires / deadlocks.
        """
        # Size bound: keep at most max_events (max_events >= 0 guaranteed).
        while len(self._events) > self._max_events:
            self._events.pop(0)
        # TTL bound: drop anything older than now - ttl_seconds.
        cutoff = self._now_fn() - self._ttl_seconds
        while self._events and self._events[0]["ts"] < cutoff:
            self._events.pop(0)

    @staticmethod
    def _copy_event(event: dict) -> dict:
        """Shallow-copy an event so callers can't mutate the internal store.

        Copies the event dict and its ``frame`` dict; reassigning keys on the
        returned value (incl. ``frame`` contents) leaves ``_events`` untouched.
        """
        frame = event["frame"]
        return {
            "id": event["id"],
            "ts": event["ts"],
            "frame": dict(frame) if isinstance(frame, dict) else frame,
        }

    def replay_since(self, last_id: int) -> Optional[list]:
        """Return retained events with id > ``last_id``.

        · last_id == 0          → all retained events (fresh client).
        · gap below window      → None (events evicted, caller must resync).
        · otherwise             → ascending list of newer events (maybe empty).

        Returned events are copies — mutating them does not affect the store.
        Thread-safe: the whole snapshot is taken under the lock so a concurrent
        ``append``/``_evict`` can't mutate ``_events`` mid-iteration.
        """
        with self._lock:
            if last_id == 0:
                return [self._copy_event(e) for e in self._events]

            if not self._events:
                # Nothing retained. If the client already saw everything we ever
                # had (last_id >= high-water mark), nothing newer exists → []. If
                # it lags behind ids we once held but evicted → unfillable gap.
                highest_seen = self._next_id - 1
                if last_id >= highest_seen:
                    return []
                return None

            oldest_id = self._events[0]["id"]
            # The gap is fillable only if the next id the client needs
            # (last_id + 1) is still retained, i.e. last_id + 1 >= oldest_id.
            if last_id + 1 < oldest_id:
                return None

            return [self._copy_event(e) for e in self._events if e["id"] > last_id]
