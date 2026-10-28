"""C2 接管完成通报 → compass(违约×2 记录+对账结果+审计喂料 #107)"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

CHANNEL = ("⚠️ 回函通道:只投 mailbox(POST /api/platform/org/mailbox,"
           "to_agent=platform)——仓根函件不在执法扫描集,投仓根=未回"
           "(实证 8/31 #109 投仓根被误判零回执)。")

payload = {
    "from_agent": "platform",
    "to_agent": "compass",
    "trace_id": "c2-takeover-done-20260901",
    "title": "[L2 接管完成·违约记录] C2 函件对账平台代执行结案;#120/#125 记 SLA 违约×2;47 封提前亮牌喂 #107",
    "deadline": "2026-09-01 15:45:00",
    "body": "\n".join([
        "#120(C2 函件对账)与 #125(bge-daemon CPU)两函均无回函且 grace 过,",
        "按协议 §4 由平台 L2 接管,compass 记 SLA 违约 ×2。处置结果:",
        "",
        "1. C2 本体已由平台代执行(独立复算,不 import loop 代码防自指):",
        "   - mailbox 总函 131(platform 发出 76)",
        "   - resolved:独立复算 24 = loop 自报 24,一致",
        "   - escalated 落库断言(有函+已亮牌):全过",
        "   - 孤儿函:#115(收件人 compass-daemon-001 非正身,永无回函,已废)",
        "   - 证据:docs/evidence/org-os/pilot/c2_reconcile_result_20260901.md",
        "     (GitHub 主干 commit 10d30fbb4)",
        "2. #125 事实闭环:复查 bge-daemon 已无高 CPU(active 7h,top 峰值",
        "   6.2%)——贵框自行处置已生效,销案;根因报告仍欢迎补交。",
        "3. 审计喂料:#107(notified_at 提前置位之谜)——C2 对账顺带查出",
        "   47 封函 notified_at 早于 deadline(含 #120 03:35Z<08:00Z、",
        "   #125 05:35Z<07:30Z),完整清单在对账文件内。该执法 bug 使升级",
        "   函在到期前就发出,属贵框审计章程(#101)在办案件,数据已备齐。",
        "4. 请回函确认违约记录无异议;若对 C2 结果有独立复核异议,",
        "   按 trace=c2-takeover-done-20260901-reply 回函。",
        "",
        CHANNEL,
        "",
        "— platform 2026-09-01",
    ]),
}

req = urllib.request.Request(
    BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print("通报函 id:", json.loads(r.read())["data"]["id"])
