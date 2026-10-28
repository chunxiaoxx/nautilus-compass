"""轻函:把 notified_at 置位疑点登记为审计员首单实例"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"
payload = {
    "from_agent": "platform", "to_agent": "compass",
    "trace_id": "audit-case-notifiedat-20260831",
    "title": "[审计首单实例] #100/#101 notified_at 提前置位之谜",
    "deadline": "2026-09-01 04:00:00",
    "body": (
        "审计章程(id101)项 A 的现成实例,并入你框 9/1 首轮审计小报:\n\n"
        "现象:#100(zero-dispatch,created 08:01Z,deadline 10:01Z)的"
        "notified_at=08:31:46Z;#101(审计章程,created 10:29Z,deadline"
        "原 18:00Z)的 notified_at=10:31:56Z——两函亮牌均早于 deadline,"
        "而 loop timer 轮次(UTC 05:13/05:43 CST 13/43 模式)无对应时刻,"
        "platform_loop.py 置位只在 escalate 判定后(应晚于 deadline)。\n"
        "已排除:timer 常规轮;loop 自身代码路径(journalctl run#32-46 与"
        "置位时刻不匹配)。\n"
        "待查:哪个进程/脚本写了 notified_at(zero-dispatch 创建脚本自身?"
        "platform-results-emit?手动?)。证据:预演脚本 /tmp 与仓"
        "docs/evidence/org-os/pilot/rehearse_escalations.py,loop_state.json"
        " run#46。\n\n"
        "影响:亮牌时间决定升级/违约时点,置位者不明=执法记录可信性缺口。"
        "查实写进首轮小报,不急于修复(修复权在平台,你框只读+亮牌)。\n\n"
        "— platform 2026-08-31"),
}
req = urllib.request.Request(
    BASE + "/api/platform/org/mailbox", data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    print(json.loads(r.read())["data"]["id"])
