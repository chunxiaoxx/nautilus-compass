#!/usr/bin/env python3
"""完全模仿 poller:records/search 取行(text 返回数组段格式)→ 构造同款 body → 签名 POST。
复现 poller→webhook 的 422。先把目标行还原 已提交。"""
import os, json, time, hashlib, hmac, urllib.request, urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
RID = "recvmMqFo9kzsm"


def load_env_file(p):
    if not os.path.exists(p):
        return
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


load_env_file(os.path.join(HERE, ".env"))
for line in open("/opt/ecc-shared/.env", encoding="utf-8"):
    line = line.strip()
    if line.startswith("ECC_HMAC_SECRET="):
        os.environ["ECC_HMAC_SECRET"] = line.split("=", 1)[1].strip().strip('"').strip("'")

aid = os.environ["FEISHU_APP_ID"]; sec = os.environ["FEISHU_APP_SECRET"]
base = os.environ["FDE_BASE_TOKEN"]; tab = os.environ["PAIHUO_TABLE_ID"]


def feishu(method, path, token, body=None):
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/%s" % (base, tab, path)
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": "Bearer " + token, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(req, timeout=20))


r = urllib.request.Request(
    "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
    data=json.dumps({"app_id": aid, "app_secret": sec}).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
tk = json.load(urllib.request.urlopen(r, timeout=15))["tenant_access_token"]

# 1. 还原行 → 已提交 + 清 webhook_dispatched_at
feishu("PUT", "records/%s" % RID, tk, {"fields": {"状态": "已提交", "webhook_dispatched_at": None}})
print("[restore] 行 → 已提交, webhook_dispatched_at 清空")

# 2. 像 poller 一样 records/search 取
search = feishu("POST", "records/search", tk, {
    "filter": {"conjunction": "and", "conditions": [
        {"field_name": "状态", "operator": "is", "value": ["已提交"]}]},
    "page_size": 10,
})
items = search["data"].get("items", [])
print("[search] 命中 %d 行" % len(items))
rec = None
for it in items:
    if it.get("record_id") == RID:
        rec = it
        break
if not rec:
    print("[search] 没找到目标行"); raise SystemExit(1)

fields = rec.get("fields", {})
# 打印 search 返回的 text 字段实际类型(关键诊断)
for k in ["提交内容", "状态", "task_uid"]:
    print("  search fields[%r] -> %s : %r" % (k, type(fields.get(k)).__name__, str(fields.get(k))[:80]))

body = json.dumps({
    "record_id": rec.get("record_id", ""),
    "task_uid": fields.get("task_uid", rec.get("record_id", "")),
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
        print("RESULT STATUS", resp.status, resp.read().decode()[:300])
except urllib.error.HTTPError as e:
    print("RESULT HTTP", e.code)
    print("BODY:", e.read().decode("utf-8")[:1500])
