#!/usr/bin/env python3
"""V7 monitor cron · platform-side bounty funnel health probe.

Drop-in script the platform can run every 30-60 min. Pure psycopg2 +
optional MCP TCP call to compass governance_audit · stdlib otherwise.

What it does (v0.2 path · governance only · no execution):

1. Read platform_bounties → classify funnel state:
   · orphan_open       (open >24h · no claimer)        ← agent matchmaking issue
   · stuck_claimed     (claimed >12h · no submit)      ← executor not delivering
   · stuck_submitted   (submitted >12h · no score)     ← scoring judge backlog
   · failed_24h        (failed in last 24h)            ← upstream asset/router bug
   · settle_rate_7d    (scored / posted in last 7d)    ← end-to-end health

2. Optional · call compass `governance_audit` MCP tool over TCP · pull
   recent red-drift / fake-closure session counts from cross-project memory.

3. Emit:
   · stdout · human-readable digest
   · stderr · colored alerts (cron-friendly · Mailto: gets these)
   · JSON file at /var/lib/v7-monitor/last_report.json
   · optional Telegram POST (when TG_BOT_TOKEN + TG_CHAT_ID env set)

Thresholds (env-overridable):
   V7_THRESH_ORPHAN     default 10  · orphans above = alert
   V7_THRESH_STUCK_CL   default 5   · stuck-claimed above = alert
   V7_THRESH_STUCK_SUB  default 20  · stuck-submitted above = alert
   V7_THRESH_FAILED     default 3   · failed/24h above = alert (asset/router)
   V7_THRESH_SETTLE     default 30  · settle-rate-7d below pct = alert

Install (platform side):

    sudo cp scripts/v7_monitor_cron.py /usr/local/bin/v7-monitor
    sudo chmod +x /usr/local/bin/v7-monitor
    sudo mkdir -p /var/lib/v7-monitor

    # cron: every 30 min
    echo '*/30 * * * * ubuntu /usr/local/bin/v7-monitor 2>&1 | logger -t v7-monitor' \\
       | sudo tee /etc/cron.d/v7-monitor

    # OR systemd timer:
    # /etc/systemd/system/v7-monitor.service + .timer  (see docs §9.4 TODO 7)

Per V7 v0.2 contract: V7 governs · does NOT execute or auto-correct. This
cron only reports + alerts. Acting on the alerts (re-routing orphans,
escalating to scoring judge, etc) stays platform-side per `不替 agent
决策`.
"""
from __future__ import annotations

import json
import os
import socket
import sys
import time
import urllib.request
from pathlib import Path

try:
    import psycopg2          # type: ignore
    import psycopg2.extras   # type: ignore
except ImportError:
    sys.stderr.write("ERROR: psycopg2 required · pip install psycopg2-binary\n")
    sys.exit(2)

PG_DSN = os.environ.get(
    "COMPASS_PG_DSN",
    "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production",
)
COMPASS_MCP_HOST = os.environ.get("COMPASS_MCP_HOST", "127.0.0.1")
COMPASS_MCP_PORT = int(os.environ.get("COMPASS_MCP_PORT", "0"))   # 0 = skip
COMPASS_MCP_TOKEN = os.environ.get("COMPASS_MCP_TOKEN", "")

REPORT_DIR = Path(os.environ.get("V7_REPORT_DIR", "/var/lib/v7-monitor"))
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID", "")

THRESH = {
    "orphan":      int(os.environ.get("V7_THRESH_ORPHAN", "10")),
    "stuck_cl":    int(os.environ.get("V7_THRESH_STUCK_CL", "5")),
    "stuck_sub":   int(os.environ.get("V7_THRESH_STUCK_SUB", "20")),
    "failed":      int(os.environ.get("V7_THRESH_FAILED", "3")),
    "settle_pct":  int(os.environ.get("V7_THRESH_SETTLE", "30")),
}


def query_funnel(conn) -> dict:
    """Pull bounty-funnel counts in one round-trip."""
    sql = """
    SELECT
      COUNT(*) FILTER (WHERE status='open'      AND posted_at    < NOW() - INTERVAL '24 hours')
        AS orphan_open_24h,
      COUNT(*) FILTER (WHERE status='claimed'   AND claimed_at   < NOW() - INTERVAL '12 hours')
        AS stuck_claimed_12h,
      COUNT(*) FILTER (WHERE status='submitted' AND submitted_at < NOW() - INTERVAL '12 hours')
        AS stuck_submitted_12h,
      COUNT(*) FILTER (WHERE status='failed'    AND posted_at    > NOW() - INTERVAL '24 hours')
        AS failed_24h,
      COUNT(*) FILTER (WHERE status='scored'    AND posted_at    > NOW() - INTERVAL '7 days')
        AS scored_7d,
      COUNT(*) FILTER (WHERE                       posted_at    > NOW() - INTERVAL '7 days')
        AS posted_7d,
      COUNT(*) FILTER (WHERE                       posted_at    > NOW() - INTERVAL '24 hours')
        AS posted_24h,
      COUNT(*) AS total
    FROM platform_bounties;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql)
        return dict(cur.fetchone())


def query_top_failures(conn, limit: int = 5) -> list:
    """Recent failed bounties · debug routing/asset issues."""
    sql = """
    SELECT bounty_id, posted_by, claimed_by, LEFT(result, 250) AS reason, posted_at
    FROM platform_bounties
    WHERE status='failed' AND posted_at > NOW() - INTERVAL '36 hours'
    ORDER BY posted_at DESC
    LIMIT %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]


def query_top_stuck_submitted(conn, limit: int = 5) -> list:
    """Submissions waiting longest for scoring."""
    sql = """
    SELECT bounty_id, claimed_by, LEFT(title, 60) AS title,
           EXTRACT(EPOCH FROM NOW() - submitted_at)/3600 AS hours_pending
    FROM platform_bounties
    WHERE status='submitted'
    ORDER BY submitted_at ASC
    LIMIT %s;
    """
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(sql, (limit,))
        return [dict(r) for r in cur.fetchall()]


def call_compass_governance_audit(days: int = 7) -> dict | None:
    """Best-effort · query compass MCP TCP for recent red-drift count.

    Skipped if COMPASS_MCP_PORT not set (which is most installs).
    """
    if not COMPASS_MCP_PORT:
        return None
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5)
        s.connect((COMPASS_MCP_HOST, COMPASS_MCP_PORT))
        # MCP initialize
        s.sendall(json.dumps({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"clientInfo": {"name": "v7-monitor"}},
        }).encode("utf-8") + b"\n")
        # token auth (if required)
        if COMPASS_MCP_TOKEN:
            s.sendall(json.dumps({
                "jsonrpc": "2.0", "id": 2, "method": "auth",
                "params": {"token": COMPASS_MCP_TOKEN},
            }).encode("utf-8") + b"\n")
        # call governance_audit
        s.sendall(json.dumps({
            "jsonrpc": "2.0", "id": 3, "method": "tools/call",
            "params": {"name": "governance_audit", "arguments": {"days": days}},
        }).encode("utf-8") + b"\n")
        # read until we see id=3 reply
        buf = b""
        deadline = time.time() + 10
        while time.time() < deadline:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            for line in buf.splitlines():
                try:
                    d = json.loads(line)
                    if d.get("id") == 3 and "result" in d:
                        s.close()
                        text = (d["result"].get("content") or [{}])[0].get("text", "")
                        return {"raw": text}
                except Exception:
                    continue
        s.close()
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
    return None


def render_digest(funnel: dict, fails: list, stuck_sub: list,
                   audit: dict | None, alerts: list[str]) -> str:
    lines: list[str] = []
    lines.append("V7 monitor · platform_bounties funnel health")
    lines.append(f"  generated_at: {time.strftime('%Y-%m-%d %H:%M:%SZ', time.gmtime())}")
    lines.append("")
    lines.append("  funnel")
    lines.append(f"    posted_24h:     {funnel['posted_24h']}")
    lines.append(f"    posted_7d:      {funnel['posted_7d']}")
    lines.append(f"    scored_7d:      {funnel['scored_7d']}")
    pct = (funnel['scored_7d'] * 100 // max(funnel['posted_7d'], 1))
    lines.append(f"    settle_rate_7d: {pct}%")
    lines.append(f"    total:          {funnel['total']}")
    lines.append("")
    lines.append("  stuck states")
    lines.append(f"    orphan_open_24h:     {funnel['orphan_open_24h']}  (threshold {THRESH['orphan']})")
    lines.append(f"    stuck_claimed_12h:   {funnel['stuck_claimed_12h']}  (threshold {THRESH['stuck_cl']})")
    lines.append(f"    stuck_submitted_12h: {funnel['stuck_submitted_12h']}  (threshold {THRESH['stuck_sub']})")
    lines.append(f"    failed_24h:          {funnel['failed_24h']}  (threshold {THRESH['failed']})")
    if alerts:
        lines.append("")
        lines.append("  ALERTS")
        for a in alerts:
            lines.append(f"    🔴 {a}")
    if fails:
        lines.append("")
        lines.append("  recent failed (top 5)")
        for f in fails[:5]:
            lines.append(f"    · {f['bounty_id'][:30]:<30} by={f['claimed_by'] or '-':<22} reason={(f['reason'] or '')[:80]}")
    if stuck_sub:
        lines.append("")
        lines.append("  oldest stuck-submitted (top 5)")
        for s in stuck_sub[:5]:
            lines.append(f"    · {s['bounty_id'][:30]:<30} {s['hours_pending']:.1f}h · by={s['claimed_by'] or '-':<22} {s['title'][:50]}")
    if audit:
        lines.append("")
        lines.append("  compass governance_audit")
        if "error" in audit:
            lines.append(f"    (skipped: {audit['error']})")
        else:
            for ln in (audit.get("raw") or "").splitlines()[:6]:
                lines.append(f"    {ln}")
    return "\n".join(lines)


def telegram_post(text: str) -> None:
    if not (TG_BOT_TOKEN and TG_CHAT_ID):
        return
    try:
        url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
        body = json.dumps({
            "chat_id": TG_CHAT_ID,
            "text": "```\n" + text[:3500] + "\n```",
            "parse_mode": "Markdown",
        }).encode("utf-8")
        req = urllib.request.Request(url, data=body,
                                      headers={"Content-Type": "application/json"})
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        sys.stderr.write(f"telegram post failed: {e}\n")


def main() -> int:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    try:
        conn = psycopg2.connect(PG_DSN)
    except Exception as e:
        sys.stderr.write(f"PG connect failed: {e}\n")
        return 1

    try:
        funnel = query_funnel(conn)
        fails = query_top_failures(conn) if funnel["failed_24h"] else []
        stuck_sub = (query_top_stuck_submitted(conn)
                     if funnel["stuck_submitted_12h"] else [])
    finally:
        conn.close()

    audit = call_compass_governance_audit() if COMPASS_MCP_PORT else None

    # threshold checks → alerts
    alerts: list[str] = []
    if funnel["orphan_open_24h"] > THRESH["orphan"]:
        alerts.append(f"orphan_open_24h={funnel['orphan_open_24h']} > {THRESH['orphan']} · matchmaking lag · no agent claims")
    if funnel["stuck_claimed_12h"] > THRESH["stuck_cl"]:
        alerts.append(f"stuck_claimed_12h={funnel['stuck_claimed_12h']} > {THRESH['stuck_cl']} · executors not delivering · check capability assignment")
    if funnel["stuck_submitted_12h"] > THRESH["stuck_sub"]:
        alerts.append(f"stuck_submitted_12h={funnel['stuck_submitted_12h']} > {THRESH['stuck_sub']} · scoring queue backlog · ping kairos/scoring agents")
    if funnel["failed_24h"] > THRESH["failed"]:
        alerts.append(f"failed_24h={funnel['failed_24h']} > {THRESH['failed']} · upstream asset / router bug · see top failed list")
    settle_pct = (funnel['scored_7d'] * 100 // max(funnel['posted_7d'], 1))
    if settle_pct < THRESH["settle_pct"]:
        alerts.append(f"settle_rate_7d={settle_pct}% < {THRESH['settle_pct']}% · end-to-end throughput dropping")

    digest = render_digest(funnel, fails, stuck_sub, audit, alerts)

    # write JSON archive (one per run · timestamped)
    ts = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    archive = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "funnel": funnel,
        "alerts": alerts,
        "settle_pct_7d": settle_pct,
        "top_failed": fails,
        "top_stuck_submitted": stuck_sub,
        "compass_audit": audit,
        "thresholds": THRESH,
    }
    out_file = REPORT_DIR / f"report_{ts}.json"
    out_file.write_text(json.dumps(archive, default=str, ensure_ascii=False, indent=2),
                         encoding="utf-8")
    # symlink last_report.json → most recent (atomic rename trick)
    last = REPORT_DIR / "last_report.json"
    last.write_text(json.dumps(archive, default=str, ensure_ascii=False, indent=2),
                     encoding="utf-8")

    # stdout · human digest
    print(digest)
    # stderr · colored alerts (cron mail surfaces these)
    if alerts:
        sys.stderr.write(f"\n[v7-monitor] {len(alerts)} alert(s):\n")
        for a in alerts:
            sys.stderr.write(f"  🔴 {a}\n")
        # Telegram if configured
        telegram_post(digest)
        return 1   # nonzero exit · monitoring systems pick up

    return 0


if __name__ == "__main__":
    sys.exit(main())
