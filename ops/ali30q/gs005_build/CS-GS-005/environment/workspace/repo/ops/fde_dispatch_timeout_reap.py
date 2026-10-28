#!/usr/bin/env python3
"""fde_dispatch claimed-timeout reaper(2026-06-18·platform turf·解孤儿堆积根因）。
consumer claim 后卡 >Nh 不推进 → 双分支自清:
  claimed + 有 output  → status=produced（尊重已产·让 scorer settle）
  claimed + 无 output  → status=open, 清 claim（re-claimable）
真 OS cron 1h 跑。env FDE_DISPATCH_TIMEOUT_HOURS（默认 2）。
"""
import os, sys
import psycopg
from datetime import datetime

DSN = os.environ.get("DATABASE_URL", "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production").replace("postgresql+asyncpg:", "postgresql:")

def main():
    h = int(os.environ.get("FDE_DISPATCH_TIMEOUT_HOURS", "2"))
    n_prod = n_open = 0
    with psycopg.connect(DSN, connect_timeout=10) as c:
        with c.cursor() as cu:
            cu.execute(f"""UPDATE fde_dispatch SET status='produced'
                WHERE status='claimed' AND output IS NOT NULL
                  AND claimed_at < NOW() - INTERVAL '{h} hours' RETURNING task_uid""")
            n_prod = len(cu.fetchall())
            cu.execute(f"""UPDATE fde_dispatch SET status='open', claimed_by=NULL, claimed_at=NULL
                WHERE status='claimed' AND output IS NULL
                  AND claimed_at < NOW() - INTERVAL '{h} hours' RETURNING task_uid""")
            n_open = len(cu.fetchall())
        c.commit()
    print(f"[fde-dispatch-reap] {datetime.now().isoformat()} · timeout={h}h · ->produced {n_prod} · ->open {n_open}")

if __name__ == "__main__":
    main()
