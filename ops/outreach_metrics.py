"""Outreach metrics cron · 每天 9am · 抓 GitHub + Gmail + PG · diff baseline · Telegram push.

用途:回答 "outreach 真有效吗" — 不靠"我以为送达"· 看真数据。

L1 (delivery): drafts pushed (one-time)
L2 (ingestion): bounce-back count + open + click(无 tracking · skip)
L3 (action): GitHub stars Δ + forks Δ + issues Δ + Gmail reply count + PG compass_recall Δ
L4 (outcome): true external user signups(无 SaaS signup · skip · 用 stars 当 proxy)

State file: ~/.cache/compass/outreach-metrics-state.json
  · baseline_ts: 第一次跑的时间
  · baseline_stars / forks / issues / compass_recall_calls

Daily run · 显示 delta · push Telegram · 不 stop(用户 satisfied 后 crontab -e 删行)
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


STATE_FILE = Path(os.environ.get(
    "OUTREACH_METRICS_STATE",
    str(Path.home() / ".cache" / "compass" / "outreach-metrics-state.json")
))
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_REPO = "chunxiaoxx/nautilus-compass"


def gh_api(path: str) -> dict:
    try:
        with urlopen(f"https://api.github.com/{path}", timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        return {"_error": repr(e)[:120]}


def pg_compass_recall_24h() -> dict:
    """How many times has any agent (V5/V6/Kairos) called compass_recall in last 24h?
    Earlier today this was 0 · we want to see it climb if Anthropic alignment / etc
    actually consume our outreach AND register tokens to use the compass cloud."""
    try:
        env = {**os.environ, "PGPASSWORD": "nautilus2024"}
        r = subprocess.run(
            ["psql", "-h", "localhost", "-U", "nautilus_user", "-d", "nautilus_production",
             "-tA", "-c",
             """SELECT tool_name, count(*)
                FROM agent_tool_calls
                WHERE ts > NOW() - INTERVAL '24 hours'
                  AND tool_name IN ('compass_recall', 'compass_ingest_obs', 'compass_drift_check')
                GROUP BY 1
                ORDER BY 1"""],
            env=env, capture_output=True, text=True, timeout=10,
        )
        out = {}
        for ln in r.stdout.strip().splitlines():
            if "|" in ln:
                k, v = ln.split("|", 1)
                out[k.strip()] = int(v.strip())
        return out
    except Exception as e:
        return {"_error": repr(e)[:120]}


def send_telegram(text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        sys.stderr.write("TELEGRAM creds missing\n")
        return False
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    data = urlencode({"chat_id": TELEGRAM_CHAT_ID, "text": text[:4000]}).encode("utf-8")
    try:
        with urlopen(Request(url, data=data), timeout=10) as resp:
            return '"ok":true' in resp.read().decode("utf-8")
    except Exception as e:
        sys.stderr.write(f"telegram fail: {e!r}\n")
        return False


def main() -> int:
    now = int(time.time())

    # ── grab current metrics ──
    repo = gh_api(f"repos/{GITHUB_REPO}")
    if "_error" in repo:
        send_telegram(f"⚠️ outreach metrics · github api fail: {repo['_error']}")
        return 1

    cur = {
        "stars":   int(repo.get("stargazers_count", 0)),
        "forks":   int(repo.get("forks_count", 0)),
        "watchers": int(repo.get("subscribers_count", 0)),
        "issues":  int(repo.get("open_issues_count", 0)),
        "pushed_at": repo.get("pushed_at", ""),
    }
    pg = pg_compass_recall_24h()
    cur["pg_compass_recall_24h"] = pg.get("compass_recall", 0)
    cur["pg_compass_ingest_obs_24h"] = pg.get("compass_ingest_obs", 0)
    cur["pg_compass_drift_check_24h"] = pg.get("compass_drift_check", 0)

    # ── load / init baseline ──
    if STATE_FILE.exists():
        try:
            state = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            state = {}
    else:
        state = {}

    if "baseline_ts" not in state:
        state["baseline_ts"] = now
        state["baseline"] = cur
        STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
        STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")
        send_telegram(
            f"📊 outreach metrics · BASELINE set\n"
            f"  github: stars={cur['stars']} forks={cur['forks']} watchers={cur['watchers']} open_issues={cur['issues']}\n"
            f"  PG 24h: compass_recall={cur['pg_compass_recall_24h']} "
            f"ingest_obs={cur['pg_compass_ingest_obs_24h']} drift_check={cur['pg_compass_drift_check_24h']}\n"
            f"  baseline_ts: {time.strftime('%F %T', time.localtime(now))}\n"
            f"  next snapshot tomorrow same time · diff vs baseline · expecting GitHub stars to climb after outreach replies"
        )
        return 0

    # ── diff vs baseline ──
    base = state.get("baseline", {})
    elapsed_h = (now - state["baseline_ts"]) / 3600

    delta_lines = []
    for k in ("stars", "forks", "watchers", "issues",
              "pg_compass_recall_24h", "pg_compass_ingest_obs_24h", "pg_compass_drift_check_24h"):
        b = base.get(k, 0)
        c = cur.get(k, 0)
        d = c - b
        arrow = "→" if d == 0 else ("↑" if d > 0 else "↓")
        delta_lines.append(f"  {k:30}  {b:>4} {arrow} {c:>4}  ({d:+d})")

    # interesting signal?
    big_signal = (
        (cur["stars"] - base.get("stars", 0)) >= 1 or
        (cur["forks"] - base.get("forks", 0)) >= 1 or
        (cur["pg_compass_recall_24h"] - base.get("pg_compass_recall_24h", 0)) >= 1
    )

    tag = "🟢 GROWTH" if big_signal else "🟡 flat"
    msg = (
        f"{tag} outreach metrics · +{elapsed_h:.1f}h since baseline\n"
        f"baseline_ts: {time.strftime('%F %T', time.localtime(state['baseline_ts']))}\n"
        f"now:         {time.strftime('%F %T', time.localtime(now))}\n\n"
        f"  metric                          base → now  (Δ)\n"
        + "\n".join(delta_lines) + "\n\n"
        + ("✅ external traction signal — outreach reaching humans" if big_signal else
           "⏳ no external signal yet — drafts may need send / wait longer / re-target")
    )
    send_telegram(msg)
    print(msg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
