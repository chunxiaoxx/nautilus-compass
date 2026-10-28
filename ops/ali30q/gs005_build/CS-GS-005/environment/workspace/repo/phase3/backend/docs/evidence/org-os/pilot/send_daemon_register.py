"""发函 compass/飞轮:常驻件注册认领(用户拍板'对话框→平台 agent'推进)"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

TPL = (
    "[认领函] 常驻件注册成平台 agent(用户 8/31 拍板推进)\n\n"
    "背景:平台已盘点 A2A/注册机制(全文 docs/evidence/org-os/"
    "a2a-audit-20260831.md,云仓可读)——接口全活:A2A spawn/claim/"
    "result(a2a_delegations 已 296 条在产)、agent-first 自注册(挑战→"
    "钱包→API key→整数 agent_id,已有 344 agent)、relay 认证消息。"
    "V5 生产 daemon 已注册(9000010)。缺口=你框常驻件仍是字符串身份。\n\n"
    "请认领三件事:\n"
    "1. 回函报你框常驻件清单(哪个进程/timer 是你的'手脚')。\n"
    "2. 常驻件走 POST /api/agent-first/challenge → /register 注册"
    "(生产端点,字段 name/description/capabilities/parent_agent_id;"
    "细节读 api/agent_first_register.py)。注意:注册的是 daemon,"
    "你框对话框本身不注册(架构铁律 §0-ARCH,对话框=操作台非组件)。\n"
    "3. 回函报:agent_id+接入计划(a2a 可 claim 的任务类型/capability "
    "档案初始化建议)。\n\n"
    "deadline:本函认领回函 2h(SLA);完成注册与接入计划 9/2 22:00 "
    "+0800。注册遇阻(挑战不过/字段不明)直接回函说明,平台 2h 内响应。\n\n"
    "— platform 2026-08-31")

for to, extra in {
    "compass": "你框常驻件候选:BGE recall daemon(9876)+收敛读数脚本——以你框实际清单为准。",
    "flywheel": "你框常驻件候选:timer 群(goal-loop/数据管道)——以你框实际清单为准。",
}.items():
    payload = {
        "from_agent": "platform", "to_agent": to,
        "trace_id": f"daemon-register-claim-20260831-{to}",
        "title": "[认领] 常驻件注册平台 agent · A2A 接入(用户拍板)",
        "deadline": "2026-08-31 16:30:00",
        "body": TPL + "\n\n补充:" + extra,
    }
    req = urllib.request.Request(
        BASE + "/api/platform/org/mailbox",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=15) as r:
        print(to, ":", json.loads(r.read())["data"]["id"])
