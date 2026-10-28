# -*- coding: utf-8 -*-
"""通用组织投函器(平台身份)——9/21 起鉴权强制后平台自投函的唯一正门。

凭据:backend/.env 的 PLATFORM_ORG_AUTH_KEY(name=org-auth:platform,agent_id=9000002 哨兵位)。
deadline 一律动态 now+2h(SLA 纪律,禁手写绝对时间——三次失误教训)。
409=同 (to,trace) 已存在,幂等成功。

用法:python ops/send_org_mail.py <to> <trace> <title> <body-file> [--from platform]
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

DB_TZ = ZoneInfo("Asia/Shanghai")  # org_mailbox 各时间列的时钟(naive 存储,与 loop now_local 同钟)

BASE = "https://www.nautilus.social"
ENV = Path(__file__).resolve().parents[1] / ".env"


def _key() -> str:
    for ln in ENV.read_text(encoding="utf-8").splitlines():
        if ln.startswith("PLATFORM_ORG_AUTH_KEY="):
            return ln.split("=", 1)[1].strip()
    raise SystemExit("PLATFORM_ORG_AUTH_KEY missing in .env")


def send(to: str, trace: str, title: str, body: str, from_a: str = "platform",
         hours: float = 2) -> dict:
    r = requests.post(
        f"{BASE}/api/platform/org/mailbox",
        json={"from_agent": from_a, "to_agent": to, "trace_id": trace,
              "title": title[:200], "body": body, "task_meta": None, "meta": None,
              # deadline 钟=上海 naive。9/22 实证:utcnow 落库早 8h → 每函落地即"超期",
              # loop 30min 内必升级一轮(777/782/783 升级函时间戳早于原函=此病;豁免挡症状,此修病根)
              # hours 默认 2(SLA);深夜发函给 hours>2 免整夜空升级(值班窗照常升级)
              "deadline": (datetime.now(DB_TZ).replace(tzinfo=None)
                           + timedelta(hours=hours)).isoformat()},
        headers={"X-API-Key": _key()}, timeout=30)
    if r.status_code == 409:
        return {"idempotent": True, "resp": r.json()}
    if r.status_code >= 400:
        raise SystemExit(f"HTTP {r.status_code}: {r.text[:200]}")
    return r.json()


if __name__ == "__main__":
    _argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    _hours = 2.0
    _from = "platform"
    _rest = list(sys.argv[1:])
    for _k, _d in (("--hours", "_hours"), ("--from", "_from")):
        if _k in _rest:
            _i = _rest.index(_k)
            if _d == "_hours":
                _hours = float(_rest[_i + 1])
            else:
                _from = _rest[_i + 1]
            del _rest[_i:_i + 2]
    if len(_rest) < 4:
        raise SystemExit(__doc__)
    _to, _trace, _title, _bf = _rest[:4]
    print(send(_to, _trace, _title, Path(_bf).read_text(encoding="utf-8"),
               from_a=_from, hours=_hours))
