#!/usr/bin/env python3
"""复现 poller→webhook 的 422,打印 Pydantic 错误详情。读 /opt/ecc-shared/.env 的 ECC_HMAC_SECRET。"""
import os, json, time, hashlib, hmac, urllib.request, urllib.error

def load_env(p):
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

load_env("/opt/ecc-shared/.env")
secret = os.environ.get("ECC_HMAC_SECRET", "").encode()
base = os.environ.get("FDE_WEBHOOK_BASE", "http://127.0.0.1:8848")

# 模拟 poller 对我 test 行构造的 body(record_id 来自 create)
body = json.dumps({
    "record_id": "recvmMqFo9kzsm",
    "task_uid": "my_test_webhook_e2e_replay",
    "status": "已提交",
    "table_id": "tblfPoDrZzKHpU36",
    "fields": {"状态": "已提交", "task_uid": "my_test_webhook_e2e_replay"},
}).encode()

ts = str(int(time.time()))
msg = ts.encode() + b"." + body
sig = "sha256=" + hmac.new(secret, msg, hashlib.sha256).hexdigest()
print("secret_set=%s base=%s" % (bool(secret), base))

req = urllib.request.Request(base + "/webhook/s2_auto_qc", data=body, method="POST", headers={
    "Content-Type": "application/json",
    "X-Lark-Signature": sig,
    "X-Lark-Timestamp": ts,
    "X-Poller-Source": "replay422",
})
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        print("STATUS", r.status, r.read().decode()[:500])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print("BODY:", e.read().decode()[:1000])
