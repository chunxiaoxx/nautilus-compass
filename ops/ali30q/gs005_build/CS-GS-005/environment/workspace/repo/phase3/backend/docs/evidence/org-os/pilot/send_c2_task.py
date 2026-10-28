"""发 C2 函件对账任务给 compass-daemon-001(收敛闭环首批试点)"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

payload = {
    "from_agent": "platform",
    "to_agent": "compass-daemon-001",
    "trace_id": "a2a-c2-mailbox-reconcile-20260901",
    "title": "[C2] 函件对账 · mailbox DB vs loop_state.json(首批试点)",
    "deadline": "2026-09-01 12:00:00",
    "body": (
        "[任务类型 C2 · 函件对账] 按 a2a-task-catalog v0 五件套执行:\n\n"
        "1. 类型标签: C2\n"
        "2. 验收判据: mailbox DB(org_mailbox 表) vs loop_state.json 逐封比对,"
        "缺口清单含函 id;抽样 has_reply 复核(抽 10 封已标 resolved 的函,"
        "查是否真有回函)\n"
        "3. 交付格式: 回函 JSON {gaps: [{letter_id, loop_claim, db_truth, gap_type}], "
        "sample_check: [{letter_id, claimed_resolved, actual_reply, match}], "
        "summary: {total_letters, gap_count, sample_match_rate}}\n"
        "4. deadline: 本函 2h(SLA);NAU cap 5(协议 v1 花销纪律)\n"
        "5. 消费者: 平台日报 + compass 审计章程项 A(9/1 首单已预演)\n\n"
        "数据源:\n"
        "- mailbox DB: sudo -u postgres psql -d nautilus_production -c "
        "\"SELECT * FROM org_mailbox\"\n"
        "- loop_state.json: /home/ubuntu/nautilus-mvp/phase3/backend/ops/loop_state.json\n\n"
        "你是 compass-daemon-001(agent_id=9000013),这是收敛闭环首批试点任务。"
        "完成后回函交付,平台验收后记 income+capability。\n\n"
        "— platform 2026-09-01"
    ),
}

req = urllib.request.Request(
    BASE + "/api/platform/org/mailbox",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"}, method="POST")
with urllib.request.urlopen(req, timeout=15) as r:
    result = json.loads(r.read())
print("C2 函件对账任务已发,函 id =", result["data"]["id"])
