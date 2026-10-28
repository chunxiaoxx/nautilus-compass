"""一次性:在 base EOVh 建「专家库(CRM)」表 + 招募表单视图(intake).

Run(本地·金库凭据): python phase3/backend/scripts/bootstrap_expert_crm.py
幂等:表/视图已存在则跳过。输出 table_id + form_view_id(记入宪章飞书表清单)。

设计:专家库=组织 CRM(领域专家档案);招募表单视图=应聘 intake(填→进专家库·状态=应聘中)。
关联派活表用「指派专家」文本对齐(不改派活表 schema·避免破坏 S1/S2 poller 的 _plain 文本解析)。
"""
import json
import os
import urllib.request
import urllib.error

APP = "EOVhbQwA0a1HEOsgmxecgkBVnwh"
F = "https://open.feishu.cn/open-apis"
TABLE_NAME = "专家库(CRM)"
# type: 1=文本 3=单选 2=数字 7=复选 · property.options 给单选
FIELDS = [
    {"field_name": "姓名", "type": 1},
    {"field_name": "擅长领域", "type": 1},        # 金融/法律/医疗/工程/农业/其他 或 9 类目·自由文本
    {"field_name": "擅长业务线", "type": 3, "property": {"options": [
        {"name": "一类(题目)"}, {"name": "二类(教案)"}, {"name": "一类+二类"}]}},
    {"field_name": "联系方式", "type": 1},
    {"field_name": "代表作/简历", "type": 1},
    {"field_name": "状态", "type": 3, "property": {"options": [
        {"name": "应聘中"}, {"name": "onboarding"}, {"name": "在岗"}, {"name": "暂停"}]}},
    {"field_name": "在产任务数", "type": 2, "property": {"formatter": "0"}},
    {"field_name": "通过率", "type": 1},
    {"field_name": "备注", "type": 1},
]
# 招募表单暴露给应聘者填的字段(其余=内部 ops 列·表单不暴露)
FORM_FIELDS = ["姓名", "擅长领域", "擅长业务线", "联系方式", "代表作/简历"]


def _http(method, url, token=None, body=None):
    data = json.dumps(body).encode() if body is not None else None
    h = {"Content-Type": "application/json"}
    if token:
        h["Authorization"] = "Bearer " + token
    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return json.loads(e.read().decode())


def _load_secrets():
    p = os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env")
    for ln in open(p, encoding="utf-8"):
        ln = ln.strip()
        if ln and not ln.startswith("#") and "=" in ln:
            k, v = ln.split("=", 1)
            os.environ.setdefault(k, v)


_load_secrets()
tok = _http("POST", f"{F}/auth/v3/tenant_access_token/internal", body={
    "app_id": os.environ["FEISHU_APP_ID"],
    "app_secret": os.environ["FEISHU_APP_SECRET"]})["tenant_access_token"]

# 幂等:找现有同名表
tables = _http("GET", f"{F}/bitable/v1/apps/{APP}/tables?page_size=100", token=tok)["data"]["items"]
existing = next((t for t in tables if t["name"] == TABLE_NAME), None)
if existing:
    table_id = existing["table_id"]
    print("exists table:", table_id)
else:
    j = _http("POST", f"{F}/bitable/v1/apps/{APP}/tables", token=tok,
              body={"table": {"name": TABLE_NAME, "fields": FIELDS}})
    if j.get("code") != 0:
        raise SystemExit("create table failed: " + json.dumps(j, ensure_ascii=False))
    table_id = j["data"]["table_id"]
    print("created table:", table_id)

# 招募表单视图(幂等:已存在同名跳过)
views = _http("GET", f"{F}/bitable/v1/apps/{APP}/tables/{table_id}/views?page_size=100",
              token=tok)["data"]["items"]
form = next((v for v in views if v.get("view_name") == "招募申请表单"), None)
if form:
    print("exists form view:", form["view_id"])
else:
    fv = _http("POST", f"{F}/bitable/v1/apps/{APP}/tables/{table_id}/views", token=tok,
               body={"view_name": "招募申请表单", "view_type": "form"})
    if fv.get("code") != 0:
        raise SystemExit("create form failed: " + json.dumps(fv, ensure_ascii=False))
    print("created form view:", fv["data"]["view"]["view_id"])

print("DONE · table_id:", table_id, "· base:", APP)
print("注:表单字段筛选/分享链接=飞书 UI(表单视图→设置可见字段→分享);仪表盘=UI 手动。")
