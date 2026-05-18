#!/usr/bin/env python3
"""Cross-dialog handoff notifier · cron every 5 min.

Watches ~/.claude/projects/*/memory/session_*.md for new entries with:
  · thread_id matching a watch list (e.g. 'compass-platform-handoff')
  · thread_role: outbound  (= the writer wants the OTHER dialog to see it)

When a new outbound session arrives, posts a Telegram message so the human
operator knows to open the receiving dialog and have it thread_recall.

This is the missing wire for cross-dialog flywheel B → flywheel A handoff.
Without it, sessions sit in compass memory until the receiving dialog
happens to thread_recall — which can be hours / days.

State:
  ~/.cache/compass/cross-dialog-notifier-state.json
  · seen: list of session_*.md basenames already notified (dedup)
  · seen[].ts: when notified (rotation · keep last 500)

Cron:
  */5 * * * * /home/ubuntu/nautilus-compass/ops/cross_dialog_notifier.sh \
              >> /home/ubuntu/.cache/compass/cross-dialog-notifier.log 2>&1

Env (loaded by bash wrapper from /home/ubuntu/nautilus-v5/.env):
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


MEM_BASE = Path(os.environ.get(
    "COMPASS_MEM_BASE",
    str(Path.home() / ".claude" / "projects")
))
STATE_FILE = Path(os.environ.get(
    "CROSS_DIALOG_STATE",
    str(Path.home() / ".cache" / "compass" / "cross-dialog-notifier-state.json")
))
WATCH_THREADS = os.environ.get(
    "CROSS_DIALOG_WATCH_THREADS",
    "compass-platform-handoff,compass-agent-handoff,compass-dogfood-L3,spec-V7-actuator-collapse"
).split(",")
MAX_SEEN = 500  # state file rotation
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
LOOKBACK_HOURS = int(os.environ.get("CROSS_DIALOG_LOOKBACK_H", "24"))


def _parse_frontmatter(text: str) -> dict:
    """Naive YAML frontmatter parser · expects --- delim · ---."""
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 4)
    if end < 0:
        return {}
    fm = {}
    for line in text[4:end].split("\n"):
        if ":" in line:
            k, _, v = line.partition(":")
            fm[k.strip().lower()] = v.strip()
    return fm


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seen": []}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen": []}


def _save_state(state: dict) -> None:
    try:
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        # rotate · keep last MAX_SEEN
        if len(state.get("seen", [])) > MAX_SEEN:
            state["seen"] = state["seen"][-MAX_SEEN:]
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
    except Exception as e:
        sys.stderr.write(f"WARN · state write fail: {e}\n")


def _send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        sys.stderr.write("ERR · TELEGRAM_BOT_TOKEN/CHAT_ID not set\n")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text[:4000],  # Telegram per-message limit
    }).encode("utf-8")
    try:
        with urlopen(Request(url, data=data), timeout=10) as resp:
            body = resp.read().decode("utf-8")
            return '"ok":true' in body
    except Exception as e:
        sys.stderr.write(f"telegram send fail: {e}\n")
        return False


def main() -> int:
    if not MEM_BASE.exists():
        sys.stderr.write(f"no MEM_BASE: {MEM_BASE}\n")
        return 0

    state = _load_state()
    seen: set[str] = set(state.get("seen", []))
    now = time.time()
    cutoff = now - LOOKBACK_HOURS * 3600

    new_entries = []
    for project_dir in MEM_BASE.iterdir():
        if not project_dir.is_dir() or project_dir.name.startswith("_"):
            continue
        mem = project_dir / "memory"
        if not mem.is_dir():
            continue
        for f in mem.glob("session_*.md"):
            try:
                mtime = f.stat().st_mtime
            except Exception:
                continue
            if mtime < cutoff:
                continue
            key = f"{project_dir.name}/{f.name}"
            if key in seen:
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            fm = _parse_frontmatter(text)
            thread_id = fm.get("thread_id", "")
            thread_role = fm.get("thread_role", "")
            if not thread_id:
                continue
            if thread_id not in WATCH_THREADS:
                continue
            # only notify on outbound (writer wants other side to see)
            # self_note + inbound stay quiet
            if thread_role != "outbound":
                continue
            new_entries.append((key, f.name, fm, project_dir.name))

    if not new_entries:
        print(f"{time.strftime('%FT%TZ', time.gmtime())} · no new outbound sessions in watch threads")
        return 0

    # sort by mtime ASC so oldest notified first
    new_entries.sort(key=lambda x: (MEM_BASE / x[3] / "memory" / x[1]).stat().st_mtime)

    # build telegram message (compact · multiple sessions in one msg)
    lines = [
        f"Cross-dialog handoff · {len(new_entries)} new outbound session(s)",
        "",
    ]
    for key, fname, fm, proj in new_entries:
        author = fm.get("agent", "unknown")
        thread = fm.get("thread_id", "")
        desc = fm.get("description", "")[:140]
        tags = fm.get("tags", "")[:80]
        lines.append(f"· {fname}")
        lines.append(f"  thread: {thread}  · author: {author}")
        if desc:
            lines.append(f"  desc: {desc}")
        lines.append("")
    lines.append("To consume: open receiving Claude Code dialog · run:")
    lines.append(f"  thread_recall({new_entries[0][2].get('thread_id', '')!r})")

    msg = "\n".join(lines)
    ok = _send_telegram(msg)

    if ok:
        for key, _, _, _ in new_entries:
            seen.add(key)
        state["seen"] = list(seen)
        _save_state(state)
        print(f"{time.strftime('%FT%TZ', time.gmtime())} · notified {len(new_entries)} new session(s)")
        return 0
    else:
        sys.stderr.write("notification failed · NOT marking as seen · will retry next tick\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
