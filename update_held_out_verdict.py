"""update_held_out_verdict.py · 真写 buyer 表 14 行 held_out_verdict 字段
走 PATCH /bitable/v1/apps/{app_token}/tables/{table_id}/records/{record_id}
"""
import json, sys
sys.path.insert(0, "/home/ubuntu/fde-toolbox")
from feishu_client import tenant_token, _req, BASE

APP = "KY9ZbC2Qqa6ZZXsKrWyc5VGRnXe"
TBL = "tblQAW4aNM99nva6"

# load our results
rows = [json.loads(l) for l in open("/home/ubuntu/doubao_held_out/doubao_held_out.jsonl") if l.strip()]

def verdict_for(p):
    if p <= 0.4: return "KILLED"  # very hard
    if p <= 0.6: return "PROVEN_HARD"  # hard but not killed
    return "PROVEN_EASY"  # easy

# 但 buyer 表 held_out_verdict 取值固定 PROVEN/KILLED/PENDING
# 按 charter 钉死 pass@5 <= 0.6 = 难倒标 = KILLED
# 实际买方的"难倒"口径为模型在该题上 ≤ 0.6 · 故 hard=True 标 KILLED · hard=False 标 PROVEN
results = []
for r in rows:
    rec_id = r["record_id"]
    p5 = r["pass_at_5"]
    hard = r["hard_flag"]
    # buyer held_out_verdict:PROVEN/KILLED/PENDING · §1.3 hard=pass@5<=0.6
    # KILLED = 难倒(doubao 折在这题)
    verdict = "KILLED" if hard else "PROVEN"
    fields = {"held_out_verdict": verdict}
    # PATCH via _req
    token = tenant_token()
    url = f"{BASE}/bitable/v1/apps/{APP}/tables/{TBL}/records/{rec_id}"
    resp = _req("PUT", url, token, body={"fields": fields})
    results.append((rec_id, r["task_id"], verdict, p5, hard, resp.get("code"), resp.get("msg","")))
    print(f"rec={rec_id} {r['task_id']}: {verdict} (pass@5={p5} hard={hard}) -> code={resp.get('code')} msg={resp.get('msg','')[:80]}")

# save log
with open("/home/ubuntu/doubao_held_out/feishu_update_log.json","w") as f:
    json.dump([{"rec": r[0], "task": r[1], "verdict": r[2], "pass5": r[3], "hard": r[4],
                "code": r[5], "msg": r[6]} for r in results], f, indent=2)
print(f"\n=== updated {len(results)} records ===")