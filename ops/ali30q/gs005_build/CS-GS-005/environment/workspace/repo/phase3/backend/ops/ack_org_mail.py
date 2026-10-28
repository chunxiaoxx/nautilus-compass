# -*- coding: utf-8 -*-
"""组织函 ack 器(平台身份)——回函后必置 ack_at 纪律的执行件(欠函病 9/24 根治配套)。

凭据同 send_org_mail.py(backend/.env PLATFORM_ORG_AUTH_KEY)。
用法:python ops/ack_org_mail.py <id> [note]
"""
from __future__ import annotations

import sys
from pathlib import Path

import requests

BASE = "https://www.nautilus.social"
ENV = Path(__file__).resolve().parents[1] / ".env"


def _key() -> str:
    for ln in ENV.read_text(encoding="utf-8").splitlines():
        if ln.startswith("PLATFORM_ORG_AUTH_KEY="):
            return ln.split("=", 1)[1].strip()
    raise SystemExit("PLATFORM_ORG_AUTH_KEY missing in .env")


def ack(mid: int, note: str = "") -> dict:
    r = requests.post(f"{BASE}/api/platform/org/mailbox/{mid}/ack",
                      json={"note": note}, headers={"X-API-Key": _key()}, timeout=30)
    if r.status_code >= 400:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


if __name__ == "__main__":
    _id = int(sys.argv[1])
    _note = sys.argv[2] if len(sys.argv) > 2 else ""
    print(ack(_id, _note))
