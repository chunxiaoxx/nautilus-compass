#!/usr/bin/env python3
"""Conductor 常驻入口 v1(2026-06-22)· 第一个常驻自治 agent 的 heartbeat。

surfacing-only(v1·反 drift:不 auto-trigger·只读真信号+写 pulse+alert)。
身份注册(V5 钱包骨架)= 🔴红线 gated·进程先活·身份后补。

每 cycle:读真 loop 信号(DB settled/fuel + daemon/backend 健康)+ 维护的齿轮态
→ conductor_core 大脑(active_gear/stalls/actions)→ 写 pulse 文件(下个 session 起手即读
= 连续性·治 session 间失忆)+ alert 停滞/逾期。
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services.conductor_runner import make_snapshot_fn, make_pulse_fn, run_conductor_cycle  # noqa: E402

STATE_DIR = os.environ.get("CONDUCTOR_DIR", "/home/ubuntu/conductor")
GEARS_FILE = os.path.join(STATE_DIR, "gears.json")
PULSE_FILE = os.path.join(STATE_DIR, "last_pulse.json")
ALERT_LOG = os.path.join(STATE_DIR, "alerts.log")
FUEL_PATH = os.environ.get("FUEL_PATH", os.path.join(STATE_DIR, "fuel.jsonl"))


def _psql(q: str) -> str:
    try:
        r = subprocess.run(["sudo", "-u", "postgres", "psql", "nautilus_production", "-tAc", q],
                           capture_output=True, text=True, timeout=15)
        return r.stdout.strip()
    except Exception:
        return ""


def _port_open(port: int) -> bool:
    try:
        r = subprocess.run(["ss", "-tlnH", f"sport = :{port}"], capture_output=True, text=True, timeout=5)
        return bool(r.stdout.strip())
    except Exception:
        return False


def _http_ok(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False


def gears_reader() -> dict:
    """维护的收敛态(慢变·当前真实·可手动/未来 conductor 更新)。"""
    if os.path.exists(GEARS_FILE):
        try:
            return json.load(open(GEARS_FILE, encoding="utf-8"))
        except Exception:
            pass
    # 当前真实态(6/22):②link/③verdict LIVE·①fuel building·⑤memory/⑦distill pending
    return {"fuel": "building", "link": "done", "verdict": "done",
            "memory": "pending", "distill": "pending"}


def fuel_summary() -> dict:
    """读 V5 ALE records → A 类率(替人盯 Q3 风险)。文件缺 = 还没产(records_seen=0)。

    FUEL_RECORDS_PATH 指向 V5 6-key records jsonl(同步到本盒的约定路径)。
    复用 services.distill_mint_runner.fuel_rate(已测·不重写分拣)。fail-soft。
    """
    path = os.environ.get("FUEL_RECORDS_PATH", FUEL_PATH)
    if not os.path.exists(path):
        return {"records_seen": 0, "a_bucket": 0, "a_rate": 0.0, "enough": False}
    try:
        from services.distill_mint_runner import fuel_rate
        # 逐行容错:V5 非原子写时 race 读到半截最后一行 → 跳过该行·不让整体计数归 0
        # (compass 实测 firing-killer 担忧·防间歇漏数)。
        recs = []
        for ln in open(path, encoding="utf-8"):
            ln = ln.strip()
            if not ln:
                continue
            try:
                recs.append(json.loads(ln))
            except Exception:
                continue
        r = fuel_rate(recs, min_n=int(os.environ.get("DISTILL_MIN_N", "20")))
        return {"records_seen": r["total"], "a_bucket": r["a_bucket"],
                "a_rate": r["a_rate"], "enough": r["enough_for_poc"]}
    except Exception:
        return {"records_seen": 0, "a_bucket": 0, "a_rate": 0.0, "enough": False}


def loop_reader() -> dict:
    settled = _psql("SELECT count(*) FROM fde_dispatch WHERE status='settled'")
    fuel = fuel_summary()
    return {
        "settled": int(settled) if settled.isdigit() else None,
        "fuel_count": fuel["a_bucket"],   # A 类数(非裸行数)= 真燃料库存
        "fuel": fuel,
        "fuel_threshold": int(os.environ.get("FUEL_THRESHOLD", "50")),
        "daemon_8001_ok": _port_open(8001),
        "backend_8000_ok": _http_ok("http://localhost:8000/api/platform/fde/capability/__hb__"),
        "ready_steps": [],   # v1 surfacing-only·不 auto-trigger(反 drift)
    }


def main() -> int:
    os.makedirs(STATE_DIR, exist_ok=True)
    snapshot_fn = make_snapshot_fn(gears_reader, loop_reader, contracts_reader=lambda: [])

    def derive_blockers(gears, loop):
        """持续推动力本质:始终知道当前真瓶颈(确定性推导·非判断)。"""
        from services.conductor_core import fuel_poc_status
        b = []
        if gears.get("fuel") != "done":
            f = loop.get("fuel", {})
            fs = fuel_poc_status(f.get("a_bucket", 0), f.get("records_seen", 0),
                                 min_n=int(os.environ.get("DISTILL_MIN_N", "20")))
            if fs["blocker"]:
                b.append(fs["blocker"])   # 精确瓶颈:awaiting_records / short(N/min_n)
        if not loop.get("daemon_8001_ok"):
            b.append("producer daemon :8001 DOWN")
        if not loop.get("backend_8000_ok"):
            b.append("backend :8000 unhealthy")
        if gears.get("memory") != "done":
            b.append("memory: split-brain 未沉淀·gated on compass ⑤")
        return b

    def memory_writer(pulse):
        pulse = dict(pulse)
        pulse["ts"] = datetime.now(timezone.utc).isoformat()
        loop = loop_reader()
        pulse["loop"] = loop
        pulse["blockers"] = derive_blockers(gears_reader(), loop)
        json.dump(pulse, open(PULSE_FILE, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    def alert_fn(msg):
        with open(ALERT_LOG, "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.now(timezone.utc).isoformat()} {msg}\n")

    pulse_fn = make_pulse_fn(memory_writer, trigger_fn=lambda step: None, alert_fn=alert_fn)
    res = run_conductor_cycle(snapshot_fn, pulse_fn)
    print(f"[conductor] cycle ok={res['ok']} pulse={PULSE_FILE}")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
