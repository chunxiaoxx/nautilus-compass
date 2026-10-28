"""拉 org/bootstrap 七节包概要(核对四框目标栈+协同件在产状态)"""
import json
import urllib.request

with urllib.request.urlopen(
        "http://127.0.0.1:8000/api/platform/org/bootstrap", timeout=15) as r:
    d = json.loads(r.read())

data = d.get("data", d)
print("顶层键:", list(data.keys()))
for k, v in data.items():
    if isinstance(v, dict):
        print(f"  {k}: keys={list(v.keys())[:10]}")
    elif isinstance(v, list):
        print(f"  {k}: {len(v)} 项; 首项样例={json.dumps(v[0], ensure_ascii=False)[:200] if v else '[]'}")
    else:
        print(f"  {k}: {json.dumps(v, ensure_ascii=False)[:200]}")
