"""One-time OAuth flow for Gmail drafts.

Reads client_secret.json, opens browser for consent, saves token.json.
Scope is gmail.compose ONLY -- this lets us read/write/delete drafts
but does NOT permit users.messages.send. The send action stays a
human-in-the-loop click in the Gmail UI.

Run once after Google Cloud Console setup:
    python scripts/gmail_oauth_init.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

GMAIL_DIR = Path.home() / ".gmail"
CLIENT_SECRET = GMAIL_DIR / "client_secret.json"
TOKEN = GMAIL_DIR / "token.json"

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def main() -> int:
    if not CLIENT_SECRET.exists():
        print(f"missing: {CLIENT_SECRET}", file=sys.stderr)
        print("download OAuth Desktop client JSON from Google Cloud Console "
              "and place it at the path above.", file=sys.stderr)
        return 1

    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    print("starting local OAuth server on a free port...")
    print("if a browser does NOT open automatically, copy the URL below into one")
    print("(make sure you are signed into the test-user Gmail account first):")
    print()
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        open_browser=True,
        authorization_prompt_message="OPEN THIS URL: {url}",
    )

    GMAIL_DIR.mkdir(parents=True, exist_ok=True)
    TOKEN.write_text(creds.to_json(), encoding="utf-8")
    print(f"token saved: {TOKEN}")

    payload = json.loads(creds.to_json())
    print(f"scopes: {payload.get('scopes')}")
    print(f"refresh_token present: {bool(payload.get('refresh_token'))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
