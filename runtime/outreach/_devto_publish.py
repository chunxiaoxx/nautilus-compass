import json
import os
import urllib.request

key = [l.split("=", 1)[1].strip() for l in
       open(os.path.expanduser("~/nautilus-v5/.env")) if l.startswith("DEVTO_API_KEY")][0]
body = open("/tmp/judge_devto.md", encoding="utf-8").read()
payload = json.dumps({"article": {
    "title": "We pay people to say 'insufficient evidence': human gold-standard judges for AI grader calibration",
    "body_markdown": body,
    "tags": ["ai", "llm", "opensource", "machinelearning"],
    "published": True}}).encode()
req = urllib.request.Request(
    "https://dev.to/api/articles", data=payload, method="POST",
    headers={"api-key": key, "Content-Type": "application/json",
             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
d = json.load(urllib.request.urlopen(req, timeout=30))
print("URL:", d.get("url"))
print("id:", d.get("id"), "published_at:", d.get("published_at"))
