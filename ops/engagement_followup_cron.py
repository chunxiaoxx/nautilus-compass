"""Engagement followup · daily 真扫 7d+ 无回 outreach · INSERT followup bounty into raid.

Cron (cloud):
  30 9 * * * /home/ubuntu/nautilus-compass/ops/engagement_followup_cron.sh \
              >> /home/ubuntu/.cache/compass/engagement-followup.log 2>&1

Flow:
  1. PG scan: completed outreach bounties where posted_at in [7d, 21d) and no engagement signal
  2. Engagement signal = either (a) reply bounty created with same thread_id, or (b) result_url has known reply marker
  3. INSERT followup bounty:
     - task_type='outreach-followup'
     - parent_task_id=<original bounty_id>
     - assigned_to='nautilus-prime-001'
  4. raid: nautilus-prime-001 generates short polite followup · anchors gate · publish through same channel
  5. State file tracks which bounties have been followed-up (don't double-followup)

No human review.
"""
from __future__ import annotations
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg
except ImportError:
    sys.stderr.write("psycopg not installed · pip install psycopg\n")
    sys.exit(1)


DSN = os.environ.get("NAUTILUS_DSN", "").strip()
STATE_FILE = Path(os.environ.get(
    "ENGAGEMENT_FOLLOWUP_STATE",
    str(Path.home() / ".cache" / "compass" / "engagement-followup-state.json"),
))
MAX_FOLLOWUPS_PER_RUN = int(os.environ.get("ENGAGEMENT_MAX_FOLLOWUPS", "5"))
FOLLOWUP_AGE_MIN_DAYS = int(os.environ.get("ENGAGEMENT_FOLLOWUP_AGE_MIN", "7"))
FOLLOWUP_AGE_MAX_DAYS = int(os.environ.get("ENGAGEMENT_FOLLOWUP_AGE_MAX", "21"))


def _require_dsn(value: str, variable_name: str) -> str:
    if not value:
        raise RuntimeError(f"{variable_name} is required")
    return value


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"followed_up_bounty_ids": [], "dispatched_count": 0, "last_run_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"followed_up_bounty_ids": [], "dispatched_count": 0, "last_run_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["followed_up_bounty_ids"] = state.get("followed_up_bounty_ids", [])[-1000:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _find_stale_outreach(conn) -> list[dict]:
    """Find completed outreach bounties old enough for followup, with no reply yet.

    Schema check: assumes platform_bounties has columns
      bounty_id, channel, source, status, posted_at, result_url, metadata
    """
    rows = conn.execute(f"""
        SELECT
            b.bounty_id,
            b.channel,
            b.source,
            b.status,
            b.posted_at,
            b.result_url,
            b.metadata,
            b.title
        FROM platform_bounties b
        WHERE b.source LIKE 'compass-outreach-%'
          AND b.status = 'completed'
          AND b.posted_at < NOW() - interval '{FOLLOWUP_AGE_MIN_DAYS} days'
          AND b.posted_at > NOW() - interval '{FOLLOWUP_AGE_MAX_DAYS} days'
          AND b.source NOT LIKE 'compass-outreach-followup%'
          AND NOT EXISTS (
              SELECT 1 FROM platform_bounties f
              WHERE f.source = 'compass-outreach-followup'
                AND f.metadata->>'parent_bounty_id' = b.bounty_id
          )
          AND NOT EXISTS (
              SELECT 1 FROM platform_bounties r
              WHERE r.source = 'compass-outreach-gmail-inbound'
                AND r.posted_at > b.posted_at
                AND r.metadata->>'thread_subject_match' = 'true'
          )
        ORDER BY b.posted_at ASC
        LIMIT 20
    """).fetchall()
    keys = [
        "bounty_id", "channel", "source", "status",
        "posted_at", "result_url", "metadata", "title",
    ]
    return [dict(zip(keys, r)) for r in rows]


def _insert_followup_bounty(conn, parent: dict) -> str | None:
    parent_id = parent["bounty_id"]
    title = f"Followup: {(parent.get('title') or 'outreach')[:140]}"
    channel = parent.get("channel") or "email"
    parent_meta = parent.get("metadata") or {}
    if isinstance(parent_meta, str):
        try:
            parent_meta = json.loads(parent_meta)
        except Exception:
            parent_meta = {}

    days_since = "?"
    try:
        posted = parent["posted_at"]
        if hasattr(posted, "isoformat"):
            now = datetime.now(timezone.utc)
            days_since = (now - posted).days
    except Exception:
        pass

    description = (
        f"Followup outreach · parent_bounty_id={parent_id}\n"
        f"channel: {channel}\n"
        f"original posted: {parent['posted_at']}\n"
        f"days since: {days_since}\n"
        f"original result_url: {parent.get('result_url') or '(none)'}\n\n"
        f"task: nautilus-prime-001 · short polite followup (anchors_outreach_quality gate) · "
        f"recall original outreach via compass thread_recall · don't repeat content · "
        f"offer a smaller next step (e.g. \"single-transcript Colab\" instead of \"50+50 transcripts\"). "
        f"Skip if drift_check rejects (means we'd come across as needy)."
    )
    new_metadata = {
        "parent_bounty_id": parent_id,
        "parent_channel": channel,
        "parent_posted_at": str(parent["posted_at"]),
        "followup_attempt": 1,
        "discovery_ts": datetime.now(timezone.utc).isoformat(),
    }
    new_bounty_id = f"outreach-followup-{parent_id[:48]}"
    try:
        conn.execute(
            """
            INSERT INTO platform_bounties (
                bounty_id, title, description, reward_nau,
                task_type, status, posted_by,
                channel, source, asset_path, assigned_to,
                parent_task_id, metadata, posted_at
            ) VALUES (
                %s, %s, %s, 35,
                'outreach-followup', 'open', 'compass-engagement-followup-cron',
                %s, 'compass-outreach-followup', 'inline-text', 'nautilus-prime-001',
                %s, %s, NOW()
            )
            ON CONFLICT (bounty_id) DO NOTHING
            """,
            (new_bounty_id, title, description, channel, parent_id, json.dumps(new_metadata)),
        )
        return new_bounty_id
    except Exception as e:
        sys.stderr.write(f"INSERT followup fail for {parent_id}: {e!r}\n")
        return None


def main() -> int:
    state = _load_state()
    followed_up = set(state.get("followed_up_bounty_ids", []))
    dispatched = 0
    skipped_already = 0
    errors = 0

    try:
        conn = psycopg.connect(
            _require_dsn(DSN, "NAUTILUS_DSN"),
            autocommit=True,
        )
    except Exception as e:
        sys.stderr.write(f"PG connect fail: {type(e).__name__}\n")
        return 1

    try:
        stale = _find_stale_outreach(conn)
        print(f"found {len(stale)} stale outreach bounties (age {FOLLOWUP_AGE_MIN_DAYS}-{FOLLOWUP_AGE_MAX_DAYS}d)")
        for parent in stale:
            if dispatched >= MAX_FOLLOWUPS_PER_RUN:
                break
            if parent["bounty_id"] in followed_up:
                skipped_already += 1
                continue
            new_id = _insert_followup_bounty(conn, parent)
            if new_id:
                followed_up.add(parent["bounty_id"])
                dispatched += 1
                print(f"followup dispatched · {new_id} (parent={parent['bounty_id']} channel={parent.get('channel')})")
            else:
                errors += 1
    finally:
        conn.close()

    state["followed_up_bounty_ids"] = sorted(followed_up)
    state["dispatched_count"] = int(state.get("dispatched_count", 0)) + dispatched
    state["last_run_ts"] = int(time.time())
    _save_state(state)

    print(
        f"{datetime.now().isoformat(timespec='seconds')} · "
        f"dispatched={dispatched} skipped_already={skipped_already} errors={errors} "
        f"total_dispatched={state['dispatched_count']}"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
