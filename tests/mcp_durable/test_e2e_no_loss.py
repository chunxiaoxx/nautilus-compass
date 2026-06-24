"""Task 6 (capstone) · END-TO-END zero-message-loss across a transport drop.

This is the closed-loop PROOF that "MCP 总断" is now *durable*, not merely
auto-recovered. It drives the REAL server (`mcp_server.py` `_tcp_loop`, booted
as a subprocess in dev/no-auth TCP mode) and the REAL bridge client helpers
(`ops/mcp_stdio_to_cloud.py`: `_CloudLink`, `_strip_eid_and_track`,
`_inject_last_event_id`, the high-water tracking) — no reimplementation of the
durability logic, no real SSH tunnel.

What it demonstrates
--------------------
The server emits a burst of N content frames, each tagged with a monotonic
`_eid` 1..N by the real session-scoped EventStore. The socket DROPS mid-burst:
the client read frames 1..k for some k<N, and frames k+1..N were in flight /
unsent on the wire when the link died (but the server retained them in its
session store). The client reconnects with the SAME `sessionId` and
`lastEventId=k` (built via the real bridge `_inject_last_event_id`, seeded from
the real high-water the client tracked). The real server replays exactly
k+1..N (original `_eid`, ascending) then replies `resumed=true`. Each replayed
line is run through the real bridge `_strip_eid_and_track`. We assert the
Claude-Code-facing stream is the complete, contiguous, deduplicated sequence of
all N payloads, in order, with no `_eid` leaked.

Non-triviality (durable vs v1.8-only)
-------------------------------------
A v1.8-style bridge reconnects with an `initialize` that carries NO
`lastEventId` (initialize-replay-only auth, no Last-Event-ID resume). We drive
that SAME drop through that path and assert the in-flight frames k+1..N are
LOST (a gap in the client stream). That contrast proves Task 6 isn't trivially
green: the durable resume layer is precisely what closes the gap; without it
the gap is real. We isolate the two paths purely by what the reconnect
`initialize` carries — `lastEventId=k` (durable) vs absent (v1.8) — against the
identical server, session, and pre-drop history. `_inject_last_event_id` is the
real seam: with `high_eid=k` it injects the marker (durable); with `high_eid=0`
it is a documented no-op (v1.8 shape).

Determinism
-----------
The drop is driven EXPLICITLY (close the client socket at a known frame k), not
by racing a timer. Frames are pulled one reply per request, so "seen up to k"
is exact. No real sleep gates any assertion (the only bounded settle waits on an
OBSERVED socket buffer state via MSG_PEEK, and the real gate is the replayed
content). The server subprocess is terminated and waited on in teardown — no
port/process leak.
"""
from __future__ import annotations

import contextlib
import importlib
import json
import os
import socket
import subprocess
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

# Real bridge client helpers — we exercise the actual client durability code,
# not a reimplementation. A token is required at import time (the bridge exits
# if COMPASS_CLOUD_TOKEN is unset) but is irrelevant in dev/no-auth server mode.
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "test-dummy-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")


# --------------------------------------------------------------------------
# Harness — real server subprocess (shape reused from test_resume_handshake).
# --------------------------------------------------------------------------

def _req(msg_id, method, params=None):
    m = {"jsonrpc": "2.0", "id": msg_id, "method": method}
    if params is not None:
        m["params"] = params
    return m


def _free_port() -> int:
    with contextlib.closing(socket.socket()) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _send(sock: socket.socket, msg: dict) -> None:
    sock.sendall((json.dumps(msg) + "\n").encode("utf-8"))


def _recv_one(sock: socket.socket, timeout: float = 3.0) -> bytes:
    """Read a single raw line-delimited frame (BYTES, without the newline)."""
    sock.settimeout(timeout)
    buf = b""
    while b"\n" not in buf:
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    line, _, _ = buf.partition(b"\n")
    return line


def _recv_n_raw(sock: socket.socket, n: int, timeout: float = 3.0) -> list[bytes]:
    """Read exactly n raw line-delimited frames (handles >1 per recv)."""
    sock.settimeout(timeout)
    frames: list[bytes] = []
    buf = b""
    while len(frames) < n:
        while b"\n" in buf and len(frames) < n:
            line, buf = buf.split(b"\n", 1)
            line = line.strip()
            if line:
                frames.append(line)
        if len(frames) >= n:
            break
        chunk = sock.recv(4096)
        if not chunk:
            break
        buf += chunk
    return frames


@contextlib.contextmanager
def _tcp_server():
    """Dev/no-auth TCP server (token_table=None) on an ephemeral port."""
    port = _free_port()
    cmd = [sys.executable, str(PLUGIN_ROOT / "mcp_server.py"),
           "--transport", "tcp", "--host", "127.0.0.1", "--port", str(port)]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env={**os.environ, "PYTHONUTF8": "1"})
    deadline = time.time() + 5.0
    ready = False
    while time.time() < deadline:
        line = proc.stderr.readline() if proc.stderr else b""
        if b"listening on" in line:
            ready = True
            break
    try:
        assert ready, "TCP server did not announce readiness"
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=2)


def _connect(port: int) -> socket.socket:
    s = socket.socket()
    s.connect(("127.0.0.1", port))
    return s


def _initialize_request(session_id: str) -> dict:
    return _req(1, "initialize", {
        "protocolVersion": "2024-11-05",
        "clientInfo": {"name": "e2e", "version": "0"},
        "sessionId": session_id,
    })


def _drain_until_store_has(sock: socket.socket, n_unread: int,
                           timeout: float = 2.0) -> None:
    """Block until the n_unread in-flight replies are observable in the
    client's recv buffer — proof the server processed (and thus appended to its
    session store) the in-flight requests — WITHOUT consuming them.

    We MSG_PEEK the socket (non-destructive) and gate on seeing >= n_unread
    newline-delimited frames buffered. Because the server processes a
    connection's messages strictly in order, observing the in-flight replies
    buffered guarantees the store holds k+1..N for replay. We never read them,
    so the client genuinely never "saw" them — the drop loses them on the wire.
    This gates on an OBSERVED buffer state, not on elapsed time; the bounded
    timeout is only a safety cap (the real gate is the replay content).
    """
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            sock.settimeout(0.05)
            data = sock.recv(65536, socket.MSG_PEEK)
        except (socket.timeout, OSError):
            continue
        if data.count(b"\n") >= n_unread:
            return
    # Fall through: the replay assertions below are the real gate — if the
    # server hadn't stored the frames the replay would come up short and FAIL.


# --------------------------------------------------------------------------
# 1) POSITIVE — durable path closes the loop: zero loss, zero dup, no _eid leak.
# --------------------------------------------------------------------------

def test_e2e_zero_loss_across_drop_durable_path():
    """REAL server + REAL bridge helpers. Burst of N frames, mid-burst socket
    drop after the client saw up to k, reconnect with lastEventId=k, server
    replays k+1..N. Claude-Code-facing stream == exactly all N payloads,
    contiguous, deduplicated, _eid stripped.

    Client side uses the real bridge `_CloudLink` (high-water tracking),
    `_strip_eid_and_track` (forward + strip + track), and `_inject_last_event_id`
    (build the resume initialize) — not a hand-rolled clone.
    """
    SESSION = "e2e-durable"
    N = 8           # total content frames in the logical burst (initialize=_eid 1)
    K = 4           # client read _eid 1..K, then the socket dropped

    with _tcp_server() as port:
        # Real client-side durability object (high-water tracker lives here).
        link = bridge._CloudLink(opener=lambda: None)

        # The Claude-Code-facing stream we assert on. We capture each frame's
        # logical _eid from the RAW line BEFORE the real forwarder strips it
        # (so we can prove contiguity over the logical sequence), then run the
        # REAL bridge `_strip_eid_and_track` to produce the actual stripped
        # bytes Claude would receive and to advance the real high-water mark.
        delivered: list[dict] = []  # {"eid": int, "stripped": dict}

        def forward_to_claude(raw_line: bytes) -> None:
            logical_eid = json.loads(raw_line.decode("utf-8")).get("_eid")
            out_bytes = bridge._strip_eid_and_track(raw_line, link)
            stripped = json.loads(out_bytes.decode("utf-8"))
            delivered.append({"eid": logical_eid, "stripped": stripped})

        # --- Phase 0: connect, burst, drop mid-stream after k frames read. ---
        s1 = _connect(port)
        s1.sendall((json.dumps(_initialize_request(SESSION)) + "\n").encode())
        forward_to_claude(_recv_one(s1))          # _eid 1 (initialize reply)
        for mid in range(2, K + 1):
            _send(s1, _req(mid, "ping"))
            forward_to_claude(_recv_one(s1))      # _eid 2..K
        assert link.high_eid == K, f"expected high-water {K}, got {link.high_eid}"

        # Drive the remaining K+1..N requests so the server appends their
        # replies to the SESSION store, but DROP the socket before the client
        # reads them — they are the in-flight/unsent-across-the-drop frames.
        for mid in range(K + 1, N + 1):
            _send(s1, _req(mid, "ping"))
        _drain_until_store_has(s1, N - K)         # gate on server having stored them
        s1.close()                                # <-- explicit transport drop.

        # --- Phase 1: reconnect with lastEventId = high-water (the real seam). ---
        base_init = json.dumps(_initialize_request(SESSION))
        resume_init = bridge._inject_last_event_id(base_init, link.high_eid)
        assert json.loads(resume_init)["params"]["lastEventId"] == K

        s2 = _connect(port)
        s2.sendall((resume_init + "\n").encode("utf-8"))
        # Server replays the missed frames RAW (k+1..N) then the init reply
        # (resumed=true): (N-K) replay frames + 1 reply.
        replay_frames = _recv_n_raw(s2, (N - K) + 1)
        s2.close()

        # The last frame is the resume initialize reply. The real bridge swallows
        # it (_recv_one_line on reconnect) — it is NOT forwarded to Claude — so
        # we assert on it but do not add it to the delivered stream.
        init_reply = json.loads(replay_frames[-1].decode("utf-8"))
        assert init_reply.get("id") == 1
        assert init_reply["result"].get("resumed") is True, (
            "server did not signal resumed=true — durable replay didn't engage")
        # Forward the replayed missed frames through the real bridge forwarder.
        for raw in replay_frames[:-1]:
            forward_to_claude(raw)

        # ---------- THE CONTIGUITY ASSERTION (no gap AND no dup) ----------
        # (a) every delivered payload reached Claude with _eid STRIPPED;
        # (b) the recovered logical ids == exactly {1..N}, each once
        #     (sorted == range(1,N+1)  ⇒  contiguous, no gap;
        #      len == len(set) == N    ⇒  no duplicate);
        # (c) delivery order is ascending across the drop seam.
        for d in delivered:
            assert "_eid" not in d["stripped"], (
                f"internal _eid leaked to Claude Code: {d['stripped']}")
        ids = [d["eid"] for d in delivered]
        assert sorted(ids) == list(range(1, N + 1)), (
            f"client stream is not the contiguous dedup'd 1..{N}: {ids}")
        assert len(ids) == len(set(ids)) == N, f"duplicate frame delivered: {ids}"
        assert ids == sorted(ids), f"frames delivered out of order: {ids}"
        # high-water reached N (client now believes it has everything).
        assert link.high_eid == N, f"high-water {link.high_eid} != {N}"


# --------------------------------------------------------------------------
# 2) CONTRAST — v1.8-only path (reconnect WITHOUT lastEventId) LOSES frames.
#    Proves the durable layer is what closes the gap (Task 6 is non-trivial).
# --------------------------------------------------------------------------

def test_e2e_v18_only_reconnect_loses_inflight_frames():
    """Identical drop scenario, but the reconnect initialize carries NO
    lastEventId (v1.8 initialize-replay-only). Isolation: SAME server, session,
    pre-drop history — the ONLY difference is the reconnect init shape, produced
    by the real `_inject_last_event_id` with high_eid=0 (its documented no-op).
    The server does a fresh init and DOES NOT replay k+1..N → the client stream
    has a GAP. This is exactly the loss the durable path eliminates.
    """
    SESSION = "e2e-v18-only"
    N = 8
    K = 4

    with _tcp_server() as port:
        seen_ids: list[int] = []  # logical _eids the client actually READ

        s1 = _connect(port)
        s1.sendall((json.dumps(_initialize_request(SESSION)) + "\n").encode())
        seen_ids.append(json.loads(_recv_one(s1).decode())["_eid"])   # _eid 1
        for mid in range(2, K + 1):
            _send(s1, _req(mid, "ping"))
            seen_ids.append(json.loads(_recv_one(s1).decode())["_eid"])  # 2..K
        assert seen_ids == list(range(1, K + 1))
        for mid in range(K + 1, N + 1):
            _send(s1, _req(mid, "ping"))           # in-flight, never read
        _drain_until_store_has(s1, N - K)
        s1.close()  # explicit drop

        # v1.8 reconnect: NO lastEventId. Built via the SAME real injector with
        # high_eid=0 (nothing-seen shape) so the marker is legitimately absent.
        base_init = json.dumps(_initialize_request(SESSION))
        v18_init = bridge._inject_last_event_id(base_init, 0)  # documented no-op
        assert "lastEventId" not in json.loads(v18_init).get("params", {}), (
            "isolation broken: v1.8 path must not carry lastEventId")

        s2 = _connect(port)
        s2.sendall((v18_init + "\n").encode("utf-8"))
        reply = json.loads(_recv_one(s2).decode("utf-8"))  # immediate init reply
        s2.close()

        # The very first frame back is the init reply (no replay frames preceded
        # it) and it does NOT signal resumed=true.
        assert reply.get("id") == 1, (
            "v1.8 path unexpectedly received a replayed frame before the reply — "
            "isolation broken")
        assert reply["result"].get("resumed") is not True, (
            "v1.8 (no lastEventId) must NOT resume")

        # CONFIRM LOSS: the client only ever surfaced 1..K; k+1..N are GONE.
        # This is the gap the durable path (test above) eliminates.
        assert seen_ids == list(range(1, K + 1)), seen_ids
        missing = [e for e in range(K + 1, N + 1) if e not in seen_ids]
        assert missing == list(range(K + 1, N + 1)), (
            f"expected v1.8 to LOSE frames {list(range(K + 1, N + 1))}, "
            f"but missing={missing}")
