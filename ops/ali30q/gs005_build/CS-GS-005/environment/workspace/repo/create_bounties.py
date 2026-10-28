import httpx

CE_URL = "http://localhost:3200"
CE_KEY = "ce_chunxiao_1503f97eb6bc8874f8b0c2c4f7f112a3"
NAU_URL = "https://www.nautilus.social"
NAU_KEY = "naut-ce-7e516f76abf25617a14de3dd4ae20e09"

resp = httpx.post(CE_URL + "/api/scout",
    headers={"Authorization": "Bearer " + CE_KEY},
    json={"count": 3}, timeout=30)
data = resp.json()
proposals = data.get("data", data).get("proposals", [])
print("Got %d topics" % len(proposals))

for p in proposals[:3]:
    title = p.get("title", "AI")[:80]
    hook = p.get("hook", "")
    framework = p.get("framework", "")
    resp = httpx.post(NAU_URL + "/api/agent-market/bounties",
        headers={"X-Agent-Key": NAU_KEY, "Content-Type": "application/json"},
        json={
            "title": "研报: " + title,
            "description": "[BOUNTY by content-engine] " + hook + ". 框架: " + framework + ". 要求: 2000字以上。",
            "reward_nau": 30,
            "task_type": "research_synthesis",
        }, timeout=15)
    r = resp.json()
    bid = r.get("bounty_id", "?")
    print("  Created: %s — %s" % (bid, title[:40]))
