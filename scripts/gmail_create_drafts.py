"""Create Gmail drafts from paper/promo/outreach_emails_2026-05-08.md.

Hard rule: drafts only. Scope is gmail.compose -- we cannot send.
The user reviews each draft in the Gmail UI, fills in the recipient
where the source MD has [TODO: ...] placeholders, and clicks Send.

Usage:
    python scripts/gmail_create_drafts.py [--dry-run] [--source path/to/md]

Default source: paper/promo/outreach_emails_2026-05-08.md
Default token:  ~/.gmail/token.json
"""
from __future__ import annotations

import argparse
import base64
import re
import sys
from email.mime.text import MIMEText
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

GMAIL_DIR = Path.home() / ".gmail"
TOKEN = GMAIL_DIR / "token.json"
DEFAULT_SOURCE = Path(__file__).resolve().parent.parent / "paper" / "promo" / "outreach_emails_2026-05-08.md"

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]

# section delimiters in the source MD: lines starting with "## N · ..."
SECTION_RE = re.compile(r"^## (\d+) · (.+)$", re.MULTILINE)
TO_RE = re.compile(r"^\*\*To:\*\*\s*(.+?)$", re.MULTILINE)
SUBJECT_RE = re.compile(r"^\*\*Subject:\*\*\s*(.+?)$", re.MULTILINE)


def parse_emails(text: str) -> list[dict]:
    """Split MD into per-email dicts: number, target, to, subject, body."""
    matches = list(SECTION_RE.finditer(text))
    out = []
    for i, m in enumerate(matches):
        num = m.group(1)
        target = m.group(2).strip()
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        block = text[start:end]

        to_m = TO_RE.search(block)
        subj_m = SUBJECT_RE.search(block)
        if not subj_m:
            continue

        to_raw = to_m.group(1).strip() if to_m else ""
        # if To: is purely a [TODO: ...] placeholder, leave empty so user fills in Gmail UI
        if to_raw.startswith("[TODO"):
            to_clean = ""
        else:
            # strip trailing " · [TODO: ...]" notes
            to_clean = re.sub(r"\s*·\s*\[TODO[^\]]*\]\s*$", "", to_raw).strip()

        subject = subj_m.group(1).strip()

        # body = everything after the Subject line, up to a trailing "---" line
        body_start = subj_m.end()
        body = block[body_start:].lstrip("\n")
        # trim trailing horizontal rule
        body = re.sub(r"\n---\s*$", "", body).rstrip() + "\n"

        out.append({
            "number": num,
            "target": target,
            "to": to_clean,
            "subject": subject,
            "body": body,
        })
    return out


def load_creds() -> Credentials:
    if not TOKEN.exists():
        print(f"missing token: {TOKEN}", file=sys.stderr)
        print("run: python scripts/gmail_oauth_init.py", file=sys.stderr)
        sys.exit(1)
    creds = Credentials.from_authorized_user_file(str(TOKEN), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        TOKEN.write_text(creds.to_json(), encoding="utf-8")
    if not creds.valid:
        print("invalid creds; re-run gmail_oauth_init.py", file=sys.stderr)
        sys.exit(1)
    # belt-and-suspenders: refuse anything that grants send
    granted = set(creds.scopes or [])
    if any("gmail.send" in s or "gmail.modify" in s or "https://mail.google.com/" in s for s in granted):
        print(f"refusing to run: token has send-capable scope: {granted}", file=sys.stderr)
        sys.exit(2)
    return creds


def make_raw(to: str, subject: str, body: str) -> str:
    msg = MIMEText(body, _charset="utf-8")
    if to:
        msg["To"] = to
    msg["Subject"] = subject
    return base64.urlsafe_b64encode(msg.as_bytes()).decode("ascii")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default=str(DEFAULT_SOURCE))
    ap.add_argument("--dry-run", action="store_true", help="parse + print, do not call Gmail API")
    args = ap.parse_args()

    src = Path(args.source)
    if not src.exists():
        print(f"missing source: {src}", file=sys.stderr)
        return 1

    text = src.read_text(encoding="utf-8")
    emails = parse_emails(text)
    print(f"parsed {len(emails)} email blocks from {src.name}")

    if args.dry_run:
        for e in emails:
            print(f"  [{e['number']}] {e['target']}")
            print(f"      To:      {e['to'] or '(empty - fill in Gmail UI)'}")
            print(f"      Subject: {e['subject']}")
            print(f"      Body:    {len(e['body'].splitlines())} lines, {len(e['body'])} chars")
        return 0

    creds = load_creds()
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    created = []
    for e in emails:
        raw = make_raw(e["to"], e["subject"], e["body"])
        draft = service.users().drafts().create(
            userId="me",
            body={"message": {"raw": raw}},
        ).execute()
        draft_id = draft.get("id")
        msg_id = (draft.get("message") or {}).get("id")
        created.append((e["number"], e["target"], draft_id, msg_id))
        print(f"  draft created: [{e['number']}] {e['target']:<30}  id={draft_id}")

    print(f"\n{len(created)} drafts in Gmail · open https://mail.google.com/mail/u/0/#drafts to review")
    print("for [TODO]-address rows, fill the recipient before sending.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
