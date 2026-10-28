#!/usr/bin/env python3
"""platform-soul · webhook 端到端受控测试工具(demo 前验证 poller→webhook→runner→writeback)。
在 FDE host 跑(/opt/ecc-shared/runner/platform_soul/ 同目录有 .env)。
子命令:
  fields                 列 v06_派活 字段
  create                 建一个 my_test_webhook_e2e_<ts> 行(状态=已提交)·打印 record_id
  check <record_id>      读该行 状态/QC反馈/webhook_dispatched_at
  delete <record_id>     删除该行(清理)
用法: python3 webhook_e2e_test.py <cmd> [record_id]
"""
import os, sys, json, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))


def load_env():
    p = os.path.join(HERE, ".env")
    if os.path.exists(p):
        for line in open(p, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


def tok():
    app_id = os.environ["FEISHU_APP_ID"]; app_secret = os.environ["FEISHU_APP_SECRET"]
    r = urllib.request.Request(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        data=json.dumps({"app_id": app_id, "app_secret": app_secret}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    return json.load(urllib.request.urlopen(r, timeout=15))["tenant_access_token"]


def api(method, path, token, body=None):
    base = os.environ["FDE_BASE_TOKEN"]; table = os.environ["PAIHUO_TABLE_ID"]
    url = "https://open.feishu.cn/open-apis/bitable/v1/apps/%s/tables/%s/%s" % (base, table, path)
    data = json.dumps(body).encode() if body is not None else None
    r = urllib.request.Request(url, data=data, method=method,
        headers={"Authorization": "Bearer %s" % token, "Content-Type": "application/json"})
    return json.load(urllib.request.urlopen(r, timeout=20))


def main():
    load_env()
    cmd = sys.argv[1] if len(sys.argv) > 1 else "fields"
    t = tok()
    if cmd == "fields":
        d = api("GET", "fields?page_size=50", t)
        for it in d["data"]["items"]:
            name = it["field_name"]; typ = it["type"]
            print("  [%s] type=%s" % (name, typ))
    elif cmd == "create":
        uid = "my_test_webhook_e2e_%d" % int(time.time())
        # 线2 教案 4 段最小可 QC 内容(完整性 validate 用)
        submission = (
            "## 任务标题\nWEBHOOK 端到端测试教案(my_test·测完即删)\n\n"
            "## 领域\n工程\n\n"
            "## 一、Instruction\n演示 webhook→runner 链路的占位教案。\n\n"
            "## 二、Knowledge Points\n1. poller 扫已提交行\n2. webhook 派 subprocess\n3. runner 写回 QC\n\n"
            "## 三、Background Knowledge\n这是 webhook 端到端验证的占位正文,用于触发 s2_auto_qc runner 的完整性校验路径。"
            "内容仅供链路测试,非真实交付,测完删除。权衡:占位文本无知识密度,故预期 QC 打回(正是要验证写回路径生效)。\n\n"
            "## 四、Task 示例\n占位任务:确认 webhook 触发后 runner 写回 QC反馈字段。\n")
        fields = {
            "标题": uid,
            "task_uid": uid,
            "业务线": "2·教案",
            "状态": "已提交",
            "提交内容": submission,
        }
        d = api("POST", "records", t, {"fields": fields})
        rid = d["data"]["record"]["record_id"]
        print("CREATED record_id=%s task_uid=%s 状态=已提交" % (rid, uid))
    elif cmd == "check":
        rid = sys.argv[2]
        d = api("GET", "records/%s" % rid, t)
        f = d["data"]["record"]["fields"]
        def g(k):
            v = f.get(k)
            if isinstance(v, list):
                return json.dumps(v, ensure_ascii=False)[:200]
            return str(v)[:200]
        print("状态 =", g("状态"))
        print("webhook_dispatched_at =", g("webhook_dispatched_at"))
        print("webhook_status =", g("webhook_status"))
        print("QC反馈 =", g("QC反馈"))
    elif cmd == "delete":
        rid = sys.argv[2]
        api("DELETE", "records/%s" % rid, t)
        print("DELETED %s" % rid)
    else:
        print("unknown cmd", cmd)


if __name__ == "__main__":
    main()
