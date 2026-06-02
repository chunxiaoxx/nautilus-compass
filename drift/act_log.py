"""E.fix-1 (2026-05-30) · drift alert ack writer + reader.

Background (5/27 finding · session_20260527_drift_loop_open_tuneout):
detection side wrote 25k+ events to `.cache/drift_mitigation_log.jsonl`
(recall.py:159 writer) with stable `alert_id` per fire · but ZERO ack
records were ever written → act-on rate uncomputable → drift loop open.

Plan §E.1 originally proposed a parallel `telemetry/act_on_log.jsonl`
sidecar. Audit found this would add a 4th telemetry stream (existing:
usage.jsonl, drift_mitigation_log.jsonl, drift_act_log.jsonl). Instead,
this module writes ack records into the SAME drift_mitigation_log.jsonl
sidecar, distinguished by `kind: "ack"`. audit_kpi.act_on_rate then
joins fires + acks by alert_id.

`log_drift_ack` is the ack-writing primitive. Callers:
- feedback.py:cmd_log (E.fix-3 wire · user fp/tp labels → ack)
- future: stop_hook auto-ack on agent self-acknowledgement text
- future: mid_session_hook on explicit "drift fire" text-pattern match

Status values (free-form · suggested):
- "fp"           — user marked false positive via feedback CLI
- "tp"           — user marked true positive via feedback CLI
- "acknowledged" — agent text response acknowledged the alert
- "ignored"      — agent explicitly chose not to act
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Iterator, Optional

DEFAULT_SIDECAR = (
    Path.home()
    / ".claude"
    / "plugins"
    / "nautilus-compass"
    / ".cache"
    / "drift_mitigation_log.jsonl"
)


def log_drift_ack(
    alert_id: str,
    status: str,
    sidecar: Optional[Path] = None,
    source: str = "",
    note: str = "",
) -> None:
    """Append an ack record for a drift alert to the mitigation log sidecar.

    No-op when alert_id is empty/falsy (defensive · callers may pass missing ids).
    Errors writing the file are swallowed silently to avoid disrupting the
    caller's path (this is observability code · must not break the host).
    """
    if not alert_id:
        return
    path = sidecar if sidecar is not None else DEFAULT_SIDECAR
    rec = {
        "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "kind": "ack",
        "alert_id": alert_id,
        "status": status,
    }
    if source:
        rec["source"] = source
    if note:
        rec["note"] = note
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def iter_drift_events(sidecar: Optional[Path] = None) -> Iterator[dict]:
    """Yield drift mitigation log records · safe on missing file / corrupt lines."""
    path = sidecar if sidecar is not None else DEFAULT_SIDECAR
    if not path.exists():
        return
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            yield json.loads(line)
        except Exception:
            continue
