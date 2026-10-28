"""反向写测探针:验证我引擎 bot 对 RGDK v06_派活 有 editor 写权。
先列字段(确认 SingleSelect 选项名)→ 可选写一行测试行 → 读回。
用法:
  python _probe_rgdk_write.py fields           # 只列字段
  python _probe_rgdk_write.py write            # 写一行测试行并读回
  python _probe_rgdk_write.py delete <rec_id>  # 删除测试行
env: FEISHU_APP_ID / FEISHU_APP_SECRET (我引擎 app)
"""
import json
import os
import sys
import urllib.request

BASE = "https://open.feishu.cn/open-apis"
APP_TOKEN = "RGDKbrtZ1aMcEOsZ2GcczeFknNg"
TABLE_ID = "tblfPoDrZzKHpU36"  # v06_派活


def _post(url, body, token=None):
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _get(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def _del(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"}, method="DELETE")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def token():
    app_id = os.environ["FEISHU_APP_ID"]
    secret = os.environ["FEISHU_APP_SECRET"]
    resp = _post(f"{BASE}/auth/v3/tenant_access_token/internal",
                 {"app_id": app_id, "app_secret": secret})
    if resp.get("code") != 0:
        raise SystemExit(f"token failed: {resp}")
    return resp["tenant_access_token"]


def fields(tok):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/fields?page_size=100"
    resp = _get(url, tok)
    if resp.get("code") != 0:
        raise SystemExit(f"fields read failed (bot 无读权?): {resp}")
    items = resp["data"]["items"]
    print(f"=== v06_派活 字段 ({len(items)}) ===")
    for f in items:
        ftype = f["type"]
        extra = ""
        if "property" in f and f["property"] and "options" in (f["property"] or {}):
            opts = [o["name"] for o in f["property"]["options"]]
            extra = f"  options={opts}"
        print(f"  [{ftype}] {f['field_name']}{extra}")
    return items


def write(tok):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records"
    row = {
        "fields": {
            "task_uid": "probe_platform_soul_writetest_20260616",
            "标题": "[反向写测·platform-soul bot 可删] editor 授权验证",
            "状态": "待派单",
            "备注": "platform-soul bot 反向写测·验证 RGDK editor 授权·可删",
        }
    }
    resp = _post(url, row, tok)
    if resp.get("code") != 0:
        raise SystemExit(f"WRITE FAILED (editor 未生效?): {resp}")
    rec = resp["data"]["record"]["record_id"]
    print(f"WRITE OK · record_id={rec}")
    # read back
    rb = _get(f"{url}/{rec}", tok)
    print(f"READBACK code={rb.get('code')} fields={json.dumps(rb['data']['record']['fields'], ensure_ascii=False)}")
    return rec


def delete(tok, rec):
    url = f"{BASE}/bitable/v1/apps/{APP_TOKEN}/tables/{TABLE_ID}/records/{rec}"
    resp = _del(url, tok)
    print(f"DELETE code={resp.get('code')} msg={resp.get('msg')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fields"
    tok = token()
    print(f"token OK (app={os.environ['FEISHU_APP_ID']})")
    if cmd == "fields":
        fields(tok)
    elif cmd == "write":
        fields(tok)
        write(tok)
    elif cmd == "delete":
        delete(tok, sys.argv[2])
