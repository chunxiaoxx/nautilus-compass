"""compass · 把 BioMysteryBench 试点投递包推上飞书多维表格(charter 交付载体)。

复用 feishu_read_via_cloud 的「ssh cloud 白名单 IP + env 传凭据 + 远端 stdlib urllib」代理模式
(治家宽 IP 99991401),扩出**写**能力:create-table + batch-create-records。
建一张专属投递表(镜像买方 problems.csv 列 + 内部答案/溯源/验收列),推 3 行,读回验证。

🔴 保密:内容不含甲方名(买方名从不出现在题面/交付)。内部答案列仅供我方追踪。

用法: python ops/feishu_bmb_deliver.py            # 建表+推送+读回
       python ops/feishu_bmb_deliver.py --dry-run  # 只打印将推送内容,不写飞书
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ops.feishu_read_via_cloud import _load_creds, _shq, SSH_HOST, DEFAULT_BASE  # noqa: E402

DELIVERY = Path(__file__).resolve().parent.parent / "vtf/fde_benchmarks/biomysterybench/_DELIVERY"
TABLE_NAME = "BioMysteryBench_投递_试点_20260717"

# 远端写 payload:stdin 收 {op, base, ...};纯 stdlib;凭据走 env。
_REMOTE_WRITE = r'''
import os, sys, json, urllib.request, urllib.error
API="https://open.feishu.cn/open-apis"
req=json.loads(sys.stdin.read())
def http(url,data=None,token=None,method=None):
    h={"Content-Type":"application/json"}
    if token: h["Authorization"]="Bearer "+token
    m=method or ("POST" if data is not None else "GET")
    r=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,headers=h,method=m)
    try:
        with urllib.request.urlopen(r,timeout=30) as resp: return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e: return json.loads(e.read().decode())
tok=http(API+"/auth/v3/tenant_access_token/internal",
         {"app_id":os.environ["FEISHU_APP_ID"],"app_secret":os.environ["FEISHU_APP_SECRET"]}).get("tenant_access_token")
base=req["base"]; op=req["op"]
if op=="create-table":
    fields=[{"field_name":n,"type":1} for n in req["fields"]]
    body={"table":{"name":req["name"],"default_view_name":"Grid","fields":fields}}
    r=http(f"{API}/bitable/v1/apps/{base}/tables",body,token=tok)
    print(json.dumps({"code":r.get("code"),"msg":r.get("msg"),"table_id":r.get("data",{}).get("table_id")}))
elif op=="create-records":
    body={"records":[{"fields":f} for f in req["records"]]}
    r=http(f"{API}/bitable/v1/apps/{base}/tables/{req['table_id']}/records/batch_create",body,token=tok)
    print(json.dumps({"code":r.get("code"),"msg":r.get("msg"),"n":len(r.get("data",{}).get("records",[]))}))
'''


def _remote(payload: dict) -> dict:
    creds = _load_creds()
    cmd = (f"FEISHU_APP_ID='{creds['FEISHU_APP_ID']}' FEISHU_APP_SECRET='{creds['FEISHU_APP_SECRET']}' "
           f"python3 -c \"import sys;exec(sys.argv[1])\" {_shq(_REMOTE_WRITE)}")
    proc = subprocess.run(["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", SSH_HOST, cmd],
                          input=json.dumps(payload), capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=120)
    if proc.returncode != 0:
        sys.exit(f"[err] ssh/remote rc={proc.returncode}: {proc.stderr[:300]}")
    return json.loads(proc.stdout.strip().splitlines()[-1])


def load_rows() -> list[dict]:
    prob = {r["id"]: r for r in csv.DictReader(open(DELIVERY / "problems.csv", encoding="utf-8"))}
    prov = {p["id"]: p for p in json.loads((DELIVERY / "_INTERNAL_provenance.json").read_text(encoding="utf-8"))["problems"]}
    rows = []
    for pid, r in prob.items():
        ak = prov.get(pid, {}).get("answer_key", {})
        rows.append({
            "id": pid,
            "question": r["question"],
            "answer_rubric": r["answer_rubric"],
            "allowed_domains": r["allowed_domains"],
            "human_solvable": r["human_solvable"],
            "内部_答案": f"{ak.get('gene','')}|{ak.get('condition','')}",
            "内部_数据包": f"data/{pid}.zip",
            "内部_验收": "bmb_validator 0 REJECT · 盲解唯一=1",
        })
    return rows


FIELDS = ["id", "question", "answer_rubric", "allowed_domains", "human_solvable",
          "内部_答案", "内部_数据包", "内部_验收"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--base", default=DEFAULT_BASE)
    a = ap.parse_args()
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass

    rows = load_rows()
    print(f"载入 {len(rows)} 题:{[r['id'] for r in rows]}")
    if a.dry_run:
        for r in rows:
            print(f"  {r['id']} · 答案={r['内部_答案']} · Q={r['question'][:60]}...")
        print("(dry-run,不写飞书)")
        return 0

    print(f"建表 '{TABLE_NAME}' @ base {a.base} ...")
    ct = _remote({"op": "create-table", "base": a.base, "name": TABLE_NAME, "fields": FIELDS})
    if ct.get("code") != 0:
        sys.exit(f"[err] 建表失败: {ct}")
    tid = ct["table_id"]
    print(f"  ✅ table_id={tid}")

    print(f"推送 {len(rows)} 行 ...")
    cr = _remote({"op": "create-records", "base": a.base, "table_id": tid, "records": rows})
    if cr.get("code") != 0:
        sys.exit(f"[err] 推送失败: {cr}")
    print(f"  ✅ 写入 {cr['n']} 行")

    # 读回验证(独立验证非自报)
    from ops.feishu_read_via_cloud import read_records, table_row_count
    n = table_row_count(tid, base=a.base)
    rb = read_records(tid, limit=5, base=a.base)
    print(f"\n读回验证:表 {tid} 共 {n} 行")
    for rec in rb.get("records", []):
        print(f"  · {rec.get('id')} · human_solvable={rec.get('human_solvable')} · 内部答案={rec.get('内部_答案')}")
    print(f"\n✅ BioMysteryBench 试点投递已上飞书:base={a.base} table={tid}({TABLE_NAME})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
