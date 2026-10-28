#!/usr/bin/env python3
"""cron/unit 失败通知器(2026-10-07 B8) · 由 systemd OnFailure=nautilus-cron-fail-notifier@<unit>.service 触发
收 %i(失败 unit 名)→抓 journal 尾 20 行→INSERT org_mailbox(B 账正本,to=platform)告警。
"""
import sys, os, json, subprocess, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
unit = sys.argv[1] if len(sys.argv) > 1 else "unknown"
journal = subprocess.run(["journalctl", "-u", unit, "-n", "20", "--no-pager", "-o", "cat"],
                         capture_output=True, text=True).stdout[-3000:]
for line in open("/home/ubuntu/nautilus-mvp/phase3/backend/.env"):
    line = line.strip()
    if line.startswith("DATABASE_URL"):
        url = line.split("=", 1)[1].strip()
        if "postgresql+" in url: url = url.split("+", 1)[1]
        break
else:
    url = os.environ.get("DATABASE_URL", "")
import psycopg2
c = psycopg2.connect(url, connect_timeout=8)
cur = c.cursor()
cur.execute("""INSERT INTO org_mailbox (trace_id, from_agent, to_agent, title, body, deadline, created_at)
VALUES (%s,%s,%s,%s,%s,%s,now())""",
            ("onfailure-"+unit+"-"+datetime.datetime.now().strftime("%H%M%S"), "platform", "platform",
             f"[OnFailure] {unit} 失败",
             f"unit={unit}\njournal 尾 20 行:\n{journal}",
             datetime.datetime.now() + datetime.timedelta(hours=4)))
c.commit()
print(f"alert inserted for {unit}")
