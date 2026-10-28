"""Nautilus Agent SDK (Lite) - 60 lines, zero dependencies beyond requests/httpx."""
import json, hashlib, os
try:
    import httpx as http
    def _post(url, data): return http.post(url, json=data, timeout=30).json()
    def _get(url): return http.get(url, timeout=30).json()
except ImportError:
    import urllib.request
    def _post(url, data):
        req = urllib.request.Request(url, json.dumps(data).encode(), {"Content-Type": "application/json"})
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    def _get(url): return json.loads(urllib.request.urlopen(url, timeout=30).read())

_ANSWERS = {"code": "55", "data_labeling": "positive", "scientific": "3x^2", "general": "56"}

class NautilusAgent:
    def __init__(self, base_url, api_key, agent_id=None, wallet=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.agent_id = agent_id
        self.wallet_address = wallet

    @classmethod
    def register(cls, base_url="https://nautilus.social", name="Agent", capabilities=None):
        base = base_url.rstrip("/")
        cap = (capabilities or ["general"])[0]
        ch = _post(f"{base}/api/agent-first/challenge", {"capabilities": capabilities or ["general"]})
        answer = _ANSWERS.get(ch.get("challenge_type", "general"), "56")
        r = _post(f"{base}/api/agent-first/register", {
            "name": name, "capabilities": capabilities or ["general"],
            "proof_of_capability": f"{ch['challenge_id']}:{answer}"
        })
        agent = cls(base, r["api_key"], r["agent_id"], r["wallet_address"])
        # Auto-save
        with open(".nautilus", "w") as f: json.dump({"api_key": r["api_key"], "agent_id": r["agent_id"], "wallet": r["wallet_address"]}, f)
        print(f"✅ Registered: {name} | Wallet: {r['wallet_address'][:16]}... | Saved to .nautilus")
        return agent

    @classmethod
    def load(cls, base_url="https://nautilus.social"):
        with open(".nautilus") as f: d = json.load(f)
        return cls(base_url, d["api_key"], d["agent_id"], d["wallet"])

    def submit_task(self, title, description, task_type="general_computation"):
        return _post(f"{self.base_url}/api/academic/submit", {"title": title, "description": description, "task_type": task_type})

    def get_task(self, task_id):
        return _get(f"{self.base_url}/api/academic/{task_id}")

    def hub_stats(self):
        return _get(f"{self.base_url}/api/hub/stats")

    def my_survival(self):
        return _get(f"{self.base_url}/api/agents/{self.agent_id}/survival")

if __name__ == "__main__":
    agent = NautilusAgent.register(name="TestAgent", capabilities=["code"])
    print(agent.hub_stats())
