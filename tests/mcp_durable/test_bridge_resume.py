"""Task 4 · bridge tracks _eid + requests Last-Event-ID replay on reconnect.

Durable MCP = zero message loss across a cloud-link drop. Tasks 1-3 gave the
SERVER side: it tags every outbound frame with a monotonic `_eid`, keeps a
session-scoped EventStore, and on `initialize` with `params.lastEventId=k`
replays the missed frames (original _eid, ascending) then replies resumed=true.

Task 4 = the CLIENT side: the bridge `ops/mcp_stdio_to_cloud.py` must
  1. track the highest `_eid` it has forwarded from cloud→stdout,
  2. STRIP `_eid` before forwarding to Claude Code (internal durability field),
  3. on reconnect inject `params.lastEventId = <highest seen>` into the
     replayed cached initialize (only when > 0; never into the first init),
  4. preserve the v1.8 invariant: any failure → forward as-is / degrade to
     local-only, never crash, never block stdin, never drop a frame.

Approach (documented per Task 4 spec): helpers + one integration test.
  - `test_strip_eid_*` / `test_high_water_*` unit-test the pure cloud-line
    handler (`_strip_eid_and_track`) directly.
  - `test_inject_last_event_id_*` unit-test the cached-initialize injector.
  - `test_reconnect_requests_replay_over_fake_socket` drives a real
    `_CloudLink` over an in-process fake socket pair: emit _eid 1..N, drop,
    reconnect, assert the replayed initialize carried lastEventId == N and the
    stdout-facing stream is contiguous, _eid-free, no gap, no dup.
We went helpers + 1 integration because the full bridge wires three daemon
threads (stdin pump / cloud→out pump / heartbeat) around real sys.stdin and a
shared stdout lock; driving only the cloud→out reconnect seam against a fake
socket is hermetic and pins exactly the Task-4 behaviour without that thread
soup. The helpers are the load-bearing pure logic; the integration test proves
they compose over the real reconnect handshake.
"""
from __future__ import annotations

import importlib
import json
import os
import sys
import threading
import time
from pathlib import Path

PLUGIN = Path(__file__).resolve().parent.parent.parent
if str(PLUGIN) not in sys.path:
    sys.path.insert(0, str(PLUGIN))
os.environ.setdefault("COMPASS_CLOUD_TOKEN", "test-dummy-token")
bridge = importlib.import_module("ops.mcp_stdio_to_cloud")


# --------------------------------------------------------------------------
# Helper (a): strip _eid + track high-water from a single cloud line.
# --------------------------------------------------------------------------

def test_strip_eid_removes_internal_field_and_forwards():
    link = bridge._CloudLink(opener=lambda: None)
    line = json.dumps({"jsonrpc": "2.0", "id": 5, "result": {"ok": 1}, "_eid": 3})
    out = bridge._strip_eid_and_track(line, link)
    decoded = json.loads(out.decode("utf-8"))
    assert "_eid" not in decoded
    assert decoded["id"] == 5
    assert decoded["result"] == {"ok": 1}


def test_strip_eid_advances_high_water():
    link = bridge._CloudLink(opener=lambda: None)
    assert link.high_eid == 0
    bridge._strip_eid_and_track(json.dumps({"id": 1, "_eid": 1}), link)
    assert link.high_eid == 1
    bridge._strip_eid_and_track(json.dumps({"id": 2, "_eid": 5}), link)
    assert link.high_eid == 5
    # never goes backwards (out-of-order / stale frame)
    bridge._strip_eid_and_track(json.dumps({"id": 3, "_eid": 2}), link)
    assert link.high_eid == 5


def test_strip_eid_forwards_line_without_eid_unchanged():
    link = bridge._CloudLink(opener=lambda: None)
    line = json.dumps({"jsonrpc": "2.0", "id": 9, "result": {}})
    out = bridge._strip_eid_and_track(line, link)
    assert json.loads(out.decode("utf-8")) == json.loads(line)
    assert link.high_eid == 0  # nothing to track


def test_strip_eid_forwards_non_json_unchanged_and_never_crashes():
    link = bridge._CloudLink(opener=lambda: None)
    out = bridge._strip_eid_and_track("not-json-at-all", link)
    assert out == b"not-json-at-all"
    assert link.high_eid == 0


def test_strip_eid_handles_bytes_input():
    link = bridge._CloudLink(opener=lambda: None)
    raw = json.dumps({"id": 1, "_eid": 7}).encode("utf-8")
    out = bridge._strip_eid_and_track(raw, link)
    assert b"_eid" not in out
    assert link.high_eid == 7


# --------------------------------------------------------------------------
# Helper (b): inject lastEventId into a cached initialize line.
# --------------------------------------------------------------------------

def test_inject_last_event_id_sets_param():
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {"protocolVersion": "2024-11-05"}})
    out = bridge._inject_last_event_id(init, 4)
    msg = json.loads(out)
    assert msg["params"]["lastEventId"] == 4
    assert msg["params"]["protocolVersion"] == "2024-11-05"


def test_inject_last_event_id_creates_params_if_missing():
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize"})
    out = bridge._inject_last_event_id(init, 2)
    assert json.loads(out)["params"]["lastEventId"] == 2


def test_inject_last_event_id_noop_on_non_json():
    assert bridge._inject_last_event_id("garbage", 4) == "garbage"


def test_inject_last_event_id_zero_is_noop():
    """Highest==0 means nothing seen yet → don't request a replay."""
    init = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                       "params": {}})
    out = bridge._inject_last_event_id(init, 0)
    assert "lastEventId" not in json.loads(out).get("params", {})


# --------------------------------------------------------------------------
# Integration: real _CloudLink over an in-process fake cloud socket.
# Emit _eid 1..N, drop, reconnect, assert replay requested + contiguous stdout.
# --------------------------------------------------------------------------

class _FakeCloud:
    """In-process fake cloud socket. Phase 1: accept first init, emit _eid 1..N,
    then drop (recv→b''). Phase 2 (reconnect): accept the replayed init, record
    its lastEventId, emit _eid N+1..M, then idle (block until closed)."""

    def __init__(self, n_before: int, n_after: int) -> None:
        self.n_before = n_before
        self.n_after = n_after
        self.phase = 0
        self.received_inits: list[dict] = []
        self._outbox: list[bytes] = []
        self._cv = threading.Condition()
        self.closed = False
        self.connect_count = 0
        self._load_phase()

    def _frame(self, eid: int) -> bytes:
        return (json.dumps({"jsonrpc": "2.0", "method": "notifications/message",
                            "params": {"n": eid}, "_eid": eid}) + "\n").encode()

    def _load_phase(self) -> None:
        if self.phase == 0:
            self._outbox = [self._frame(e) for e in range(1, self.n_before + 1)]
        else:
            start = self.n_before + 1
            end = self.n_before + self.n_after
            self._outbox = [self._frame(e) for e in range(start, end + 1)]

    # The opener hands back `self` as the "socket".
    def __call__(self):
        self.connect_count += 1
        return self

    def sendall(self, data: bytes) -> None:
        # The bridge replays the cached initialize on reconnect.
        try:
            msg = json.loads(data.decode("utf-8").strip())
        except Exception:
            return
        if isinstance(msg, dict) and msg.get("method") == "initialize":
            self.received_inits.append(msg)

    def recv(self, n: int) -> bytes:
        with self._cv:
            if self._outbox:
                return self._outbox.pop(0)
            if self.phase == 0:
                # Drop: signal EOF so the pump reconnects.
                self.phase = 1
                self._load_phase()
                return b""
            # Phase 1 exhausted: idle until closed.
            while not self.closed and not self._outbox:
                self._cv.wait(timeout=0.1)
                if self._outbox:
                    return self._outbox.pop(0)
            return b""

    def settimeout(self, *_a, **_k) -> None:
        pass

    def close(self) -> None:
        with self._cv:
            self.closed = True
            self._cv.notify_all()


def _recv_one_line_stub(sock, timeout: float = 10.0):
    """The real _recv_one_line swallows the reconnect init reply. Our fake
    doesn't emit a reply for the replayed init, so return immediately."""
    return b""


def test_reconnect_requests_replay_over_fake_socket(monkeypatch):
    fake = _FakeCloud(n_before=3, n_after=2)
    link = bridge._CloudLink(opener=fake)
    # Cache an initialize so reconnect has something to replay.
    init_line = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize",
                            "params": {"protocolVersion": "2024-11-05"}})
    link.note_outgoing(init_line)
    link.connect(replay=False)  # phase-0 socket installed

    # Capture what the bridge writes to Claude-Code-facing stdout.
    written: list[bytes] = []
    monkeypatch.setattr(bridge, "_write_stdout", lambda payload: written.append(payload))
    # Don't block on the duplicate-init-reply swallow (fake emits none).
    monkeypatch.setattr(bridge, "_recv_one_line", _recv_one_line_stub)

    pump = threading.Thread(target=bridge._pump_cloud_to_out, args=(link,), daemon=True)
    pump.start()

    # Wait until all before+after frames have been forwarded.
    deadline = time.time() + 5.0
    want = fake.n_before + fake.n_after
    while time.time() < deadline:
        if len(written) >= want and len(fake.received_inits) >= 1:
            break
        time.sleep(0.02)

    link.close()
    pump.join(timeout=2.0)

    # 1) The FIRST reconnect's replayed initialize carried lastEventId ==
    #    n_before (the high-water captured before the drop). Auth replayed too.
    assert fake.received_inits, "bridge never replayed initialize on reconnect"
    replay_init = fake.received_inits[0]
    assert replay_init.get("params", {}).get("lastEventId") == fake.n_before, (
        f"first replay init lastEventId="
        f"{replay_init.get('params', {}).get('lastEventId')} != {fake.n_before}")
    assert replay_init.get("params", {}).get("authToken"), "auth not replayed"

    # 2) Stdout stream is contiguous, _eid-free, no gap / no dup across the drop.
    eids_seen = []
    for payload in written:
        msg = json.loads(payload.decode("utf-8"))
        assert "_eid" not in msg, "internal _eid leaked to Claude Code"
        eids_seen.append(msg["params"]["n"])
    assert eids_seen == list(range(1, want + 1)), (
        f"non-contiguous stdout stream: {eids_seen}")
    # high-water advanced all the way.
    assert link.high_eid == want
