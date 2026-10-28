"""fuel writeback 函件对账工具(2026-10-05)。

背景:flywheel writeback 改走 org_mailbox 函件通道(标题 [writeback:fuel_verify]),
POST 端点 10-04 后零调用,v5 三源实证缺口 30 行;发送端幂等键跨批重复撞
org_mailbox 唯一键致批量 500。

本工具做两件事:
1. 表升级:补 final_patch_present / env_ready 两列(带正文的 POST 行自此有落点);
2. 对账(--audit):解析函件判定面,对照表内已有 traj_id,输出缺口清单——
   不做半截 INSERT(trajectory 列 NOT NULL 且正文不在函内,占位文本会污染
   下游训练环消费)。正文缺口由数据持有方(flywheel POST per-row 或 v5 按
   r78 配方代写)闭合。

用法(云端):
    set -a; source ~/nautilus-mvp/phase3/backend/.env; set +a
    python3 ops/fuel_writeback_audit.py [--dry-run]
    --dry-run = 不执行 ALTER,只输出对账 JSON
"""
from __future__ import annotations

import ast
import json
import os
import sys

import psycopg2

TITLE_PREFIX = "[writeback:fuel_verify]"


def main() -> int:
    dry = "--dry-run" in sys.argv
    dsn = os.environ.get("DATABASE_URL", "postgresql://nautilus_user@localhost:5432/nautilus_production")
    conn = psycopg2.connect(dsn)
    cur = conn.cursor()

    cur.execute(
        """SELECT body FROM org_mailbox
           WHERE to_agent='platform' AND title LIKE %s AND body IS NOT NULL
           ORDER BY created_at""",
        (TITLE_PREFIX + "%",),
    )
    rows = cur.fetchall()

    parsed, missing, bad_body, dup = [], [], [], []
    for (body,) in rows:
        try:
            p = ast.literal_eval(body.strip())
            qid = p["qid"]
        except (ValueError, KeyError, SyntaxError):
            bad_body.append(body[:80])
            continue
        if qid in [m["qid"] for m in parsed]:
            dup.append(qid)
            continue
        parsed.append({"qid": qid, "verdict": p.get("verdict"),
                       "file": p.get("file"), "sha16": p.get("sha16")})
        cur.execute("SELECT 1 FROM fuel_trajectories WHERE traj_id=%s", (qid,))
        if not cur.fetchone():
            missing.append(qid)

    if not dry:
        cur.execute("""ALTER TABLE fuel_trajectories
            ADD COLUMN IF NOT EXISTS final_patch_present boolean,
            ADD COLUMN IF NOT EXISTS env_ready text""")
        conn.commit()

    cur.execute("SELECT count(*) FROM fuel_trajectories")
    total = cur.fetchone()[0]
    print(json.dumps({"parsed": len(parsed), "missing_in_table": len(missing),
                      "missing_qids": missing, "bad_body": len(bad_body),
                      "dup_in_letters": dup, "table_total": total, "dry_run": dry},
                     ensure_ascii=False, indent=1))
    cur.close()
    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
