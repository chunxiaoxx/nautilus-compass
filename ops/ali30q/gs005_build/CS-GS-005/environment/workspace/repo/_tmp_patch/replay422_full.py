#!/usr/bin/env python3
"""用真实完整 feishu fields 复现 poller→webhook 的 422,打印 Pydantic body。"""
import os, json, time, hashlib, hmac, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env_file(p):
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_file(os.path.join(HERE, ".env"))           # runner .env (FEISHU_APP_*)
# ECC_HMAC_SECRET 在 poller 的 env file
for line in open("/opt/ecc-shared/.env", encoding="utf-8"):
    line = line.strip()
    if line.startswith("ECC_HMAC_SECRET="):
        os.environ["ECC_HMAC_SECRET"] = line.split("=", 1)[1].strip().strip('"').strip("'")

aid = os.environ["FEISHU_APP_ID"]; sec = os.environ["FEISHU_APP_SECRET"]
base = os.environ["FDE_BASE_TOKEN"]; tab = os.environ["PAIHUO_TABLE_ID"]
rid = "recvmMqFo9kzsm"

r = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": aid, "app_secret": sec}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
tk = json.load(urllib.request.urlopen(r, timeout=15))["tenant_access_token"]

r2 = urllib.request.Request(
    "https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/records/%s" % (base, tab, rid),
    headers={"Authorization": "Bearer " + tk})
fields = json.load(urllib.request.urlopen(r2, timeout=15))["data"]["record"]["fields"]
fields["状态"] = "已提交"

body = json.dumps({
    "record_id": rid,
    "task_uid": fields.get("task_uid", ""),
    "status": "已提交",
    "table_id": tab,
    "fields": fields,
}, ensure_ascii=False).encode("utf-8")

hsec = os.environ.get("ECC_HMAC_SECRET", "").encode()
ts = str(int(time.time()))
sig = "sha256=" + hmac.new(hsec, ts.encode() + b"." + body, hashlib.sha256).hexdigest()
req = urllib.request.Request("http://127.0.0.1:8848/webhook/s2_auto_qc", data=body, method="POST",
    headers={"Content-Type": "application/json", "X-Lark-Signature": sig, "X-Lark-Timestamp": ts})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        print("STATUS", resp.status, resp.read().decode()[:300])
except urllib.error.HTTPError as e:
    print("HTTP", e.code)
    print("BODY:", e.read().decode("utf-8")[:1500])
