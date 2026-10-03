"""R84 智星云余额+实例状态探针(只读)。"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/c/Users/chunx/.workbuddy/ai-galaxy-compute/src")
from ai_galaxy_compute.client import AIGalaxyClient  # noqa: E402

_creds = json.loads(
    (Path.home() / ".config/ai-galaxy-compute/credentials.json").read_text()
)
client = AIGalaxyClient(_creds["access_key"], _creds["secret_key"])

print("=== main_account ===")
print(json.dumps(client.get_main_account_info(), ensure_ascii=False, default=str)[:800])
print("=== instance lyg1132 ===")
try:
    d = client.get_instance_detail("lyg1132")
    print(json.dumps(d, ensure_ascii=False, default=str)[:1200])
except Exception as e:
    print("detail FAIL:", e)
    print("=== instance_list p1 ===")
    lst = client.get_instance_list(page=1)
    print(json.dumps(lst, ensure_ascii=False, default=str)[:1500])
