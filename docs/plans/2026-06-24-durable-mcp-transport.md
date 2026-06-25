# Durable MCP Transport Implementation Plan (EventStore + Last-Event-ID + watchdog)

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Run in worktree `nautilus-compass-durable-mcp` (branch `feat/durable-mcp`, off `feat/v2.3.0-release`). This closes the MCP loop that v1.8 (auto-reconnect band-aid) only partially addressed — must land BEFORE v2.3.0 release per user decision 2026-06-24.

**Goal:** Make MCP survive a transport drop with **zero message loss** — the protocol-official durable solution (EventStore + Last-Event-ID replay) plus a watchdog supervisor, so "MCP 总断" is closed-loop, not just auto-recovered.

**Architecture:** Today's stack = Claude Code stdio → `ops/mcp_stdio_to_cloud.py` bridge → SSH tunnel → cloud daemon socket → `mcp_server.py` (`_tcp_loop`, already TLS-capable). v1.8 auto-reconnect replays ONLY the `initialize` handshake — any notification/response in flight during a drop is **lost**. This plan adds: (1) server-side EventStore tagging every outbound message with a monotonic global id + bounded history window; (2) Last-Event-ID handshake so a reconnecting client replays exactly the messages it missed; (3) a watchdog/heartbeat layer (checkpoint≠durable — a dead daemon needs external detection).

**Tech Stack:** Python · stdlib socket/threading · pytest · existing `mcp_server.py` transport loops + `ops/mcp_stdio_to_cloud.py` CloudLink (v1.8 reconnect pump).

**Grounding (verified 2026-06-24):**
- `mcp_server.py:2185 _stdio_loop` (Claude Code), `:2227 _tcp_loop` (cloud · per-connection session state · `_build_server_ssl_context` TLS/mTLS already present).
- `ops/mcp_stdio_to_cloud.py` CloudLink (`:146`) = v1.8 auto-reconnect + initialize replay; `:513 _cloud_to_out_pump` reconnect w/ exp backoff cap 30s. Caches `initialize` only.
- grep confirmed **zero** EventStore / Last-Event-ID / SSE / StreamableHTTP in serving layer → durable layer is genuinely unbuilt.

---

## Task 1: EventStore (pure · server-side)

**Files:**
- Create: `mcp_durable/event_store.py`
- Test: `tests/mcp_durable/test_event_store.py`

**Step 1 — failing test:**
```python
from mcp_durable.event_store import EventStore

def test_append_assigns_monotonic_ids():
    es = EventStore(max_events=100, ttl_seconds=300)
    a = es.append({"method": "notifications/message", "params": {"x": 1}})
    b = es.append({"method": "notifications/message", "params": {"x": 2}})
    assert b > a == 1  # ids start at 1, strictly increasing

def test_replay_since_returns_only_newer():
    es = EventStore(max_events=100, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    got = es.replay_since(2)            # client saw up to id=2
    assert [e["id"] for e in got] == [3, 4, 5]

def test_replay_since_zero_returns_all():
    es = EventStore(max_events=100, ttl_seconds=300)
    es.append({"i": 0})
    assert len(es.replay_since(0)) == 1

def test_bounded_by_max_events_drops_oldest():
    es = EventStore(max_events=3, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    ids = [e["id"] for e in es.replay_since(0)]
    assert ids == [3, 4, 5]            # oldest two evicted

def test_replay_below_window_floor_signals_gap(now=None):
    # client's last id fell out of the retained window → caller must full-resync
    es = EventStore(max_events=2, ttl_seconds=300)
    for i in range(5):
        es.append({"i": i})
    assert es.replay_since(1) is None   # None = "too old · resync"
```
Run: `pytest tests/mcp_durable/test_event_store.py -v` → FAIL (module missing).

**Step 2 — minimal impl:** ring buffer of `{"id", "ts", "frame"}`, monotonic counter, `append(frame)→id`, `replay_since(last_id)→list|None` (None when `last_id < oldest_retained_id-1` and last_id>0). TTL eviction on append using an injected `now` (no `Date.now()` in tests). Never raises.

**Step 3 — pass.** **Step 4 — commit** `feat(mcp): EventStore ring buffer for durable replay`.

---

## Task 2: Wire EventStore into the server outbound path

**Files:**
- Modify: `mcp_server.py` (`_tcp_loop._serve` outbound writes + `handle_message` notification emit)
- Test: `tests/mcp_durable/test_server_tags_events.py`

**Approach:** Each connection owns an `EventStore`. Every outbound frame (response + notification) goes through a `send(frame)` helper that calls `es.append(frame)`, stamps `frame["_eid"]=id`, then writes. Replays bypass re-append. Keep stdio loop unchanged (single-process, no drop surface).

**TDD:** spin a `_tcp_loop` on an ephemeral port (reuse pattern in `tests/test_mcp_*`), connect, send `initialize` + a tool call, assert every server frame carries a strictly increasing `_eid`. Commit.

---

## Task 3: Last-Event-ID resume handshake (server)

**Files:**
- Modify: `mcp_server.py` (`_serve` initialize handling)
- Test: `tests/mcp_durable/test_resume_handshake.py`

**Behaviour:** `initialize` (or a reconnect) MAY carry `params.lastEventId`. On present:
- `replay = es.replay_since(lastEventId)`; if `None` → reply initialize with `result.resumed=false` (client must full-resync) ; else write each replayed frame then `resumed=true`.
- Absent → fresh session (today's behaviour · `resumed` omitted).

**TDD:** connect, capture frames + last `_eid`, drop, reconnect with `lastEventId=<that>`, assert the missed frames replay in order and `resumed=true`; reconnect with a stale id → `resumed=false` no crash. Commit.

---

## Task 4: Bridge integration (client replay)

**Files:**
- Modify: `ops/mcp_stdio_to_cloud.py` (CloudLink `:146` · `_cloud_to_out_pump` `:513`)
- Test: `tests/mcp_durable/test_bridge_resume.py`

**Behaviour:** CloudLink records the highest `_eid` seen from cloud→out. On reconnect, after replaying cached `initialize`, it sends `params.lastEventId=<highest>` so the server replays the gap. Strip `_eid` before forwarding to Claude Code stdout (internal field). Preserve v1.8 invariant: any failure → degrade to local-only, never crash, never block stdin.

**TDD:** fake cloud socket that drops after N frames; assert bridge reconnects, requests `lastEventId`, and Claude-Code-facing stdout sees a contiguous no-gap stream. Commit.

---

## Task 5: Watchdog / heartbeat (supervisor)

**Files:**
- Create: `mcp_durable/watchdog.py` + `ops/compass-mcp-watchdog.service`/`.timer` (template from `compass-mcp-tcp.service`)
- Test: `tests/mcp_durable/test_watchdog.py`

**Behaviour:** periodic `ping`→`pong` on the link (or TCP health probe of the daemon port); on K consecutive misses → restart the daemon unit (systemd) and log. Key insight (research §A4): checkpoint≠durable — a dead daemon needs external detection. Pure decision fn `should_restart(miss_count, threshold)` is the unit-tested core; the systemd wiring is ops.

**TDD:** `should_restart` truth table + a fake-clock heartbeat loop that flips to restart after K misses. Commit. (Deploy the timer on box = separate gated step, like tier_promotion timer.)

---

## Task 6: E2E no-message-loss (the closed-loop proof)

**Files:**
- Test: `tests/mcp_durable/test_e2e_no_loss.py`

**Behaviour:** end-to-end — server (EventStore) + bridge (resume), inject a mid-stream socket drop while the server is emitting a burst of notifications, assert the Claude-Code-facing output is a complete contiguous sequence (0 lost, 0 duplicated). **This is the verification that "MCP 总断" is now durable, not just auto-recovered** — the thing v1.8 alone cannot pass.

**Acceptance:** Task 6 green = MCP durable loop closed. Then: bump CHANGELOG v2.3.0 with the durable-MCP entry (+ v1.8), deploy watchdog timer on box (gated), `git push origin v2.3.0` (PyPI · gated · user go).

---

## Notes / discipline
- **measurement-first:** Task 6 is the real verification — don't claim "durable" until it passes (verification-before-completion). v1.8 alone fails Task 6 by design.
- **never-breaks-recall posture:** bridge changes keep v1.8's degrade-to-local-only invariant — durable resume is best-effort on top, never a new crash surface.
- **scope guard:** layers 3 (staggered health-check auto-evict) + 5 (agentgateway multiplexer) from research §A are OUT of this plan (heavier · defer) — this plan = layers 2 (EventStore/Last-Event-ID) + 4 (watchdog) = the durable core.
- Relates: memory `reference_architecture_fusion_research_20260623` §A · `gotcha_compass_mcp_bridge_no_reconnect_fixed_v18` (v1.8 root cause).
