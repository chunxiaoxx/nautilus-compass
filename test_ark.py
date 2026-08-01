"""test_ark.py · quick connectivity probe"""
import json, urllib.request, os
SECRETS_ENV = os.environ.get("FDE_API_SECRETS_ENV", "/home/ubuntu/.claude/.cache/.fde_api_secrets.env")
d = {}
with open(SECRETS_ENV) as f:
    for ln in f:
        if "=" in ln and not ln.strip().startswith("#"):
            k, v = ln.strip().split("=", 1); d[k] = v
base = d.get("ARK_BASE_URL")
model = d.get("ARK_MODEL_DOUBAO")
key = d.get("ARK_API_KEY")
print(f"BASE={base} MODEL={model} KEY={key[:8]}...")
url = base + "/chat/completions"
body = json.dumps({
    "model": model,
    "messages": [{"role": "user", "content": "Reply with one word: PONG"}],
    "max_tokens": 20,
}).encode("utf-8")
req = urllib.request.Request(url, data=body, method="POST",
                              headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("STATUS", r.status)
        print(r.read().decode("utf-8")[:500])
except urllib.error.HTTPError as e:
    print("HTTPError", e.code, e.read().decode("utf-8")[:300])
except Exception as e:
    print("Error:", type(e).__name__, str(e)[:200])