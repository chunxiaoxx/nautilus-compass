#!/usr/bin/env python3
"""主链活性巡检 · Liveness Check V1(2026-10-14)
8 锚(LIVENESS_RUNBOOK_V1)+收款单跟踪+信箱积压计数。
全绿→journal 一行;有红→org_mailbox 函(to=platform,4h 去重防噪音)。
systemd timer 每 30min 调用(liveness-check.timer)。
"""
import json, os, sqlite3, sys, urllib.request
from datetime import datetime

sys.path.insert(0, "/home/ubuntu/nautilus-mvp/phase3/backend")
STATE_DB = "/home/ubuntu/nautilus-mvp/phase3/backend/ops/.liveness_state.db"
PAY_SID = "1caff8497a95444d"
BASE = "https://www.nautilus.social"
DEDUP_HOURS = 4

def fetch(url, timeout=12):
    req = urllib.request.Request(url, headers={"User-Agent": "nautilus-liveness/1.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def check(name, fn):
    try:
        ok, detail = fn()
        return (name, ok, detail)
    except Exception as e:
        return (name, False, f"EXC {type(e).__name__}: {str(e)[:80]}")

def c_bench():
    s, b = fetch("https://bench.nautilus.social")
    ok = s == 200 and "免费榜单收录".encode() in b and b"nautilus-judge-action" in b
    return ok, f"{s} {len(b)}B"

def c_submit():
    s, b = fetch(BASE + "/submit/")
    return (s == 200 and len(b) > 10000), f"{s} {len(b)}B(794=SPA兜底死)"

def c_judge_status():
    try:
        s, b = fetch(BASE + "/api/judge_status?id=liveness-probe")
        return (s in (200, 404)), f"{s}(非502即活)"
    except urllib.error.HTTPError as e:
        return (e.code in (200, 404)), f"{e.code}(非502即活)"

def c_card():
    s, b = fetch("https://org.nautilus.social/L1_READOUT_CARD_mini_swe_agent_20261006.md")
    return (s == 200 and len(b) == 3027), f"{s} {len(b)}B"

def c_criteria():
    s, b = fetch(BASE + "/criteria/")
    return (s == 200 and b"L1_READOUT" in b), f"{s} {len(b)}B"

def c_intake():
    req = urllib.request.Request(BASE + "/api/platform/org/assay/submissions", method="GET")
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status == 405, f"{r.status}"
    except urllib.error.HTTPError as e:
        return e.code == 405, f"{e.code}"

def c_pay():
    s, b = fetch(f"{BASE}/api/platform/org/assay/submissions/{PAY_SID}")
    if s != 200:
        return False, f"pay单查询 {s}"
    d = json.loads(b)
    st = d.get("status") or (d.get("data") or {}).get("status")
    prev = _state_get("pay_status")
    _state_set("pay_status", st or "")
    if prev and st != prev:
        return False, f"PAY-CHANGE {prev}->{st}(可能已付款!即查回执)"
    return True, f"pay={st}"

def c_mailbox():
    s, b = fetch("https://nautilus.social/api/platform/org/mailbox?to=platform&unread=1&limit=50", timeout=15)
    d = json.loads(b)
    items = d if isinstance(d, list) else d.get("items") or d.get("data") or []
    n = len(items)
    return (n <= 5), f"unread={n}(>5=积压)"

# 组织成员活性锚(10/18 用户批):72h 无实质函 = 红。
# 教训锚:soul 静默 8 天无人知——consumer 心跳(步0回执)≠活性,故排除心跳函只认实质信号。
MEMBERS = ["compass", "flywheel", "v5", "soul", "kairos", "zenmind"]

def _member_engine():
    from sqlalchemy import create_engine
    return create_engine(os.environ.get("DATABASE_URL", "postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production"))

def c_members():
    from sqlalchemy import text
    stale = []
    with _member_engine().connect() as cx:
        for m in MEMBERS:
            hours = cx.execute(text(
                "SELECT extract(epoch FROM (now() - max(created_at)))/3600 FROM org_mailbox "
                "WHERE from_agent=:m AND title NOT LIKE '%步0回执%'"), {"m": m}).scalar()
            if hours is None:
                stale.append(f"{m}:无实质函记录")
            elif float(hours) > 72:
                stale.append(f"{m}:{float(hours):.0f}h无实质函")
    return (len(stale) == 0), ("; ".join(stale) if stale else f"{len(MEMBERS)}成员全活(72h内有实质函)")

def c_soul_daemon():
    """soul 主循环活性:6h 内有 Finished 轮为绿(班表 15min/轮=应 24 轮)。
    判活必查 journalctl 主循环,不信信箱心跳(2026-10-18 soul 复盘)。"""
    import subprocess
    try:
        out = subprocess.run(
            ["journalctl", "-u", "nautilus-soul.service", "--since", "-6 hours", "--no-pager"],
            capture_output=True, text=True, timeout=20).stdout
        n = out.count("Finished Autonomous Nautilus Soul")
        return (n > 0), f"6h绿轮={n}(0=主循环死)"
    except Exception as e:
        return False, f"探针异常:{e}"

def _state_get(k):
    try:
        c = sqlite3.connect(STATE_DB)
        r = c.execute("SELECT v FROM kv WHERE k=?", (k,)).fetchone()
        c.close()
        return r[0] if r else None
    except Exception:
        return None

def _state_set(k, v):
    c = sqlite3.connect(STATE_DB)
    c.execute("CREATE TABLE IF NOT EXISTS kv (k TEXT PRIMARY KEY, v TEXT, t TEXT DEFAULT (datetime('now')))")
    c.execute("INSERT INTO kv (k,v) VALUES (?,?) ON CONFLICT(k) DO UPDATE SET v=excluded.v, t=datetime('now')", (k, v))
    c.commit(); c.close()

def _recently_alerted(key):
    try:
        c = sqlite3.connect(STATE_DB)
        r = c.execute("SELECT t FROM kv WHERE k=?", (key,)).fetchone()
        c.close()
        if not r: return False
        t = datetime.fromisoformat(r[0])
        return (datetime.now() - t).total_seconds() < DEDUP_HOURS * 3600
    except Exception:
        return False

def _mark_alerted(key):
    _state_set(key, datetime.now().isoformat())

def send_red_mail(reds, extras):
    title = f"[Liveness RED] {len(reds)}锚红 " + " ".join(r[0] for r in reds)
    lines = [f"- {n}: {d}" for n, ok, d in reds]
    if extras: lines.append(""); lines.append("附报: " + "; ".join(extras))
    body = "云端 liveness-check.timer 自动巡检红灯(去重 {0}h):\n\n".format(DEDUP_HOURS) + "\n".join(lines) + \
        "\n\n巡检时间: " + datetime.now().strftime("%F %T") + "\nrunbook: docs/LIVENESS_RUNBOOK_V1"
    import psycopg2
    from sqlalchemy import create_engine, text
    eng = create_engine(os.environ.get("DATABASE_URL", "postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production"))
    trace = f"liveness-{datetime.now():%Y%m%d%H%M%S}"
    with eng.begin() as cx:
        cx.execute(text("INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline) VALUES (:t,'platform','platform',:ti,:b, now()+interval '2 hours')"),
                   {"t": trace, "ti": title, "b": body})
    print(f"RED mail sent: {title}")

def main():
    results = [
        check("bench", c_bench), check("submit", c_submit), check("judge_status", c_judge_status),
        check("readout_card", c_card), check("criteria", c_criteria), check("intake_route", c_intake),
        check("pay_order", c_pay), check("mailbox_backlog", c_mailbox),
        check("members_active", c_members), check("soul_daemon", c_soul_daemon),
    ]
    reds = [(n, ok, d) for n, ok, d in results if not ok]
    extras = []
    s, b = fetch(f"{BASE}/api/platform/org/assay/submissions/{PAY_SID}")
    try:
        d = json.loads(b); st = d.get("status") or ""
        if st and st != "intake_validated": extras.append(f"pay单状态={st}")
    except Exception: pass
    stamp = datetime.now().strftime("%F %T")
    if reds:
        print(f"[{stamp}] RED x{len(reds)}: " + "; ".join(f"{n}({d})" for n, _, d in reds))
        key = "alert_" + "_".join(sorted(n for n, _, _ in reds))
        if not _recently_alerted(key):
            send_red_mail(reds, extras)
            _mark_alerted(key)
        else:
            print("dedup: 红灯函 4h 内已发,跳过")
    else:
        print(f"[{stamp}] ALL GREEN " + "; ".join(f"{n}={d}" for n, _, d in results))

if __name__ == "__main__":
    main()
