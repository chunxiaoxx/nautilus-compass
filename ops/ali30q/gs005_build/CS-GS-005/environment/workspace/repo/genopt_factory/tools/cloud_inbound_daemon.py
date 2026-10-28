"""Cloud inbound daemon — 5min poll, surface INBOUND_*.md to my SSOT/memory.

Fix the recurring root cause (anchors #4 + #6): cross-dialog outbound
delivery = cloud `~/nautilus-soul-workspace/docs/`, not git. This daemon
picks up INBOUND_* files others have dropped in the cloud queue, and:
  1. Reads the file (utf-8 / gbk safe)
  2. Extracts a thread_id (5/12 close-ack convention: thread_role + thread_id
     in frontmatter; we extract if present, else tag 'no_thread_id')
  3. Writes a digest to memory/INBOUND_<date>_<thread>_<slug>.md (so I can
     reference it)
  4. Renames the file to `READ_<original>` to mark consumed (preserves the
     file; later diffs show I've seen it)
  5. Writes a /tmp/cloud_inbound_cron.log line for downstream consumers

Does NOT auto-process or auto-respond — the human (or a separate dialog)
decides what to do with the inbound. The daemon only surfaces.

Idempotent: re-running is safe. Stops after --max-iterations polls.

Usage:
    python genopt_factory/tools/cloud_inbound_daemon.py
    python genopt_factory/tools/cloud_inbound_daemon.py --interval 60 --max-iterations 1
"""

import argparse
import datetime
import json
import os
import pathlib
import subprocess
import sys
import time


CLOUD_HOST = "cloud"  # alias in ~/.ssh/config → 43.160.239.61:24860
CLOUD_DOCS = "~/nautilus-soul-workspace/docs"
LOCAL_MEMORY = pathlib.Path(__file__).resolve().parent.parent.parent / ".claude" / "projects" / "C--Users-chunx-Projects-nautilus-core" / "memory"
STATE_FILE = pathlib.Path.home() / ".nautilus" / "cloud_inbound_seen.json"


def ssh_ls_inbound():
    """Return list of INBOUND_*.md filenames in cloud docs."""
    try:
        out = subprocess.run(
            ["ssh", CLOUD_HOST, f"ls {CLOUD_DOCS} | grep '^INBOUND_' | sort"],
            capture_output=True, text=True, timeout=20,
        )
        if out.returncode != 0:
            return []
        return [l.strip() for l in out.stdout.splitlines() if l.strip()]
    except Exception as exc:
        print(f"[err] ssh_ls_inbound: {exc}", file=sys.stderr)
        return []


def ssh_cat(path):
    """Read cloud file as bytes; decode with utf-8 first, fall back to gbk.
    (5/17 close-ack + 6/2 outbound feedback show that older files may be
    encoded in non-utf-8; treat as bytes then decode safely.)
    """
    try:
        out = subprocess.run(
            ["ssh", CLOUD_HOST, f"cat {path}"],
            capture_output=True, timeout=20,
        )
        if out.returncode != 0:
            return None
        raw = out.stdout
        for enc in ("utf-8", "gbk", "utf-16", "latin-1"):
            try:
                return raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return raw.decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"[err] ssh_cat({path}): {exc}", file=sys.stderr)
        return None


def load_state():
    if STATE_FILE.is_file():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=1, ensure_ascii=False))


def extract_thread_id(body):
    """5/12 close-ack convention: thread_id in frontmatter (--- block)."""
    if not body or not body.startswith("---"):
        return "no_thread_id"
    end = body.find("---", 3)
    if end < 0:
        return "no_thread_id"
    for line in body[3:end].splitlines():
        line = line.strip()
        if line.startswith("thread_id:"):
            return line.split(":", 1)[1].strip()
    return "no_thread_id"


def surface_to_memory(filename, body, thread_id):
    """Write a digest to local memory/INBOUND_<date>_<thread>_<slug>.md"""
    LOCAL_MEMORY.mkdir(parents=True, exist_ok=True)
    today = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).strftime("%Y%m%d")
    digest_name = f"INBOUND_{today}_thread-{thread_id}_from_{filename[:-3]}.md"
    digest_path = LOCAL_MEMORY / digest_name
    if digest_path.is_file():
        return None  # already surfaced
    first_para = ""
    for line in body.splitlines():
        if line.strip() and not line.strip().startswith("#") and not line.strip().startswith("---"):
            first_para = line.strip()
            break
    digest = (
        f"# Inbound digest · {filename} (thread_id={thread_id}, surfaced {today})\n\n"
        f"**Source**: cloud `~/nautilus-soul-workspace/docs/{filename}`\n"
        f"**First paragraph**: {first_para[:200]}\n\n"
        f"```\n{body[:1500]}\n```\n"
    )
    digest_path.write_text(digest, encoding="utf-8")
    return digest_path


def log_ack_line(filename, thread_id, digest_path):
    """Append a 1-line ack to /tmp/cloud_inbound_cron.log for downstream consumers."""
    log_path = pathlib.Path("/tmp/cloud_inbound_cron.log")
    try:
        with open(log_path, "a", encoding="utf-8") as f:
            ts = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z"
            f.write(f"{ts}\tthread={thread_id}\tfile={filename}\tdigest={digest_path}\n")
    except OSError as exc:
        print(f"[warn] log_ack_line: {exc}", file=sys.stderr)


def mark_consumed(filename):
    """Rename INBOUND_*.md → READ_<original> in cloud to mark consumed."""
    if filename.startswith("READ_"):
        return False
    try:
        subprocess.run(
            ["ssh", CLOUD_HOST, f"cd {CLOUD_DOCS} && mv {filename} READ_{filename}"],
            capture_output=True, text=True, timeout=20,
        )
        return True
    except Exception as exc:
        print(f"[err] mark_consumed({filename}): {exc}", file=sys.stderr)
        return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=300,
                    help="poll interval in seconds (default 300 = 5 min)")
    ap.add_argument("--max-iterations", type=int, default=0,
                    help="0 = run forever; N = stop after N polls")
    ap.add_argument("--no-mark", action="store_true",
                    help="do not rename INBOUND_*.md to READ_*.md (just digest)")
    args = ap.parse_args()

    state = load_state()
    seen = state.get("seen", {})
    iteration = 0
    while True:
        iteration += 1
        inbounds = ssh_ls_inbound()
        new = [f for f in inbounds if f.startswith("INBOUND_") and f not in seen]
        print(f"[poll {iteration}] {len(inbounds)} inbound · {len(new)} new", flush=True)
        for f in new:
            body = ssh_cat(f"{CLOUD_DOCS}/{f}") or ""
            thread_id = extract_thread_id(body)
            digest_path = surface_to_memory(f, body, thread_id)
            consumed = mark_consumed(f) if not args.no_mark else False
            log_ack_line(f, thread_id, digest_path)
            seen[f] = {
                "surfaced_at": datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat() + "Z",
                "thread_id": thread_id,
                "digest": str(digest_path) if digest_path else None,
                "consumed": consumed,
            }
            print(f"  + {f}  thread={thread_id}  digest={digest_path}  consumed={consumed}",
                  flush=True)
        if new:
            state["seen"] = seen
            save_state(state)
        if args.max_iterations and iteration >= args.max_iterations:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()