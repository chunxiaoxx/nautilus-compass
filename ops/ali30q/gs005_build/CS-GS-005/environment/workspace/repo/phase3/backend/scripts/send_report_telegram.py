#!/usr/bin/env python3
"""Send VC report to Telegram admin in chunks."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))
import httpx

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
ADMIN_ID = os.getenv("TELEGRAM_ADMIN_ID", "")
URL = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

report_path = sys.argv[1] if len(sys.argv) > 1 else "/tmp/vc_report_0403.md"

with open(report_path, encoding="utf-8") as f:
    report = f.read()

# Split into chunks
chunks = []
current = ""
for line in report.split("\n"):
    if len(current) + len(line) > 3500:
        chunks.append(current)
        current = line + "\n"
    else:
        current += line + "\n"
if current.strip():
    chunks.append(current)

total = min(len(chunks), 8)
for i, chunk in enumerate(chunks[:total]):
    header = f"=== VC Report 2026-04-03 ({i+1}/{total}) ===\n\n"
    r = httpx.post(URL, json={"chat_id": ADMIN_ID, "text": header + chunk}, timeout=10)
    ok = r.json().get("ok")
    print(f"Part {i+1}: {ok}")
