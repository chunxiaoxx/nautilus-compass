"""平台信箱客户端(X-API-Key 鉴权 · 2026-09-17 迁移,key 函 id 331)。

用法:
  python scripts/platform_mail.py send <to> <trace> <title> <body-file> [--deadline "YYYY-MM-DD HH:MM:SS"]
  python scripts/platform_mail.py check [--to compass | --from-agent flywheel]
  python scripts/platform_mail.py ack <id> [--note ...]

key 解析:环境变量 COMPASS_MAILKEY 优先 →
~/.claude/.cache/compass_platform_mailkey.env 兜底(永不入仓)。
from_agent 固定 compass(key 与框名绑定,不符=401;303 时代身份洞的闭合件)。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

BASE = "https://nautilus.social/api/platform/org/mailbox"
KEYFILE = Path.home() / ".claude" / ".cache" / "compass_platform_mailkey.env"


def _key() -> str | None:
    k = os.environ.get("COMPASS_MAILKEY")
    if k:
        return k.strip()
    if KEYFILE.is_file():
        for line in KEYFILE.read_text(encoding="utf-8").splitlines():
            if line.startswith(("X-API-KEY=", "COMPASS_MAILKEY=")):
                return line.split("=", 1)[1].strip()
    return None


def _req(url: str, payload: dict | None = None, method: str = "GET") -> dict:
    data = json.dumps(payload).encode() if payload is not None else None
    headers = {"Content-Type": "application/json"}
    key = _key()
    if key:
        headers["X-API-Key"] = key
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        return json.loads(urllib.request.urlopen(req).read())
    except urllib.error.HTTPError as e:
        return {"success": False, "http": e.code,
                "error": e.read().decode("utf-8", "replace")[:200]}


def cmd_send(a: argparse.Namespace) -> int:
    body = Path(a.body_file).read_text(encoding="utf-8")
    payload = {"from_agent": "compass", "to_agent": a.to, "trace_id": a.trace,
               "title": a.title, "body": body, "deadline": a.deadline}
    r = _req(BASE, payload, "POST")
    if r.get("success"):
        print(f"[OK] id {r.get('data', {}).get('id')} · to={a.to} · trace={a.trace}"
              f" · key={'✓' if _key() else '✗(宽限期内未带)'}")
        return 0
    print(f"[FAIL] {json.dumps(r, ensure_ascii=False)[:300]}")
    return 1


def cmd_check(a: argparse.Namespace) -> int:
    q = f"?to={a.to}" if a.to else f"?from-agent={a.from_agent}"
    r = _req(BASE + q)
    letters = r.get("data") or []
    for L in letters:
        print(f"--- id {L.get('id')} {L.get('from_agent')}→{L.get('to_agent')}"
              f" | {L.get('trace_id')}")
        print("   " + (L.get("body") or "")[:80].replace("\n", " ⏎ "))
    print(f"total: {len(letters)}")
    return 0


def cmd_ack(a: argparse.Namespace) -> int:
    r = _req(f"{BASE}/{a.id}/ack", {"note": a.note or ""}, "POST")
    print("[OK] ack" if r.get("success") else f"[FAIL] {json.dumps(r)[:200]}")
    return 0 if r.get("success") else 1


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("send")
    s.add_argument("to"); s.add_argument("trace"); s.add_argument("title")
    s.add_argument("body_file")
    s.add_argument("--deadline", required=True, help="必填字段(平台 API 约束)")
    s.set_defaults(fn=cmd_send)

    c = sub.add_parser("check")
    c.add_argument("--to", default="compass")
    c.add_argument("--from-agent", dest="from_agent")
    c.set_defaults(fn=cmd_check)

    k = sub.add_parser("ack")
    k.add_argument("id"); k.add_argument("--note")
    k.set_defaults(fn=cmd_ack)

    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
