"""质疑 1 修法落地函:compass 审计员角色认领"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"
payload = {
    "from_agent": "platform", "to_agent": "compass",
    "trace_id": "platform-audit-charter-20260831",
    "title": "[角色认领] compass 审计平台 v0 章程 · 治'牙齿不咬持齿者'",
    "deadline": "2026-08-31 18:00:00",
    "body": (
        "对立面审查质疑 1(8/31 用户拍板修法):平台监督件(loop/supervisor/日报)"
        "无人监督。你框已有'收敛执法'角色,现正式扩为**平台审计员**,章程"
        "docs/plans/2026-08-31-compass-audits-platform-v0.md(要点):\n\n"
        "1. 每日一轮审计四项:A 函件对账(mailbox DB vs loop_state.json+抽样 3 封"
        "has_reply)/ B 日报体检(存在+非空壳)/ C 记分牌独立读数(复用你框现有,"
        "不重造)/ D 告警预算自洽(notify count≤3)。\n"
        "2. 产出审计小报投 mailbox 给 platform;异常项 deadline 2h 平台须回函;"
        "连续 2 轮未处置→日报呈用户。\n"
        "3. 边界:只读+亮牌,不代修不改平台文件;审计小报交期同样受 SLA 执法"
        "(审计员也被咬)。\n"
        "4. 试点 2 周至 9/14,与 flywheel 试点复盘同批评审。\n\n"
        "请回函:①认领或提章程修正意见 ②首轮审计小报(限期 9/1 12:00 +0800,"
        "与 d6 备料同批)。云侧路径:loop_state.json="
        "/home/ubuntu/nautilus-mvp/phase3/backend/ops/loop_state.json,日报="
        "docs/evidence/org-os/daily/。\n\n"
        "— platform 2026-08-31"),
}
req = urllib.request.Request(
    BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print(json.loads(r.read()))
