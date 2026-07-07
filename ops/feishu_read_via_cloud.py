"""compass · 经 cloud 白名单 IP 中转读飞书多维表格(治家宽 IP 被 app 白名单拒 code 99991401)。

背景(2026-07-07 收敛执法 grounded):飞书 app 开了 IP 白名单,compass 家宽 IP 直读 →
`HTTP 400 code=99991401 "ip <IP> is denied by app setting"`(token 照拿到 · base token 没错)。
cloud egress IP(43.160.239.61)在白名单。本模块把"ssh cloud 跑远端 urllib"这条已验证路径
封装成可复用 helper,未来 compass 读飞书透明走 cloud,不再重新发现 IP 白名单坑(anchor #5/#6)。

凭据:本机金库 `~/.claude/.cache/.fde_api_secrets.env` 的 FEISHU_APP_ID/SECRET,经 ssh 远端 env
传入(不落 cloud 盘 · 不进本进程 argv 以外)。远端只跑 stdlib urllib,无需 cloud 装任何东西。

用法:
    python ops/feishu_read_via_cloud.py list-tables
    python ops/feishu_read_via_cloud.py count <table_id>
    python ops/feishu_read_via_cloud.py rows <table_id> [--limit N]
    # 库用:from ops.feishu_read_via_cloud import list_tables, table_row_count
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

VAULT = Path(os.path.expanduser("~/.claude/.cache/.fde_api_secrets.env"))
SSH_HOST = os.environ.get("COMPASS_CLOUD_SSH", "cloud")
# FDE 管理 base(RGDK · v06 培训链)· 与 feishu_admin.py FDE_RGDK_BASE 一致
DEFAULT_BASE = os.environ.get("FDE_RGDK_BASE", "RGDKbrtZ1aMcEOsZ2GcczeFknNg")

# 远端 payload:读金库无法(creds 走 env),纯 stdlib。stdin 收 {op,base,table_id,limit}。
_REMOTE = r'''
import os, sys, json, urllib.request, urllib.error
API="https://open.feishu.cn/open-apis"
req=json.loads(sys.stdin.read())
def http(url,data=None,token=None):
    h={"Content-Type":"application/json"}
    if token: h["Authorization"]="Bearer "+token
    r=urllib.request.Request(url,data=json.dumps(data).encode() if data is not None else None,
                             headers=h,method="POST" if data is not None else "GET")
    try:
        with urllib.request.urlopen(r,timeout=25) as resp: return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e: return json.loads(e.read().decode())
tok=http(API+"/auth/v3/tenant_access_token/internal",
         {"app_id":os.environ["FEISHU_APP_ID"],"app_secret":os.environ["FEISHU_APP_SECRET"]}).get("tenant_access_token")
base=req["base"]; op=req["op"]
if op=="list-tables":
    b=http(f"{API}/bitable/v1/apps/{base}/tables?page_size=100",token=tok)
    print(json.dumps({"code":b.get("code"),"msg":b.get("msg"),
                      "items":[{"table_id":t["table_id"],"name":t["name"]} for t in b.get("data",{}).get("items",[])]}))
elif op=="count":
    r=http(f"{API}/bitable/v1/apps/{base}/tables/{req['table_id']}/records?page_size=1",token=tok)
    print(json.dumps({"code":r.get("code"),"msg":r.get("msg"),"total":r.get("data",{}).get("total")}))
elif op=="rows":
    r=http(f"{API}/bitable/v1/apps/{base}/tables/{req['table_id']}/records?page_size={req.get('limit',10)}",token=tok)
    d=r.get("data",{})
    print(json.dumps({"code":r.get("code"),"msg":r.get("msg"),"total":d.get("total"),
                      "records":[it.get("fields",{}) for it in d.get("items",[])]},ensure_ascii=False,default=str))
'''


def _load_creds() -> dict:
    """从本机金库读 FEISHU_APP_ID/SECRET(strip 防 CRLF · 见 feishu_client CRLF 教训)。"""
    creds = {}
    if not VAULT.exists():
        sys.exit(f"[err] 金库不存在: {VAULT}")
    for line in VAULT.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        if k.strip() in ("FEISHU_APP_ID", "FEISHU_APP_SECRET"):
            creds[k.strip()] = v.strip()
    if "FEISHU_APP_ID" not in creds or "FEISHU_APP_SECRET" not in creds:
        sys.exit("[err] 金库缺 FEISHU_APP_ID/SECRET")
    return creds


def _run(op: str, base: str | None = None, table_id: str | None = None,
         limit: int = 10) -> dict:
    """经 cloud 跑一次远端读。creds 经 ssh 远端 env 传(不落盘)。"""
    creds = _load_creds()
    base = base or DEFAULT_BASE
    payload = json.dumps({"op": op, "base": base, "table_id": table_id, "limit": limit})
    # 远端命令:env 赋值 + python3 从 stdin 收 payload。凭据在远端 shell 一次性 env,不写文件。
    remote_cmd = (
        f"FEISHU_APP_ID='{creds['FEISHU_APP_ID']}' "
        f"FEISHU_APP_SECRET='{creds['FEISHU_APP_SECRET']}' "
        f"python3 -c \"import sys,os;exec(sys.argv[1])\" {_shq(_REMOTE)}"
    )
    proc = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", SSH_HOST, remote_cmd],
        input=payload, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=90)
    if proc.returncode != 0:
        sys.exit(f"[err] ssh/remote fail rc={proc.returncode}: {proc.stderr[:300]}")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception as e:  # noqa: BLE001
        sys.exit(f"[err] 远端输出非 JSON: {e} · raw={proc.stdout[:300]}")


def _shq(s: str) -> str:
    """单引号包裹用于 ssh 远端 shell 的 python 源码参数。"""
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ------------------------------------------------------------------ 库 API
def list_tables(base: str | None = None) -> dict:
    return _run("list-tables", base=base)


def table_row_count(table_id: str, base: str | None = None) -> int | None:
    return _run("count", base=base, table_id=table_id).get("total")


def read_records(table_id: str, limit: int = 10, base: str | None = None) -> dict:
    return _run("rows", base=base, table_id=table_id, limit=limit)


def main(argv=None) -> int:
    try:  # Windows 控制台默认 GBK · 飞书内容含 emoji/中文 → 强制 UTF-8 输出(errors=replace 兜底)
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    ap = argparse.ArgumentParser(description="经 cloud 白名单 IP 读飞书(治 99991401)")
    ap.add_argument("op", choices=["list-tables", "count", "rows"])
    ap.add_argument("table_id", nargs="?")
    ap.add_argument("--base", default=None)
    ap.add_argument("--limit", type=int, default=10)
    a = ap.parse_args(argv)
    if a.op in ("count", "rows") and not a.table_id:
        ap.error(f"{a.op} 需要 table_id")
    res = _run(a.op, base=a.base, table_id=a.table_id, limit=a.limit)
    print(json.dumps(res, indent=2, ensure_ascii=False, default=str))
    return 0 if res.get("code") in (0, None) else 1


if __name__ == "__main__":
    sys.exit(main())
