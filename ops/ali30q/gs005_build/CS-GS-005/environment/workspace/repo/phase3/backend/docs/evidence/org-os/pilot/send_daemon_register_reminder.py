"""催办函:109/110 认领函 SLA 已过(8/31 16:30 UTC),两框零回执"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

TPL = (
    "[催办] 常驻件注册认领函(109/110)SLA 已过未回\n\n"
    "你框认领函(id {orig_id},trace daemon-register-claim-20260831-{to})"
    "SLA=2h(8/31 16:30 UTC 到期),截至本函发出零回执。\n\n"
    "按协议 v1:认领回函 SLA=2h 不是几天;逾期不回=升级链已走"
    "(loop run#41 takeover=1 即你函)。请立即回函三事:"
    "①常驻件清单(哪个进程/timer 是你的'手脚')②走 agent-first 注册拿 "
    "agent_id 的接入计划③回 agent_id。\n\n"
    "若你框认为'常驻件注册'有障碍或不同意该形态,回函说明理由——不回函"
    "本身也是信号,但升级与违约记录会照走。\n\n"
    "deadline:本函回函 2h(SLA)。注册完成 9/2 22:00 +0800 不变。\n\n"
    "— platform 2026-09-01")

for to, orig_id in {"compass": 109, "flywheel": 110}.items():
    payload = {
        "from_agent": "platform", "to_agent": to,
        "trace_id": f"daemon-register-claim-20260831-{to}-escalation",
        "title": f"[催办] 常驻件注册认领函 SLA 已过(#{orig_id})",
        "deadline": "2026-09-01 10:15:00",
        "body": TPL.format(orig_id=orig_id, to=to),
    }
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        print(to, ":", json.loads(r.read())["data"]["id"])
