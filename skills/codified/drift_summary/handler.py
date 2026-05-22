"""drift_summary handler · summarize compass drift events from .cache/drift_history.jsonl."""
from __future__ import annotations

import json
import time
from pathlib import Path


def _default_drift_log() -> Path:
    return (Path.home() / ".claude" / "plugins" / "nautilus-compass"
            / ".cache" / "drift_history.jsonl")


def _classify_alert(score: float) -> str:
    if score < -0.04:
        return "red"
    if score < -0.01:
        return "yellow"
    return "green"


def execute(lookback_days: int = 7, drift_log_path: str = "") -> dict:
    """Read drift log · return aggregate summary.

    Returns:
        {
            "total_events": int,
            "alert_counts": {"green": n, "yellow": n, "red": n},
            "top_negative_drifts": [{score, prompt_excerpt, ts}, ...],
            "first_seen_ts": str or None,
            "last_seen_ts": str or None,
            "log_path": str,
            "lookback_days": int,
        }
    """
    log_path = Path(drift_log_path) if drift_log_path else _default_drift_log()
    if not log_path.exists():
        return {
            "total_events": 0,
            "alert_counts": {"green": 0, "yellow": 0, "red": 0},
            "top_negative_drifts": [],
            "first_seen_ts": None,
            "last_seen_ts": None,
            "log_path": str(log_path),
            "lookback_days": lookback_days,
            "error": "drift log not found",
        }

    cutoff = time.time() - lookback_days * 86400
    events = []
    alert_counts = {"green": 0, "yellow": 0, "red": 0}

    with log_path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                evt = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_str = evt.get("ts", "") or evt.get("timestamp", "")
            try:
                if ts_str.isdigit():
                    ts_epoch = float(ts_str)
                else:
                    import datetime as _dt
                    ts_epoch = _dt.datetime.fromisoformat(
                        ts_str.replace("Z", "+00:00")
                    ).timestamp()
            except (ValueError, AttributeError):
                continue
            if ts_epoch < cutoff:
                continue

            score = float(evt.get("score", evt.get("drift_score", 0)) or 0)
            events.append({
                "score": score,
                "prompt_excerpt": (evt.get("prompt", "") or evt.get("query", ""))[:120],
                "ts": ts_str,
                "alert": _classify_alert(score),
            })
            alert_counts[_classify_alert(score)] += 1

    events_sorted_neg = sorted(
        [e for e in events if e["score"] < 0],
        key=lambda x: x["score"]
    )[:5]

    return {
        "total_events": len(events),
        "alert_counts": alert_counts,
        "top_negative_drifts": events_sorted_neg,
        "first_seen_ts": events[0]["ts"] if events else None,
        "last_seen_ts": events[-1]["ts"] if events else None,
        "log_path": str(log_path),
        "lookback_days": lookback_days,
    }


if __name__ == "__main__":
    import sys
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 7
    print(json.dumps(execute(lookback_days=days), indent=2, ensure_ascii=False))
