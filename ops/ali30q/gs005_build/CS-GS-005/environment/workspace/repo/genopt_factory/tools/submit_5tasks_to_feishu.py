"""Submit 5 GenOpt RL tasks to Feishu bitable via cloud SSH 中转 (anchors #3 + #5).

Reads genopt_rl_5tasks_20260703.xlsx (14+2 col buyer format) and inserts
5 rows into the FDE派活表 S1 (table_id=tbl69fankpoBhJfw, app=EOVhbQwA0a1HEOsgmxecgkBVnwh).

Run on cloud (43.160.239.61:24860) via SSH, where the IP is in the
Feishu app whitelist (the local IP 216.36.114.95 added 2026-06-09 is no
longer valid as of 7/3 — current local IP 1.192.64.248 is denied).
"""

import json
import os
import sys

import openpyxl

sys.path.insert(0, os.path.expanduser("~"))  # so feishu_client.py imports
import feishu_client  # noqa: E402


XLSX_PATH = os.path.expanduser("~/genopt_rl_5tasks_20260703.xlsx")
APP_TOKEN = "EOVhbQwA0a1HEOsgmxecgkBVnwh"  # FDE派活表 S1
TABLE_ID = "tbl69fankpoBhJfw"                  # 派活表 (10 列 task_uid/标题/业务线/...)


def xlsx_to_fields(xlsx_path):
    """Read 14+2 col xlsx and yield (uid, fields_dict) per row.

    Maps 14+2 buyer columns to FDE派活表 10 columns (per memory:
    FDE派活表 schema = task_uid/标题/业务线/一级类目/三级领域/L级/指派专家/
    验收标准/状态/备注).
    """
    wb = openpyxl.load_workbook(xlsx_path, read_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    headers = rows[0]
    idx = {h: i for i, h in enumerate(headers) if h}
    out = []
    for r in rows[1:]:
        if not r[idx.get("UID", 0)]:
            continue
        uid = r[idx["UID"]]
        # Map buyer 14 col → FDE 派活表 10 col
        fields = {
            "task_uid": uid,
            "标题": r[idx.get("题目", 1)] or "",
            "业务线": "GenOpt",                                # buyer #3 类:基准测试
            "一级类目": "投资、战略、专业服务与企业经营",       # closest fixed class
            "三级领域": r[idx.get("题目领域三级目录", 4)] or "",
            "L级": r[idx.get("任务类型", 14)] or "L3",
            "指派专家": "platform-soul",                          # author=platform
            "验收标准": r[idx.get("打分checklist（必填）", 15)] or
                       r[idx.get("做题关键步骤（可选）", 13)] or "",
            "状态": "待派单",                                  # 初始状态
            "备注": r[idx.get("任务概括", 5)] or "",
        }
        out.append((uid, fields))
    return out


def main():
    rows = xlsx_to_fields(XLSX_PATH)
    if not rows:
        print("[err] no rows in xlsx", file=sys.stderr)
        return 1
    print(f"[read] {XLSX_PATH} → {len(rows)} rows")
    for uid, fields in rows:
        print(f"  + {uid}")
        for k, v in fields.items():
            print(f"      {k} = {str(v)[:60]}")
    # Pre-check token
    tok = feishu_client.tenant_token()
    print(f"\n[OK] tenant_access_token 获取 (前6 {tok[:6]}...)")
    # Insert each row
    success = 0
    failures = []
    for uid, fields in rows:
        try:
            resp = feishu_client.create_bitable_record(APP_TOKEN, TABLE_ID, fields, tok)
            code = resp.get("code", -1)
            if code == 0:
                rid = resp.get("data", {}).get("record", {}).get("record_id", "?")
                print(f"  [OK] {uid} → record_id={rid}")
                success += 1
            else:
                msg = resp.get("msg", "?")
                print(f"  [err] {uid} code={code} msg={msg}")
                failures.append((uid, code, msg))
        except Exception as exc:
            print(f"  [exc] {uid}: {exc}")
            failures.append((uid, "exception", str(exc)))
    print(f"\n[summary] {success}/{len(rows)} inserted; {len(failures)} failed")
    if failures:
        for uid, code, msg in failures:
            print(f"  - {uid}: code={code} msg={msg}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())