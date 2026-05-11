#!/usr/bin/env python3
"""L2 evidence gate decision logic · stdout = Telegram message or empty.

Reads /var/log/compass-l2-metrics.json (produced by compass_l2_metrics.py).
Tracks per-agent consecutive-miss streak in /var/log/compass-l2-gate-streak.json.
Cooldowns alerts in /var/log/compass-l2-gate-last-alert.json.

Alert rule:
  · Required agents (V5/V6/V7/Kairos) must be at gate (≥ 10 calls/day).
  · Miss 3 consecutive 6h runs (= 18h continuous miss) → alert.
  · Cooldown 24h per agent after alert to avoid spam.

Output:
  · stdout: alert message text (Markdown) if alert needed
  · stdout: empty if no alert
  · exit 0 always (cron-friendly)
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path


METRICS_JSON = Path(os.environ.get(
    "COMPASS_L2_METRICS_OUT", "/var/log/compass-l2-metrics.json"))
STREAK_FILE = Path(os.environ.get(
    "COMPASS_L2_STREAK_FILE",
    str(Path.home() / ".cache" / "compass" / "l2-gate-streak.json")))
LAST_ALERT_FILE = Path(os.environ.get(
    "COMPASS_L2_LAST_ALERT",
    str(Path.home() / ".cache" / "compass" / "l2-gate-last-alert.json")))
ALERT_AFTER_RUNS = int(os.environ.get("COMPASS_L2_ALERT_AFTER", "3"))
ALERT_COOLDOWN_HRS = int(os.environ.get("COMPASS_L2_ALERT_COOLDOWN", "24"))

REQUIRED_AGENTS = ["nautilus-v5", "nautilus-v6", "v7-souls-fusion", "kairos"]


def _read_json(path: Path, default):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _write_json(path: Path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2), encoding="utf-8")
    except PermissionError:
        sys.stderr.write(f"WARN · cannot write {path}\n")


def main() -> int:
    if not METRICS_JSON.exists():
        sys.stderr.write(f"ERR · metrics not found: {METRICS_JSON}\n")
        return 0  # cron-friendly · don't fail

    metrics = _read_json(METRICS_JSON, {})
    gate = metrics.get("l2_evidence_gate", {})
    absent = set(gate.get("agents_absent", []))
    below = set(gate.get("agents_below_gate", []))

    streak = _read_json(STREAK_FILE, {})
    last_alert = _read_json(LAST_ALERT_FILE, {})

    now = time.time()
    cooldown = ALERT_COOLDOWN_HRS * 3600

    # update streaks for required agents
    for agent in REQUIRED_AGENTS:
        if agent in absent or agent in below:
            streak[agent] = streak.get(agent, 0) + 1
        else:
            streak[agent] = 0  # reset · at gate

    # decide who to alert
    to_alert = []
    for agent in REQUIRED_AGENTS:
        run_count = streak.get(agent, 0)
        if run_count < ALERT_AFTER_RUNS:
            continue
        last = last_alert.get(agent, 0)
        if now - last < cooldown:
            continue
        status = "absent" if agent in absent else "below_gate"
        to_alert.append({
            "agent": agent,
            "missed_runs": run_count,
            "status": status,
        })
        last_alert[agent] = now

    _write_json(STREAK_FILE, streak)
    _write_json(LAST_ALERT_FILE, last_alert)

    if not to_alert:
        return 0  # no message · cron logs "no alert"

    # build Telegram message (plain text · no Markdown to avoid parse errors on backticks)
    lines = ["compass · L2 evidence gate MISS", ""]
    for a in to_alert:
        lines.append(
            f"  - {a['agent']} · {a['status']} · "
            f"missed {a['missed_runs']} consecutive 6h windows"
        )
    lines += [
        "",
        "L5 dispatch (specs/SPEC-S1) BLOCKED until V5/V6/V7/Kairos hit "
        ">=10 calls/day for 3 consecutive days.",
        "",
        "See specs/DISPATCH_PROTOCOL.md §0 · platform-dialog must wire "
        "V5 daemon cycle with compass.recall + drift_check.",
    ]
    sys.stdout.write("\n".join(lines))
    return 0


if __name__ == "__main__":
    sys.exit(main())
