"""Watchdog / heartbeat layer for durable MCP.

Research insight: *checkpoint != durable*. Auto-reconnect (Tasks 1-4) only
helps while the server process is alive. A dead daemon needs EXTERNAL
detection — nothing inside the process can resurrect it. This module is that
external watcher: it periodically probes the daemon and, after K consecutive
failed probes, restarts the unit.

Design — the same discipline as ``event_store``: the decision core is pure and
fully injected, so it is 100% deterministic under test.

  · ``should_restart``      — pure boolean decision (truth-table tested).
  · ``HeartbeatMonitor``    — one ``tick()`` = probe → count/reset → maybe
                              restart. probe_fn / restart_fn injected; NO real
                              socket, NO real systemctl, NO real sleep here.
                              A probe that raises is treated as a miss (logged,
                              never propagated) — ``tick`` never raises.
  · ``tcp_probe``           — thin impure adapter: open a socket, return
                              connectable?  Kept tiny, out of the core.
  · ``systemd_restart`` /   — thin impure adapter: shell ``systemctl restart``.
    ``systemd_restart_cmd``   The command builder is pure and unit-tested; the
                              executor is not run from tests.

The systemd units in ``ops/`` are deploy templates — running them is a
separate, gated ops step (see those files' header comments).
"""

from __future__ import annotations

import logging
import pathlib
import socket
import subprocess
from typing import Callable, List, Optional

logger = logging.getLogger("mcp_durable.watchdog")


# ---------------------------------------------------------------------------
# Pure decision core
# ---------------------------------------------------------------------------

def should_restart(miss_count: int, threshold: int) -> bool:
    """True iff the daemon should be restarted now.

    Restart when ``miss_count`` has reached ``threshold`` consecutive misses.
    ``threshold`` must be >= 1; a threshold < 1 is nonsensical (it would mean
    "restart even when healthy") and is guarded to always return ``False`` so a
    misconfiguration can never cause a restart storm.
    """
    if threshold < 1:
        return False
    return miss_count >= threshold


class HeartbeatMonitor:
    """Stateful, fully-injected heartbeat loop. One step = one ``tick()``.

    All effects are injected:
      · ``probe_fn() -> bool``  — True = daemon healthy. May raise; a raised
                                  probe is counted as a miss (logged).
      · ``restart_fn() -> None``— called once when the threshold is crossed.
      · ``now_fn`` (optional)   — only used for log timestamps; never gates
                                  the decision, so the core stays deterministic.
    """

    def __init__(
        self,
        probe_fn: Callable[[], bool],
        restart_fn: Callable[[], None],
        threshold: int = 3,
        now_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        if threshold < 1:
            raise ValueError(f"threshold must be >= 1, got {threshold}")
        self._probe_fn = probe_fn
        self._restart_fn = restart_fn
        self._threshold = threshold
        self._now_fn = now_fn
        self.miss_count = 0

    def tick(self) -> bool:
        """Run one probe cycle. Returns the (effective) probe result.

        Never raises: a probe exception is swallowed and treated as a miss.
        On a successful probe the miss counter resets to 0. On a miss it
        increments; if that crosses the threshold, ``restart_fn`` is invoked
        exactly once and the counter resets (so we do not restart every tick
        while the daemon is still coming back up).
        """
        try:
            healthy = bool(self._probe_fn())
        except Exception as exc:  # a failed probe is a miss, not a crash.
            logger.warning("watchdog probe raised, counting as miss: %s", exc)
            healthy = False

        if healthy:
            self.miss_count = 0
            return True

        self.miss_count += 1
        logger.warning(
            "watchdog probe miss %d/%d", self.miss_count, self._threshold
        )
        if should_restart(self.miss_count, self._threshold):
            logger.error(
                "watchdog threshold reached (%d misses) — restarting daemon",
                self.miss_count,
            )
            try:
                self._restart_fn()
            except Exception as exc:  # restart failure must not crash the loop.
                logger.error("watchdog restart_fn failed: %s", exc)
            finally:
                self.miss_count = 0
        return False


# ---------------------------------------------------------------------------
# Impure adapters (tiny, kept out of the deterministic core)
# ---------------------------------------------------------------------------

def tcp_probe(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return True iff a TCP connection to ``host:port`` succeeds.

    The single real-socket touchpoint. Any connection error (refused, timeout,
    DNS, etc.) returns False — this is a health signal, never an exception.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def systemd_restart_cmd(unit: str, user: bool = False) -> List[str]:
    """Build the ``systemctl restart`` argv (pure — for testing/inspection).

    ``user=True`` targets the per-user manager (``systemctl --user``); the
    default is the system manager, matching the existing compass units
    (``User=ubuntu`` system services in ``ops/``).
    """
    cmd = ["systemctl"]
    if user:
        cmd.append("--user")
    cmd += ["restart", unit]
    return cmd


def systemd_restart(unit: str, user: bool = False) -> None:
    """Shell out to ``systemctl restart <unit>``. Impure — NOT run in tests."""
    cmd = systemd_restart_cmd(unit, user=user)
    logger.info("watchdog restarting unit: %s", " ".join(cmd))
    subprocess.run(cmd, check=True)


# ---------------------------------------------------------------------------
# Deploy entry point (impure; wires the adapters from env). NOT run in tests.
# ---------------------------------------------------------------------------

def _load_miss(path) -> int:
    """Read the persisted consecutive-miss count. Missing / corrupt / unreadable
    file → 0 (never raises): a lost state file must mean "start clean", not crash
    the watchdog.
    """
    try:
        return int(pathlib.Path(path).read_text().strip())
    except (OSError, ValueError) as exc:
        logger.warning("watchdog could not read miss state, defaulting 0: %s", exc)
        return 0


def _store_miss(path, n: int) -> None:
    """Persist the consecutive-miss count for the next fire. Write failure is
    logged, never raised — a watchdog that can't persist still must not crash.
    """
    try:
        p = pathlib.Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(str(n))
    except OSError as exc:
        logger.warning("watchdog could not persist miss state: %s", exc)


def _run_from_env() -> bool:
    """One-fire watchdog wiring for the systemd unit (``python -m``).

    Reads the prior miss count from the state file, runs one ``tick()``, then
    persists the new count. K accumulates across timer fires. Returns the
    (effective) probe result.
    """
    import os

    host = os.environ.get("COMPASS_MCP_WATCHDOG_HOST", "127.0.0.1")
    port = int(os.environ.get("COMPASS_MCP_WATCHDOG_PORT", "9877"))
    unit = os.environ.get("COMPASS_MCP_WATCHDOG_UNIT", "compass-mcp-tcp.service")
    threshold = int(os.environ.get("COMPASS_MCP_WATCHDOG_THRESHOLD", "3"))
    user = os.environ.get("COMPASS_MCP_WATCHDOG_USER", "0") == "1"
    state_path = os.environ.get(
        "COMPASS_MCP_WATCHDOG_STATE",
        "/home/ubuntu/nautilus-compass/.cache/mcp-watchdog.state",
    )

    mon = HeartbeatMonitor(
        probe_fn=lambda: tcp_probe(host, port),
        restart_fn=lambda: systemd_restart(unit, user=user),
        threshold=threshold,
    )
    mon.miss_count = _load_miss(state_path)
    healthy = mon.tick()
    _store_miss(state_path, mon.miss_count)
    return healthy


if __name__ == "__main__":  # pragma: no cover - deploy entry point
    logging.basicConfig(level=logging.INFO)
    _run_from_env()
