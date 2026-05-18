"""Gmail inbound monitor · 每 15min 真扫 unread · 真 reply 进 raid as outreach-reply-draft bounty.

Cron (cloud):
  */15 * * * * /home/ubuntu/nautilus-compass/ops/gmail_inbound_monitor_cron.sh \
              >> /home/ubuntu/.cache/compass/gmail-inbound.log 2>&1

Flow:
  1. Gmail API list unread newer_than:2d
  2. Filter: From: is in known outreach contact list (we've sent to them) OR has nautilus/compass keyword
  3. Dedupe via state file
  4. INSERT bounty:
     - task_type='outreach-reply-draft'
     - source='compass-outreach-gmail-inbound'
     - assigned_to='nautilus-prime-001'
     - channel='email'
     - payload contains: from, subject, body snippet, thread_id, gmail_msg_id
  5. raid: nautilus-prime-001 generates personalized reply · anchors_outreach_quality gate · saves to Gmail drafts
  6. Human (you) just clicks send in Gmail UI (already that low-friction)

Auth: ~/.gmail/token.json (gmail.compose scope · cannot send · safe)
We add gmail.readonly scope for inbox listing.
"""
from __future__ import annotations
import base64
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

try:
    import psycopg
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
except ImportError as e:
    sys.stderr.write(f"missing deps: {e!r} · pip install psycopg google-api-python-client google-auth-oauthlib\n")
    sys.exit(1)


DSN = os.environ.get(
    "NAUTILUS_DSN",
    "postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production",
)
GMAIL_TOKEN = Path(os.environ.get(
    "GMAIL_TOKEN_PATH",
    str(Path.home() / ".gmail" / "token.json"),
))
STATE_FILE = Path(os.environ.get(
    "GMAIL_INBOUND_STATE",
    str(Path.home() / ".cache" / "compass" / "gmail-inbound-state.json"),
))

# scope: compose (already authorized) + readonly for inbox listing
SCOPES = [
    "https://www.googleapis.com/auth/gmail.compose",
    "https://www.googleapis.com/auth/gmail.readonly",
]
LOOKBACK_DAYS = int(os.environ.get("GMAIL_INBOUND_LOOKBACK_DAYS", "2"))
MAX_BOUNTIES_PER_RUN = int(os.environ.get("GMAIL_INBOUND_MAX_BOUNTIES", "10"))
# keywords that mark inbound as relevant (besides known senders)
RELEVANCE_KEYWORDS = re.compile(
    r"compass|nautilus|drift|persona|agent[- ]memory|jailbreak|persona drift|"
    r"anchor pack|behavioral monitor|MCP|2605\.09863|HuggingFace",
    re.IGNORECASE,
)


def _load_state() -> dict:
    if not STATE_FILE.exists():
        return {"seen_msg_ids": [], "dispatched_count": 0, "last_run_ts": 0}
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"seen_msg_ids": [], "dispatched_count": 0, "last_run_ts": 0}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    state["seen_msg_ids"] = state.get("seen_msg_ids", [])[-2000:]
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _load_creds() -> Credentials | None:
    if not GMAIL_TOKEN.exists():
        sys.stderr.write(f"gmail token missing: {GMAIL_TOKEN}\n")
        return None
    creds = Credentials.from_authorized_user_file(str(GMAIL_TOKEN), SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                GMAIL_TOKEN.write_text(creds.to_json(), encoding="utf-8")
            except Exception as e:
                sys.stderr.write(f"refresh fail: {e!r}\n")
                return None
    return creds


def _decode_part(part: dict) -> str:
    body = part.get("body", {}) or {}
    data = body.get("data")
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data).decode("utf-8", errors="replace")
    except Exception:
        return ""


def _extract_body(payload: dict) -> str:
    if not payload:
        return ""
    parts = payload.get("parts") or []
    if not parts:
        return _decode_part(payload)
    text = ""
    for p in parts:
        mime = p.get("mimeType", "")
        if mime == "text/plain":
            text += _decode_part(p)
        elif p.get("parts"):
            text += _extract_body(p)
    return text


def _is_relevant(headers: dict, snippet: str, body: str) -> tuple[bool, str]:
    """Return (is_relevant, reason)."""
    text = f"{headers.get('subject','')} {snippet} {body[:2000]}"
    if RELEVANCE_KEYWORDS.search(text):
        return True, "keyword_match"
    # could also check From: against known outreach contacts (Kumarappan, NielsRogge, etc.)
    # for now keep simple: keyword match only
    return False, "no_keyword"


def _insert_bounty(conn, msg_id: str, headers: dict, snippet: str, body: str, thread_id: str) -> str | None:
    title = f"Reply draft: {headers.get('subject', '(no subject)')[:120]}"
    from_field = headers.get("from", "unknown")
    description = (
        f"Inbound email reply · auto-discovered via gmail_inbound_monitor.\n"
        f"From: {from_field}\n"
        f"Subject: {headers.get('subject', '')}\n"
        f"Date: {headers.get('date', '')}\n"
        f"Gmail thread: {thread_id}\n"
        f"Gmail msg: {msg_id}\n\n"
        f"Body excerpt:\n{body[:2000]}\n\n"
        f"task: nautilus-prime-001 · generate personalized reply draft (anchors_outreach_quality gate) · "
        f"save to Gmail drafts API (gmail.compose scope) · human clicks send."
    )
    metadata = {
        "gmail_msg_id": msg_id,
        "gmail_thread_id": thread_id,
        "from": from_field,
        "subject": headers.get("subject", ""),
        "snippet": snippet[:300],
        "discovery_ts": datetime.now(timezone.utc).isoformat(),
    }
    bounty_id = f"outreach-reply-{msg_id[:32]}"
    try:
        conn.execute(
            """
            INSERT INTO platform_bounties (
                bounty_id, title, description, reward_nau,
                task_type, status, posted_by,
                channel, source, asset_path, assigned_to,
                metadata, posted_at
            ) VALUES (
                %s, %s, %s, 40,
                'outreach-reply-draft', 'open', 'compass-gmail-inbound-cron',
                'email', 'compass-outreach-gmail-inbound', 'inline-text', 'nautilus-prime-001',
                %s, NOW()
            )
            ON CONFLICT (bounty_id) DO NOTHING
            """,
            (bounty_id, title, description, json.dumps(metadata)),
        )
        return bounty_id
    except Exception as e:
        sys.stderr.write(f"INSERT fail {msg_id}: {e!r}\n")
        return None


def main() -> int:
    creds = _load_creds()
    if not creds:
        return 1
    svc = build("gmail", "v1", credentials=creds, cache_discovery=False)

    state = _load_state()
    seen = set(state.get("seen_msg_ids", []))
    dispatched = 0
    skipped_seen = 0
    skipped_irrelevant = 0
    errors = 0

    try:
        conn = psycopg.connect(DSN, autocommit=True)
    except Exception as e:
        sys.stderr.write(f"PG connect fail: {e!r}\n")
        return 1

    try:
        query = f"in:inbox is:unread newer_than:{LOOKBACK_DAYS}d"
        resp = svc.users().messages().list(userId="me", q=query, maxResults=50).execute()
        messages = resp.get("messages", [])
        for m in messages:
            if dispatched >= MAX_BOUNTIES_PER_RUN:
                break
            msg_id = m["id"]
            if msg_id in seen:
                skipped_seen += 1
                continue
            try:
                msg = svc.users().messages().get(
                    userId="me", id=msg_id, format="full"
                ).execute()
            except Exception as e:
                sys.stderr.write(f"get msg fail {msg_id}: {e!r}\n")
                errors += 1
                continue
            payload = msg.get("payload", {}) or {}
            headers_list = payload.get("headers", []) or []
            headers = {h["name"].lower(): h["value"] for h in headers_list if "name" in h}
            snippet = msg.get("snippet", "")
            thread_id = msg.get("threadId", "")
            body = _extract_body(payload)

            relevant, reason = _is_relevant(headers, snippet, body)
            if not relevant:
                skipped_irrelevant += 1
                seen.add(msg_id)  # mark seen · skip next time
                continue

            bounty_id = _insert_bounty(conn, msg_id, headers, snippet, body, thread_id)
            if bounty_id:
                seen.add(msg_id)
                dispatched += 1
                print(f"dispatched · {bounty_id} · from={headers.get('from','?')[:60]}")
            else:
                errors += 1
    finally:
        conn.close()

    state["seen_msg_ids"] = sorted(seen)
    state["dispatched_count"] = int(state.get("dispatched_count", 0)) + dispatched
    state["last_run_ts"] = int(time.time())
    _save_state(state)

    print(
        f"{datetime.now().isoformat(timespec='seconds')} · "
        f"dispatched={dispatched} skipped_seen={skipped_seen} "
        f"skipped_irrelevant={skipped_irrelevant} errors={errors} "
        f"total_dispatched={state['dispatched_count']}"
    )
    return 0 if errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
