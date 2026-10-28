"""一次性:派活表(EOVh/tbl69fankpoBhJfw)加 S2 列:提交内容/QC反馈 + 状态值已通过/已打回.

Run(本地·金库凭据): python phase3/backend/scripts/add_qc_columns.py
幂等:已存在的列/选项跳过。
"""
import json
import os
import urllib.request

APP, TABLE = "EOVhbQwA0a1HEOsgmxecgkBVnwh", "tbl69fankpoBhJfw"
FEISHU = "https://open.feishu.cn/open-apis"
NEW_TEXT_FIELDS = ["提交内容", "QC反馈"]
NEW_STATUS_OPTIONS = ["已通过", "已打回"]


def _http(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def _load_secrets():
    p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
    with open(p, encoding="utf-8") as fh:
        for ln in fh:
            ln = ln.strip()
            if ln and not ln.startswith("#") and "=" in ln:
                k, v = ln.split("=", 1)
                os.environ.setdefault(k, v)


_load_secrets()
tok = _http("POST", f"{FEISHU}/auth/v3/tenant_access_token/internal", body={
    "app_id": os.environ["FEISHU_APP_ID"],
    "app_secret": os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]

fields = _http("GET", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields?page_size=100",
               token=tok)["data"]["items"]
names = {f["field_name"]: f for f in fields}

for name in NEW_TEXT_FIELDS:
    if name in names:
        print("exists:", name)
        continue
    _http("POST", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields", token=tok,
          body={"field_name": name, "type": 1})
    print("created:", name)

status = names["状态"]
existing = (status.get("property") or {}).get("options", [])
opts = [o["name"] for o in existing]
missing = [o for o in NEW_STATUS_OPTIONS if o not in opts]
if missing:
    # 🔴 gotcha(2026-06-12 实证):options 必须原对象带 id 透传,只给 name 会重建全部
    # 选项 → 既有行的单选值被清空(本表 已领取 被清过一次·已手工修复)。
    _http("PUT", f"{FEISHU}/bitable/v1/apps/{APP}/tables/{TABLE}/fields/{status['field_id']}",
          token=tok, body={"field_name": "状态", "type": 3, "property": {
              "options": existing + [{"name": o} for o in missing]}})
    print("status options added:", missing)
else:
    print("status options ok:", opts)
