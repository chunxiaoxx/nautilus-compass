#!/usr/bin/env python3
"""Compass health cron · poll /compass/health every 5 min · alert on degraded.

State file dedup · don't spam Telegram with same alert.
State persists last-known degraded_reasons set · only push when set changes.

Cron (cloud):
  */5 * * * * /home/ubuntu/nautilus-compass/ops/compass_health_cron.sh \\
              >> /home/ubuntu/.cache/compass/health-cron.log 2>&1

Env (loaded by bash wrapper):
  TELEGRAM_BOT_TOKEN · TELEGRAM_CHAT_ID
"""
from __future__ import annotations
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen, Request


HEALTH_URL = "http://127.0.0.1:8770/compass/health"
STATE_FILE = Path(os.environ.get(
    "COMPASS_HEALTH_STATE",
    str(Path.home() / ".cache" / "compass" / "health-cron-state.json")
))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"last_degraded": [], "last_tier": "unknown", "last_pushed_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"last_degraded": [], "last_tier": "unknown", "last_pushed_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        sys.stderr.write("ERR · TELEGRAM creds not set\n")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}).encode("utf-8")
    try:
        with urlopen(Request(url, data=data), timeout=10) as resp:
            return '"ok":true' in resp.read().decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"telegram fail: {e!r}\n")
        return False


def main() -> int:
    try:
        with urlopen(HEALTH_URL, timeout=5) as resp:
            health = json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        # Gateway itself down · highest severity alert
        _send_telegram(f"🔴 compass /compass/health unreachable · {e!r}")
        return 1

    degraded = sorted(health.get("degraded_reasons", []))
    tier = health.get("tier", "unknown")
    state = _load_state()
    prev_degraded = sorted(state.get("last_degraded", []))
    prev_tier = state.get("last_tier", "unknown")
    now = int(time.time())

    # Decide whether to push:
    # 1. degraded set changed (new issue / issue resolved)
    # 2. tier changed
    # 3. still degraded > 1 hour since last push (re-remind)
    push = False
    reason = ""
    if degraded != prev_degraded:
        push = True
        if degraded and not prev_degraded:
            reason = "newly degraded"
        elif prev_degraded and not degraded:
            reason = "recovered"
        else:
            reason = "degraded reasons changed"
    elif tier != prev_tier:
        push = True
        reason = f"tier transition: {prev_tier} → {tier}"
    elif degraded and (now - state.get("last_pushed_ts", 0)) > 3600:
        push = True
        reason = "still degraded · 1h re-remind"

    if push:
        components = health.get("components", {})
        ac = health.get("agent_calls_last_hour", {})
        lines = [
            f"compass /compass/health · {reason}",
            f"tier: {tier} · ok: {health.get('ok')}",
            f"ts: {time.strftime('%Y-%m-%d %H:%M:%S %z', time.localtime(now))}",
            "",
            "components:",
        ]
        for name, c in components.items():
            r = c.get("reachable")
            lat = c.get("latency_ms", "?")
            tag = "✓" if r else "✗"
            lines.append(f"  {tag} {name} · {lat}ms")
        lines.append("")
        if degraded:
            lines.append("degraded:")
            for d in degraded:
                lines.append(f"  · {d}")
        elif prev_degraded:
            lines.append("recovered from:")
            for d in prev_degraded:
                lines.append(f"  · {d}")
        lines.append("")
        load = health.get("load_avg", [0, 0, 0])
        lines.append(f"load avg: {load[0]:.2f} · {load[1]:.2f} · {load[2]:.2f}")
        lines.append(f"mem avail: {health.get('memory_available_mb', '?')} MB")
        if ac:
            top = ", ".join(f"{k}={v}" for k, v in list(ac.items())[:5])
            lines.append(f"agent calls 1h: {top}")
        msg = "\n".join(lines)
        ok = _send_telegram(msg)
        if ok:
            state["last_degraded"] = degraded
            state["last_tier"] = tier
            state["last_pushed_ts"] = now
            _save_state(state)
            print(f"{time.strftime('%FT%TZ', time.gmtime())} · pushed · {reason}")
        else:
            print(f"{time.strftime('%FT%TZ', time.gmtime())} · push fail · NOT updating state")
            return 1
    else:
        # also update last_tier silently when same degraded set
        if tier != prev_tier or degraded != prev_degraded:
            state["last_degraded"] = degraded
            state["last_tier"] = tier
            _save_state(state)
        print(f"{time.strftime('%FT%TZ', time.gmtime())} · health OK · tier={tier} · no alert")
    return 0


if __name__ == "__main__":
    sys.exit(main())
