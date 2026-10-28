"""Submit 5 GenOpt RL tasks to S3 交付表 (DLR) via cloud SSH 中转.

DLR (Delivery Ledger Record) — GenOpt 第 3 类机密交付 (S3 base
Dx2qb1fjhaJadSs0ZeMc0teVn49, table_id=tblFkmEKTk4LIWJM).
12 columns:
  task_uid, title, domain, instance_count, baseline_score, reference_score,
  best_score, gap_closed, difficulty, deliverable_url, status, closed_at

Run on cloud (43.160.239.61:24860) via SSH.
"""

import os
import sys

import openpyxl

sys.path.insert(0, os.path.expanduser("~"))
import feishu_client  # noqa: E402

XLSX_PATH = os.path.expanduser("~/genopt_rl_5tasks_20260703.xlsx")
APP_TOKEN = "Dx2qb1fjhaJadSs0ZeMc0teVn49"  # S3 机密交付 base
TABLE_ID = "tblFkmEKTk4LIWJM"                  # S3 交付表


def xlsx_to_dlr_rows(xlsx_path):
    """Read 14+2 col xlsx, yield DLR fields per task.

    5 grounded real values (7/3 0:55 + v7 二次标定) are HARDCODED here
    to avoid xlsx re-parsing that may carry stale values; the xlsx
    authoritative source is the same xlsx we just submitted to S1.
    """
    GROUNDED = {
        # task_uid → (baseline, reference, best, gap, difficulty)
        "genopt_or_jobshop_orlib_v1_001_20260702":       (24.68, 90.50, 94.89, 0.7022, "Easy"),
        "genopt_or_tsp_tsplib_v1_001_20260702":          (89.51, 99.83, 100.00, 0.1048, "Hard"),
        "genopt_ke_attention_flash_v1_001_20260702":    (0.87,  8.73,  23.06,  0.2293, "Hard"),
        "genopt_cs_cache_lru_v1_001_20260702":          (0.00,  11.42, 10.92,  0.1092, "Hard"),
        "genopt_or_bin_packing_ffd_v1_001_20260702":    (0.00,  66.67, 66.67,  0.6667, "Easy"),
    }
    DOMAIN = {
        "genopt_or_jobshop_orlib_v1_001_20260702":      "operations_research_and_decision_science",
        "genopt_or_tsp_tsplib_v1_001_20260702":         "operations_research_and_decision_science",
        "genopt_ke_attention_flash_v1_001_20260702":   "kernel_engineering_and_systems",
        "genopt_cs_cache_lru_v1_001_20260702":         "computer_systems",
        "genopt_or_bin_packing_ffd_v1_001_20260702":   "operations_research_and_decision_science",
    }
    INSTANCES = {
        "genopt_or_jobshop_orlib_v1_001_20260702":      6,
        "genopt_or_tsp_tsplib_v1_001_20260702":         6,
        "genopt_ke_attention_flash_v1_001_20260702":   4,
        "genopt_cs_cache_lru_v1_001_20260702":         5,
        "genopt_or_bin_packing_ffd_v1_001_20260702":   5,
    }
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
        title = r[idx.get("题目", 1)] or ""
        b, ref, best, gap, diff = GROUNDED[uid]
        out.append({
            "task_uid": uid,
            "标题": title,
            "domain": DOMAIN[uid],
            "instance_count": INSTANCES[uid],
            "baseline_score": b,
            "reference_score": ref,
            "best_score": best,
            "gap_closed": gap,
            "difficulty": diff,
            "deliverable_url": f"genopt_factory/tasks/{uid.replace('genopt_', '').rsplit('_', 1)[0]}/",
            "状态": "已交付",
            "closed_at": "2026-07-03T00:55:00Z",
        })
    return out


def main():
    rows = xlsx_to_dlr_rows(XLSX_PATH)
    print(f"[read] {XLSX_PATH} → {len(rows)} DLR rows")
    for r in rows:
        print(f"  + {r['task_uid']}  diff={r['difficulty']}  gap={r['gap_closed']}")
    tok = feishu_client.tenant_token()
    print(f"\n[OK] tenant_access_token (前6 {tok[:6]}...)")
    success = 0
    failures = []
    for fields in rows:
        try:
            resp = feishu_client.create_bitable_record(APP_TOKEN, TABLE_ID, fields, tok)
            code = resp.get("code", -1)
            if code == 0:
                rid = resp.get("data", {}).get("record", {}).get("record_id", "?")
                print(f"  [OK] {fields['task_uid']} → record_id={rid}")
                success += 1
            else:
                msg = resp.get("msg", "?")
                print(f"  [err] {fields['task_uid']} code={code} msg={msg}")
                failures.append((fields['task_uid'], code, msg))
        except Exception as exc:
            print(f"  [exc] {fields['task_uid']}: {exc}")
            failures.append((fields['task_uid'], "exception", str(exc)))
    print(f"\n[summary] {success}/{len(rows)} inserted; {len(failures)} failed")
    if failures:
        for uid, code, msg in failures:
            print(f"  - {uid}: code={code} msg={msg}")
    return 0 if not failures else 2


if __name__ == "__main__":
    sys.exit(main())