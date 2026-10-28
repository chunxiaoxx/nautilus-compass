#!/usr/bin/env python3
"""Walking-skeleton 首跑:seed 一道真第2类(教案)任务到 RGDK v06_派活,驱动状态转换。

诚实定位:平台作「专家#1」seed walking-skeleton 首任务(bot-member 架构·审计记 writer_source)。
内容=真实平台一手 dev 经验教案(persona drift 检测器·非编造)。**交付物 provisional**——
未经真专家过买方 AI 检测,不当买方终品。目的=验证 ①「派活→提交→QC→交付→结算」三台
(前台 RGDK + 中台 FDE webhook + 后台我 runner)全程流一遍且可见。

用法:
  create  — 建行(状态=已派单·含提交内容)
  submit <rid> — 状态→已提交(触发 FDE webhook → 我 s2_auto_qc)
  approve <rid> — 状态→已通过(触发 → 我 s3)  [通常 s2 自动写已通过·此为手动兜底]
  show <rid> — 读回当前态(状态/QC反馈/应付金额)
  delete <rid>
env: FEISHU_APP_ID / FEISHU_APP_SECRET(我引擎 app)
"""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from pathlib import Path

B = "https://open.feishu.cn/open-apis"
APP = "RGDKbrtZ1aMcEOsZ2GcczeFknNg"
TABLE = "tblfPoDrZzKHpU36"  # v06_派活
UID = "expert_line2_persona_drift_20260616"
FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "_fixtures_s3_drift_draft.md"


def _req(method, url, token=None, body=None):
    h = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        h["Authorization"] = f"Bearer {token}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    r = urllib.request.Request(url, data=data, headers=h, method=method)
    with urllib.request.urlopen(r, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def token():
    r = _req("POST", f"{B}/auth/v3/tenant_access_token/internal", body={
        "app_id": os.environ["FEISHU_APP_ID"], "app_secret": os.environ["FEISHU_APP_SECRET"]})
    if r.get("code") != 0:
        raise SystemExit(f"token failed: {r}")
    return r["tenant_access_token"]


def create(tok):
    content = FIXTURE.read_text(encoding="utf-8")
    fields = {
        "task_uid": UID,
        "标题": "persona drift 在线检测器教案(平台一手·walking-skeleton 首跑)",
        "业务线": "2·教案",
        "一级类目": "工程",
        "三级领域": "agent 可靠性工程",
        "L级": "L2",
        "指派专家": "平台专家#1",
        "验收标准": "4段结构齐全(Instruction/Knowledge Points/Background Knowledge/Task示例)·"
                    "知识点≥5·Background每段含权衡或局限·正文真人撰写非AI生成·有可执行Task示例带答案",
        "提交内容": content,
        "状态": "已派单",
        "工时": 6,
        "工时来源": "专家申报",
        "备注": "walking-skeleton 首跑·平台作专家#1·内容=真实平台一手经验·交付物 provisional(未过买方AI检测)",
    }
    r = _req("POST", f"{B}/bitable/v1/apps/{APP}/tables/{TABLE}/records", tok, {"fields": fields})
    if r.get("code") != 0:
        raise SystemExit(f"create failed: {r}")
    rid = r["data"]["record"]["record_id"]
    print(f"CREATE OK · record_id={rid} · uid={UID} · 状态=已派单")
    return rid


def set_status(tok, rid, status):
    r = _req("PUT", f"{B}/bitable/v1/apps/{APP}/tables/{TABLE}/records/{rid}", tok,
             {"fields": {"状态": status}})
    print(f"SET 状态={status} · code={r.get('code')} msg={r.get('msg')}")


def show(tok, rid):
    r = _req("GET", f"{B}/bitable/v1/apps/{APP}/tables/{TABLE}/records/{rid}", tok)
    f = r["data"]["record"]["fields"]
    print("状态:", f.get("状态"))
    print("QC反馈:", (f.get("QC反馈") or "(空)")[:400])
    print("应付金额:", f.get("应付金额"))


def delete(tok, rid):
    r = _req("DELETE", f"{B}/bitable/v1/apps/{APP}/tables/{TABLE}/records/{rid}", tok)
    print(f"DELETE code={r.get('code')}")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "create"
    tok = token()
    if cmd == "create":
        create(tok)
    elif cmd == "submit":
        set_status(tok, sys.argv[2], "已提交")
    elif cmd == "approve":
        set_status(tok, sys.argv[2], "已通过")
    elif cmd == "show":
        show(tok, sys.argv[2])
    elif cmd == "delete":
        delete(tok, sys.argv[2])
