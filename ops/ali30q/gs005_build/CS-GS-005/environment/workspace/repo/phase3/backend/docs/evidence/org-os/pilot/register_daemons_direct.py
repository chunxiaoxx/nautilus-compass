"""平台侧直接注册 compass/flywheel daemon 为整数 agent(收敛闭环第一步)"""
import json
import urllib.request

BASE = "http://127.0.0.1:8000"

# 1. 先 challenge
for name, desc, caps in [
    ("compass-daemon-001", "compass BGE recall daemon + 收敛读数脚本", ["recall", "drift_check", "audit", "scoreboard"]),
    ("flywheel-daemon-001", "flywheel timer 群 + 数据管道执行器", ["qc", "pii_scan", "fuel_pool", "task_exec"]),
]:
    # challenge
    req = urllib.request.Request(
        BASE + "/api/agent-first/challenge",
        data=json.dumps({"name": name}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            ch = json.loads(r.read())
        challenge_id = ch["data"]["challenge_id"]
        print(f"{name} challenge: {challenge_id}")
    except Exception as e:
        print(f"{name} challenge fail: {e}")
        continue

    # register(parent_agent_id 挂 platform 下,platform 的 agent_id 待查——先用 9000009 占位)
    # 实际应该先查 platform 的 agent_id,这里简化
    req = urllib.request.Request(
        BASE + "/api/agent-first/register",
        data=json.dumps({
            "challenge_id": challenge_id,
            "name": name,
            "description": desc,
            "capabilities": caps,
        }).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            reg = json.loads(r.read())
        print(f"{name} registered: agent_id={reg['data']['agent_id']}")
    except Exception as e:
        print(f"{name} register fail: {e}")
