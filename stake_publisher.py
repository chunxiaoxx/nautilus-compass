"""compass v0.9.5 · stake event publisher · #4 fusion runtime.

Polls ~/.compass/stake_events/*.json · POSTs each to nautilus stake module
via A2A protocol · marks as processed.

Run:
  python stake_publisher.py serve         # daemon mode · poll every 60s
  python stake_publisher.py once          # single pass · for testing
  python stake_publisher.py status        # show pending count

Architecture (per paper/STAKE_DRIFT_COUPLING.md):
  attach_memory.py emits drift event → ~/.compass/stake_events/<ts>.json
  stake_publisher.py polls + posts    → A2A: STAKE_EVENT message
  Nautilus stake module consumes      → applies stake_penalty / stake_bonus
                                      → returns result via A2A reply
  publisher writes result + moves     → ~/.compass/stake_events/processed/

Failure handling:
  · Network error: keep file (retry next pass)
  · Repeat fail > N times: move to .failed/ · alert
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

EVENTS_DIR = Path.home() / ".compass" / "stake_events"
PROCESSED_DIR = EVENTS_DIR / "processed"
FAILED_DIR = EVENTS_DIR / "failed"

A2A_REGISTRY_URL = os.environ.get(
    "COMPASS_A2A_STAKE_URL",
    "https://a2a-registry.nautilus.social/a2a/messages"
)
NAUTILUS_TOKEN = os.environ.get("NAUTILUS_API_TOKEN", "")
POLL_INTERVAL_S = int(os.environ.get("COMPASS_STAKE_POLL_S", "60"))
MAX_RETRIES = 3
TIMEOUT = 10


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_event(path: Path) -> dict | None:
    try:
        ev = json.loads(path.read_text(encoding="utf-8"))
        return ev
    except Exception as e:
        sys.stderr.write(f"[stake] {path.name} bad JSON: {e}\n")
        return None


def post_a2a_event(event: dict) -> tuple[bool, str]:
    """POST event to nautilus stake A2A endpoint · return (ok, reason_or_response)."""
    envelope = {
        "protocol": "a2a/v1",
        "from": "compass-memory",
        "to": "nautilus-stake",
        "ts": now_iso(),
        "msg_id": f"sevt-{int(time.time()*1000)}",
        "type": "DRIFT_EVENT",
        "payload": event,
    }
    data = json.dumps(envelope, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        A2A_REGISTRY_URL, data=data, method="POST",
        headers={
            "Content-Type": "application/json",
            "User-Agent": "compass-stake-publisher/0.9.5",
            **({"Authorization": f"Bearer {NAUTILUS_TOKEN}"} if NAUTILUS_TOKEN else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            body = resp.read().decode("utf-8")
            try:
                d = json.loads(body)
                if d.get("status") == "ok":
                    return True, body[:300]
                return False, f"a2a error: {body[:300]}"
            except Exception:
                return True, body[:300]   # got 200 · not JSON
    except urllib.error.HTTPError as e:
        return False, f"http {e.code}: {e.reason}"
    except urllib.error.URLError as e:
        return False, f"url error: {e.reason}"
    except Exception as e:
        return False, f"unknown: {type(e).__name__}: {e}"


def consume_one(path: Path) -> str:
    """Returns: 'ok' | 'kept' | 'failed'."""
    ev = load_event(path)
    if not ev:
        # Bad JSON · move to failed
        FAILED_DIR.mkdir(parents=True, exist_ok=True)
        path.rename(FAILED_DIR / path.name)
        return "failed"

    retries = ev.get("_retries", 0)
    if retries >= MAX_RETRIES:
        FAILED_DIR.mkdir(parents=True, exist_ok=True)
        path.rename(FAILED_DIR / path.name)
        sys.stderr.write(f"[stake] giving up on {path.name} after {retries} retries\n")
        return "failed"

    ok, info = post_a2a_event(ev)
    if ok:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        ev["_processed_at"] = now_iso()
        ev["_response"] = info[:300]
        target = PROCESSED_DIR / path.name
        target.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
        path.unlink()
        return "ok"
    else:
        ev["_retries"] = retries + 1
        ev["_last_error"] = info[:200]
        ev["_last_attempt"] = now_iso()
        path.write_text(json.dumps(ev, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.stderr.write(f"[stake] {path.name} kept (retry {retries+1}/{MAX_RETRIES}): {info[:100]}\n")
        return "kept"


def status_cmd():
    pending = list(EVENTS_DIR.glob("*.json")) if EVENTS_DIR.exists() else []
    processed = list(PROCESSED_DIR.glob("*.json")) if PROCESSED_DIR.exists() else []
    failed = list(FAILED_DIR.glob("*.json")) if FAILED_DIR.exists() else []
    print(f"compass stake publisher status:")
    print(f"  events_dir: {EVENTS_DIR}")
    print(f"  pending:    {len(pending)}")
    print(f"  processed:  {len(processed)}")
    print(f"  failed:     {len(failed)}")
    if pending:
        print(f"  next: {pending[0].name}")


def once_pass():
    """One sweep · return summary."""
    if not EVENTS_DIR.exists():
        EVENTS_DIR.mkdir(parents=True, exist_ok=True)
        print(f"[stake] events dir created at {EVENTS_DIR}")
    pending = sorted(EVENTS_DIR.glob("*.json"))
    if not pending:
        print(f"[stake] 0 pending events")
        return {"ok": 0, "kept": 0, "failed": 0}
    counts = {"ok": 0, "kept": 0, "failed": 0}
    for p in pending:
        r = consume_one(p)
        counts[r] += 1
    print(f"[stake] {len(pending)} processed: ok={counts['ok']} kept={counts['kept']} failed={counts['failed']}")
    return counts


def serve_cmd():
    print(f"[stake] starting publisher · interval={POLL_INTERVAL_S}s · target={A2A_REGISTRY_URL}")
    while True:
        try:
            once_pass()
        except KeyboardInterrupt:
            print("[stake] interrupted by user · exiting")
            return
        except Exception as e:
            sys.stderr.write(f"[stake] pass failed: {e}\n")
        time.sleep(POLL_INTERVAL_S)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["serve", "once", "status"])
    args = p.parse_args()

    if args.cmd == "status":
        status_cmd()
    elif args.cmd == "once":
        once_pass()
    elif args.cmd == "serve":
        serve_cmd()


if __name__ == "__main__":
    main()
