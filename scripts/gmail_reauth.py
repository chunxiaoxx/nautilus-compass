# -*- coding: utf-8 -*-
"""One-time re-auth for ~/.gmail-mcp (shared by gmail MCP + flywheel sender).

Root cause of invalid_grant: refresh_token expired/revoked (testing-mode OAuth
tokens die after 7 days). Re-runs consent with full gmail scope and writes the
@gongrzhe/server-gmail-autoauth-mcp format back to ~/.gmail-mcp/credentials.json.

Run:  python scripts/gmail_reauth.py
      (browser opens; make sure you are signed in as chunxiaoxx@gmail.com)

NOTE: if the OAuth consent screen is still "Testing" in Google Cloud Console,
the new token dies again in 7 days. Publish it ("PUBLISH APP") for long-term use:
console.cloud.google.com -> APIs & Services -> OAuth consent screen.
"""
import json
import sys
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    sys.exit("missing dep: pip install google-auth-oauthlib")

DIR = Path.home() / ".gmail-mcp"
SCOPES = ["https://mail.google.com/"]


def main() -> int:
    sec = DIR / "client_secret.json"
    if not sec.exists():
        sys.exit(f"missing: {sec}")
    flow = InstalledAppFlow.from_client_secrets_file(str(sec), SCOPES)
    creds = flow.run_local_server(
        port=0,
        prompt="consent",
        open_browser=True,
        authorization_prompt_message="OPEN THIS URL (signed in as chunxiaoxx@gmail.com): {url}",
    )
    token = json.loads(creds.to_json())
    if not token.get("refresh_token"):
        sys.exit("no refresh_token returned (revoke the old grant at "
                 "myaccount.google.com/permissions first, then rerun)")
    payload = {
        "access_token": token["token"],
        "refresh_token": token["refresh_token"],
        "scope": " ".join(token["scopes"]),
        "token_type": "Bearer",
        "expiry_date": 0,
    }
    (DIR / "credentials.json").write_text(json.dumps(payload), encoding="utf-8")
    print(f"[ok] token saved: {DIR / 'credentials.json'}")
    print("[next] restart/reconnect the gmail MCP (or /mcp) so it picks up the new token")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
