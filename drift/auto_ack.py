"""H.1 (2026-05-30) · stop_hook auto-detect drift alert acks in session text.

Closes the 5/27 drift loop open finding's last unmeasured side: agent
self-acknowledgement of drift alerts (vs the user-CLI-only path via E.fix-3).

Algorithm (rule-based · no LLM · stop_hook policy):
1. Find every `a-XXXXXXXX` literal (8 hex chars · daemon alert_id format).
2. For each occurrence, look in a ±200 char window for ack signals:
   - explicit fp:  "fp" / "false positive" / "标 FP" / "mark fp"
   - explicit tp:  "tp" / "true positive" / "标 TP" / "mark tp"
   - generic ack:  "drift fire" / "ack" / "acknowledg" / "R1 alert" / "自停"
3. Dedupe by alert_id with rank fp > tp > acknowledged (strongest verdict wins).

Conservative bias: skip alert_ids with no nearby ack signal · avoid
over-firing on bare references ("see alert a-xxx in last session").

stop_hook wires this by reading the just-written session memory body and
calling drift.act_log.log_drift_ack(alert_id, status, source="stop_hook_auto")
for each extracted entry.
"""
from __future__ import annotations

import re
from typing import Iterable

# Daemon alert_id format: "a-" followed by 8 lowercase hex chars.
_ALERT_ID_RE = re.compile(r"\ba-[0-9a-f]{8}\b")
_ACK_WINDOW_CHARS = 200

# Status detectors · ordered by strength (strongest first). Each entry is
# (status, list of regex patterns). When multiple statuses match for one id,
# the earlier-listed (stronger) one wins.
_STATUS_PATTERNS: list[tuple[str, list[re.Pattern]]] = [
    (
        "fp",
        [
            re.compile(r"\bfp\b", re.IGNORECASE),
            re.compile(r"false[ \-]positive", re.IGNORECASE),
            re.compile(r"标\s*FP", re.IGNORECASE),
            re.compile(r"mark[ \-]+fp", re.IGNORECASE),
        ],
    ),
    (
        "tp",
        [
            re.compile(r"\btp\b", re.IGNORECASE),
            re.compile(r"true[ \-]positive", re.IGNORECASE),
            re.compile(r"标\s*TP", re.IGNORECASE),
            re.compile(r"mark[ \-]+tp", re.IGNORECASE),
        ],
    ),
    (
        "acknowledged",
        [
            re.compile(r"drift\s*fire", re.IGNORECASE),
            re.compile(r"acknowledg", re.IGNORECASE),
            re.compile(r"\back(?:ed|ing)?\b", re.IGNORECASE),
            re.compile(r"R1\s*alert", re.IGNORECASE),
            re.compile(r"自停"),
            re.compile(r"R1\s*mitigation", re.IGNORECASE),
        ],
    ),
]

_STATUS_RANK = {"fp": 3, "tp": 2, "acknowledged": 1}


def _detect_status(window: str) -> str | None:
    """Return strongest matching status in window, or None when nothing matches."""
    for status, patterns in _STATUS_PATTERNS:
        for pat in patterns:
            if pat.search(window):
                return status
    return None


def extract_acks_from_text(text: str) -> list[dict]:
    """Find drift alert acks in text.

    Returns list of {"alert_id": str, "status": str, "snippet": str},
    one entry per distinct alert_id. snippet is the ±60 char context.
    Same alert_id mentioned multiple times → strongest verdict wins
    (fp > tp > acknowledged).
    """
    if not text:
        return []

    # Map alert_id → best (rank, status, snippet) seen so far.
    best: dict[str, tuple[int, str, str]] = {}

    for m in _ALERT_ID_RE.finditer(text):
        alert_id = m.group(0)
        start = max(0, m.start() - _ACK_WINDOW_CHARS)
        end = min(len(text), m.end() + _ACK_WINDOW_CHARS)
        # Cap at paragraph break · prevents cross-talk between distinct alerts
        # separated by blank lines (common in agent prose). See test
        # test_extract_handles_multiple_distinct_alerts for the bug this guards.
        pre = text[start:m.start()]
        para_back = pre.rfind("\n\n")
        if para_back >= 0:
            start = start + para_back + 2
        post = text[m.end():end]
        para_fwd = post.find("\n\n")
        if para_fwd >= 0:
            end = m.end() + para_fwd
        window = text[start:end]
        status = _detect_status(window)
        if status is None:
            continue
        rank = _STATUS_RANK.get(status, 0)
        snippet = text[max(0, m.start() - 30): min(len(text), m.end() + 30)]
        if alert_id not in best or rank > best[alert_id][0]:
            best[alert_id] = (rank, status, snippet)

    return [
        {"alert_id": aid, "status": st, "snippet": snip}
        for aid, (_, st, snip) in best.items()
    ]


def emit_acks_to_sidecar(
    acks: Iterable[dict],
    source: str = "stop_hook_auto",
    sidecar=None,
) -> int:
    """Write detected acks via drift.act_log.log_drift_ack.

    Returns count of acks written. No-op when input empty. Errors swallowed
    silently (observability code must not break the calling stop_hook).
    """
    from drift.act_log import log_drift_ack

    n = 0
    for a in acks:
        try:
            log_drift_ack(
                a.get("alert_id", ""),
                a.get("status", "acknowledged"),
                sidecar=sidecar,
                source=source,
                note=a.get("snippet", "")[:120],
            )
            n += 1
        except Exception:
            continue
    return n
