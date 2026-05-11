#!/usr/bin/env python3
"""L2 evidence metric · per-agent compass MCP call counts in 24h window.

Reads /home/ubuntu/nautilus-compass/.cache/verification_log.jsonl on
the cloud VM · counts entries grouped by agent_type and action ·
writes JSON to /var/log/compass-l2-metrics.json (and stdout).

Cron suggested:
   */5 * * * * /usr/bin/python3 /home/ubuntu/nautilus-compass/ops/compass_l2_metrics.py

Platform helix reads the JSON via:
   curl -s http://compass-vm-internal/compass-l2-metrics.json
or directly via shared file mount.

Output schema:
{
  "generated_at": "2026-05-11T05:30:12Z",
  "window_hours": 24,
  "totals": { "recall": 42, "drift_check": 18, "ingest_obs": 7, ... },
  "by_agent_type": {
    "nautilus-v5": {
      "recall": 30, "drift_check": 30, "ingest_obs": 30,
      "first_call": "2026-05-10T05:31:01Z",
      "last_call":  "2026-05-11T05:29:47Z"
    },
    "claude-code-compass-dialog": { ... },
    ...
  },
  "l2_evidence_gate": {
    "target_per_agent_per_day": 10,
    "agents_meeting_gate": ["nautilus-v5"],
    "agents_below_gate": ["nautilus-v6", "kairos"],
    "agents_absent": ["v7-souls-fusion"]
  }
}
"""
from __future__ import annotations

import json
import os
import sys
import time
from collections import defaultdict
from pathlib import Path


LOG_PATH = Path(os.environ.get(
    "COMPASS_VERIFICATION_LOG",
    "/home/ubuntu/.claude/plugins/nautilus-compass/.cache/verification_log.jsonl"
))
OUT_PATH = Path(os.environ.get(
    "COMPASS_L2_METRICS_OUT",
    "/var/log/compass-l2-metrics.json"
))
WINDOW_HOURS = int(os.environ.get("COMPASS_L2_WINDOW_HOURS", "24"))
L2_GATE_PER_AGENT_PER_DAY = int(os.environ.get("COMPASS_L2_GATE", "10"))

EXPECTED_AGENTS = [
    "nautilus-v5",
    "nautilus-v6",
    "kairos",
    "v7-souls-fusion",
    "claude-code-compass-dialog",
    "claude-code-platform-dialog",
]


def iso_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def parse_ts(s: str) -> float:
    """Parse ISO-8601 Z-suffix timestamp to epoch seconds. Returns 0 on fail."""
    try:
        return time.mktime(time.strptime(s, "%Y-%m-%dT%H:%M:%SZ")) - time.timezone
    except Exception:
        return 0.0


def main() -> int:
    if not LOG_PATH.exists():
        out = {
            "generated_at": iso_now(),
            "window_hours": WINDOW_HOURS,
            "error": f"verification log not found: {LOG_PATH}",
            "totals": {},
            "by_agent_type": {},
            "l2_evidence_gate": {
                "target_per_agent_per_day": L2_GATE_PER_AGENT_PER_DAY,
                "agents_meeting_gate": [],
                "agents_below_gate": [],
                "agents_absent": EXPECTED_AGENTS,
            },
        }
        _write(out)
        return 1

    cutoff = time.time() - WINDOW_HOURS * 3600
    totals = defaultdict(int)
    by_agent = defaultdict(lambda: {
        "_counts": defaultdict(int),
        "first_call": None,
        "last_call": None,
    })

    parsed = 0
    skipped = 0
    with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                skipped += 1
                continue
            ts_s = rec.get("ts", "")
            ts_ep = parse_ts(ts_s)
            if ts_ep < cutoff:
                continue
            action = rec.get("action", "unknown")
            # v1.2 fallback: daemon doesn't yet log agent_type per call (TODO
            # plumb COMPASS_AGENT_TYPE env from mcp_server through daemon_call
            # req · see #104). For now, group by session_id which uniquely
            # identifies the calling MCP client process.
            agent_type = rec.get("agent_type") or rec.get("session_id") or "unknown"
            totals[action] += 1
            agent_rec = by_agent[agent_type]
            agent_rec["_counts"][action] += 1
            if not agent_rec["first_call"] or ts_s < agent_rec["first_call"]:
                agent_rec["first_call"] = ts_s
            if not agent_rec["last_call"] or ts_s > agent_rec["last_call"]:
                agent_rec["last_call"] = ts_s
            parsed += 1

    # flatten _counts
    by_agent_out = {}
    for agent_type, rec in by_agent.items():
        flat = dict(rec["_counts"])
        flat["total"] = sum(rec["_counts"].values())
        flat["first_call"] = rec["first_call"]
        flat["last_call"] = rec["last_call"]
        by_agent_out[agent_type] = flat

    meeting_gate = sorted([a for a, r in by_agent_out.items()
                           if r["total"] >= L2_GATE_PER_AGENT_PER_DAY])
    below_gate = sorted([a for a, r in by_agent_out.items()
                         if 0 < r["total"] < L2_GATE_PER_AGENT_PER_DAY])
    absent = sorted(set(EXPECTED_AGENTS) - set(by_agent_out.keys()))

    out = {
        "generated_at": iso_now(),
        "window_hours": WINDOW_HOURS,
        "log_path": str(LOG_PATH),
        "log_records_parsed": parsed,
        "log_records_skipped": skipped,
        "totals": dict(totals),
        "by_agent_type": by_agent_out,
        "l2_evidence_gate": {
            "target_per_agent_per_day": L2_GATE_PER_AGENT_PER_DAY,
            "agents_meeting_gate": meeting_gate,
            "agents_below_gate": below_gate,
            "agents_absent": absent,
            "expected_agents": EXPECTED_AGENTS,
        },
    }
    _write(out)
    return 0


def _write(out: dict) -> None:
    payload = json.dumps(out, indent=2, ensure_ascii=False)
    try:
        OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUT_PATH.write_text(payload + "\n", encoding="utf-8")
    except PermissionError:
        sys.stderr.write(f"WARN · cannot write {OUT_PATH} · printing to stdout only\n")
    print(payload)


if __name__ == "__main__":
    sys.exit(main())
