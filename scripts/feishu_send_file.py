"""Send a file to a Feishu (Lark) chat via the open-platform IM API.

Reuses the tenant app credentials from ~/.claude/.cache/.fde_api_secrets.env
(FEISHU_APP_ID / FEISHU_APP_SECRET). Two-step: upload via /im/v1/files
(multipart), then send msg_type=file into the chat.

Usage:
    python scripts/feishu_send_file.py chats
    python scripts/feishu_send_file.py send --chat oc_xxx --path file.pptx
"""
from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.request
import uuid

API = "https://open.feishu.cn/open-apis"
SECRETS = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")


def _env() -> tuple[str, str]:
    vals = {}
    for line in open(SECRETS, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            vals[k.strip()] = v.strip().strip('"').strip("'")
    app_id = vals.get("FEISHU_APP_ID") or vals.get("LARK_APP_ID")
    secret = vals.get("FEISHU_APP_SECRET") or vals.get("LARK_APP_SECRET")
    if not app_id or not secret:
        sys.exit("[err] FEISHU_APP_ID/SECRET 未设")
    return app_id, secret


def token() -> str:
    app_id, secret = _env()
    req = urllib.request.Request(
        f"{API}/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": secret}).encode(),
        headers={"Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=20).read())
    if out.get("code") != 0:
        sys.exit(f"[err] token: {out.get('code')} {out.get('msg')}")
    return out["tenant_access_token"]


def chats(tok: str) -> None:
    req = urllib.request.Request(f"{API}/im/v1/chats?page_size=50",
                                 headers={"Authorization": f"Bearer {tok}"})
    out = json.loads(urllib.request.urlopen(req, timeout=20).read())
    for c in (out.get("data", {}).get("items") or []):
        print(c.get("chat_id"), "|", c.get("name") or "(p2p)")


def upload_file(tok: str, path: str) -> str:
    name = os.path.basename(path)
    mime = mimetypes.guess_type(path)[0] or "application/octet-stream"
    data = open(path, "rb").read()
    boundary = uuid.uuid4().hex
    parts = []
    for field, val in (("file_type", "stream"), ("file_name", name)):
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data;"
            f' name="{field}"\r\n\r\n{val}\r\n'.encode())
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\";"
        f" filename=\"{name}\"\r\nContent-Type: {mime}\r\n\r\n".encode()
        + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    req = urllib.request.Request(
        f"{API}/im/v1/files",
        data=body,
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    out = json.loads(urllib.request.urlopen(req, timeout=60).read())
    if out.get("code") != 0:
        sys.exit(f"[err] upload: {out.get('code')} {out.get('msg')}")
    return out["data"]["file_key"]


def send(tok: str, chat_id: str, path: str, note: str = "") -> None:
    file_key = upload_file(tok, path)
    msg = {"receive_id": chat_id,
           "msg_type": "file",
           "content": json.dumps({"file_key": file_key})}
    req = urllib.request.Request(
        f"{API}/im/v1/messages?receive_id_type=chat_id",
        data=json.dumps(msg).encode(),
        headers={"Authorization": f"Bearer {tok}",
                 "Content-Type": "application/json"})
    out = json.loads(urllib.request.urlopen(req, timeout=20).read())
    if out.get("code") != 0:
        sys.exit(f"[err] send: {out.get('code')} {out.get('msg')}")
    print(f"sent {path} → {chat_id} · message_id={out['data']['message_id']}")
    if note:
        req = urllib.request.Request(
            f"{API}/im/v1/messages?receive_id_type=chat_id",
            data=json.dumps({"receive_id": chat_id, "msg_type": "text",
                             "content": json.dumps({"text": note})}).encode(),
            headers={"Authorization": f"Bearer {tok}",
                     "Content-Type": "application/json"})
        json.loads(urllib.request.urlopen(req, timeout=20).read())
        print("note sent")


def main() -> None:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("chats")
    p = sub.add_parser("send")
    p.add_argument("--chat", required=True)
    p.add_argument("--path", required=True)
    p.add_argument("--note", default="")
    a = ap.parse_args()
    tok = token()
    if a.cmd == "chats":
        chats(tok)
    else:
        send(tok, a.chat, a.path, a.note)


if __name__ == "__main__":
    main()
