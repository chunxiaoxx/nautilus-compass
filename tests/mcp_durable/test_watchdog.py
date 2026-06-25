import socket

import pytest

from mcp_durable.watchdog import (
    HeartbeatMonitor,
    should_restart,
    tcp_probe,
    systemd_restart_cmd,
    _load_miss,
    _store_miss,
)


# ---------------------------------------------------------------------------
# should_restart — pure truth table
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "miss_count,threshold,expected",
    [
        (0, 3, False),
        (2, 3, False),
        (3, 3, True),
        (4, 3, True),
        (1, 1, True),
    ],
)
def test_should_restart_truth_table(miss_count, threshold, expected):
    assert should_restart(miss_count, threshold) is expected


def test_should_restart_guards_threshold_below_one():
    # threshold < 1 is nonsensical; never restart (avoid restart storms).
    assert should_restart(0, 0) is False
    assert should_restart(5, 0) is False
    assert should_restart(5, -1) is False


# ---------------------------------------------------------------------------
# HeartbeatMonitor.tick — fully injected, deterministic
# ---------------------------------------------------------------------------

def _make_probe(sequence):
    seq = list(sequence)
    calls = {"n": 0}

    def probe_fn():
        i = calls["n"]
        calls["n"] += 1
        if i < len(seq):
            return seq[i]
        return seq[-1]  # repeat last forever

    return probe_fn


def test_restart_fires_once_after_k_consecutive_misses():
    restarts = {"n": 0}
    # healthy, then 3 misses (K=3) -> restart on the 3rd miss, then reset.
    probe = _make_probe([True, False, False, False])
    mon = HeartbeatMonitor(
        probe_fn=probe,
        restart_fn=lambda: restarts.__setitem__("n", restarts["n"] + 1),
        threshold=3,
    )

    mon.tick()  # healthy -> miss=0
    assert restarts["n"] == 0
    mon.tick()  # miss 1
    assert restarts["n"] == 0
    mon.tick()  # miss 2
    assert restarts["n"] == 0
    mon.tick()  # miss 3 -> restart fires once
    assert restarts["n"] == 1
    assert mon.miss_count == 0  # counter reset after restart


def test_no_restart_storm_after_reset():
    restarts = {"n": 0}
    # 3 misses (restart), then keep failing — must NOT restart every tick.
    probe = _make_probe([False, False, False, False, False])
    mon = HeartbeatMonitor(
        probe_fn=probe,
        restart_fn=lambda: restarts.__setitem__("n", restarts["n"] + 1),
        threshold=3,
    )
    for _ in range(5):
        mon.tick()
    # ticks 1-3 -> restart; 4,5 only count toward the next window -> still 1.
    assert restarts["n"] == 1
    assert mon.miss_count == 2


def test_healthy_probe_resets_miss_counter():
    restarts = {"n": 0}
    probe = _make_probe([False, False, True, False])
    mon = HeartbeatMonitor(
        probe_fn=probe,
        restart_fn=lambda: restarts.__setitem__("n", restarts["n"] + 1),
        threshold=3,
    )
    mon.tick()  # miss 1
    mon.tick()  # miss 2
    assert mon.miss_count == 2
    mon.tick()  # healthy -> reset
    assert mon.miss_count == 0
    mon.tick()  # miss 1 again
    assert restarts["n"] == 0  # never reached threshold


def test_healthy_throughout_never_restarts():
    restarts = {"n": 0}
    probe = _make_probe([True])
    mon = HeartbeatMonitor(
        probe_fn=probe,
        restart_fn=lambda: restarts.__setitem__("n", restarts["n"] + 1),
        threshold=3,
    )
    for _ in range(10):
        mon.tick()
    assert restarts["n"] == 0
    assert mon.miss_count == 0


def test_probe_exception_counts_as_miss_never_raises():
    restarts = {"n": 0}

    def exploding_probe():
        raise OSError("connection refused")

    mon = HeartbeatMonitor(
        probe_fn=exploding_probe,
        restart_fn=lambda: restarts.__setitem__("n", restarts["n"] + 1),
        threshold=3,
    )
    # Must not propagate the exception out of tick().
    mon.tick()
    mon.tick()
    mon.tick()
    assert restarts["n"] == 1
    assert mon.miss_count == 0


# ---------------------------------------------------------------------------
# tcp_probe — thin real adapter (hermetic: bind a localhost socket)
# ---------------------------------------------------------------------------

def test_tcp_probe_returns_true_for_live_listener():
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    host, port = srv.getsockname()
    try:
        assert tcp_probe(host, port, timeout=2.0) is True
    finally:
        srv.close()


def test_tcp_probe_returns_false_for_closed_port():
    # Bind to grab a free port, then close it so nothing is listening.
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    host, port = s.getsockname()
    s.close()
    assert tcp_probe(host, port, timeout=0.5) is False


# ---------------------------------------------------------------------------
# systemd_restart_cmd — constructs the right command (not executed)
# ---------------------------------------------------------------------------

def test_systemd_restart_cmd_system_scope():
    assert systemd_restart_cmd("compass-mcp-tcp") == [
        "systemctl",
        "restart",
        "compass-mcp-tcp",
    ]


def test_systemd_restart_cmd_user_scope():
    assert systemd_restart_cmd("compass-mcp-tcp", user=True) == [
        "systemctl",
        "--user",
        "restart",
        "compass-mcp-tcp",
    ]


# ---------------------------------------------------------------------------
# Cross-fire state I/O (_load_miss / _store_miss) — the correctness-sensitive
# part of the systemd one-fire wiring. Inject a tmp_path state file.
# ---------------------------------------------------------------------------

def test_store_load_round_trip_accumulates(tmp_path):
    p = tmp_path / "miss.state"
    _store_miss(p, 1)
    assert _load_miss(p) == 1
    _store_miss(p, 2)
    assert _load_miss(p) == 2


def test_load_miss_corrupt_content_returns_zero(tmp_path):
    p = tmp_path / "miss.state"
    p.write_text("garbage")
    assert _load_miss(p) == 0


def test_load_miss_missing_file_returns_zero(tmp_path):
    assert _load_miss(tmp_path / "does-not-exist.state") == 0


def test_store_miss_healthy_persists_zero(tmp_path):
    # A healthy fire writes 0 so the next fire starts clean (no stale-counter
    # spurious restart).
    p = tmp_path / "miss.state"
    _store_miss(p, 3)
    assert _load_miss(p) == 3
    _store_miss(p, 0)
    assert _load_miss(p) == 0


def test_store_miss_creates_parent_dirs(tmp_path):
    p = tmp_path / "nested" / "dir" / "miss.state"
    _store_miss(p, 2)
    assert _load_miss(p) == 2


def test_store_miss_write_failure_never_raises(tmp_path):
    # Point at a path whose "parent" is a regular file -> mkdir/write fails.
    blocker = tmp_path / "blocker"
    blocker.write_text("i am a file")
    bad = blocker / "miss.state"
    # Must not raise even though the write is impossible.
    _store_miss(bad, 1)


def test_load_miss_never_raises_on_permission_error(monkeypatch, tmp_path):
    p = tmp_path / "miss.state"
    p.write_text("2")

    def boom(*a, **k):
        raise PermissionError("denied")

    monkeypatch.setattr("pathlib.Path.read_text", boom)
    assert _load_miss(p) == 0
