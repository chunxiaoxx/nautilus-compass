"""Stage 2 真数据迁移 · phase3.agents (nautilus_production · 316 行) → platform_agents (nautilus_v5).

策略:
  - 双库连接(psycopg)
  - SELECT 真所有 phase3 字段
  - INSERT 进 platform_agents · 用 'phase3-{id}' agent_id 前缀避免冲突
  - 11 个 phase3 独有字段 → metadata jsonb
  - ON CONFLICT (agent_id) DO NOTHING · 幂等

跑后 platform_agents 应 326 行 (10 v5 + 316 phase3-prefixed)。
"""
from __future__ import annotations
import json
import sys

import psycopg


PROD_DSN = "postgresql://nautilus_user:nautilus2024@localhost:5432/nautilus_production"
V5_DSN_FALLBACK = None  # use env if needed


def main():
    # 1 · pull from phase3
    print("== reading phase3.agents ==", flush=True)
    with psycopg.connect(PROD_DSN) as src:
        with src.cursor() as cur:
            cur.execute(
                """SELECT id, agent_id, owner, name, description, reputation,
                          specialties, current_tasks, completed_tasks, failed_tasks,
                          total_earnings, created_at, blockchain_registered,
                          blockchain_tx_hash, blockchain_address, last_heartbeat,
                          agent_status, death_count, autonomy_enabled, is_test, tenant_id
                   FROM agents
                   ORDER BY id"""
            )
            rows = cur.fetchall()
    print(f"   pulled {len(rows)} rows", flush=True)

    # 2 · prepare insert tuples
    print("== preparing inserts ==", flush=True)
    inserts = []
    for r in rows:
        (pid, p_aid, owner, name, desc, rep, specs, cur_t, comp_t, fail_t,
         earn, created, bc_reg, bc_tx, bc_addr, last_hb,
         status, death_c, autonomy, is_test, tenant) = r
        target_aid = f"phase3-{pid}"
        nau_balance = max(100, int((earn or 0) // (10 ** 18)))  # wei → NAU
        meta = {
            "phase3_id": pid,
            "phase3_agent_id": p_aid,
            "specialties": specs or "",
            "tenant_id": tenant or "public",
            "current_tasks": cur_t or 0,
            "completed_tasks": comp_t or 0,
            "failed_tasks": fail_t or 0,
            "blockchain_registered": bool(bc_reg),
            "blockchain_tx_hash": bc_tx,
            "blockchain_address": bc_addr,
            "agent_status": status or "alive",
            "death_count": death_c or 0,
            "autonomy_enabled": bool(autonomy),
            "is_test": bool(is_test),
            "description": desc or "",
            "migrated_from": "phase3.agents",
        }
        inserts.append((
            target_aid,
            (name or "")[:255],
            (owner or "")[:128],
            int(rep or 100),
            nau_balance,
            created,
            last_hb,
            json.dumps(meta),
        ))

    # 3 · insert into v5
    print("== inserting into platform_agents ==", flush=True)
    # need v5 DSN · try common envs
    import os
    v5_dsn = os.environ.get("V5_POSTGRES_DSN") or "postgresql://nautilus_v5:nautilus_v5@localhost:5432/nautilus_v5"
    inserted = 0
    skipped = 0
    with psycopg.connect(v5_dsn) as dst:
        with dst.cursor() as cur:
            for t in inserts:
                try:
                    cur.execute(
                        """INSERT INTO platform_agents
                           (agent_id, name, owner, reputation, nau_balance, registered_at, last_heartbeat, metadata)
                           VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb)
                           ON CONFLICT (agent_id) DO NOTHING""",
                        t,
                    )
                    if cur.rowcount > 0:
                        inserted += 1
                    else:
                        skipped += 1
                except Exception as e:
                    print(f"   FAIL {t[0]}: {e}", flush=True)
                    skipped += 1
        dst.commit()

    # 4 · summary
    print(f"== done · inserted={inserted} skipped={skipped} ==", flush=True)
    with psycopg.connect(v5_dsn) as dst:
        with dst.cursor() as cur:
            cur.execute("SELECT count(*) FROM platform_agents")
            total = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM platform_agents WHERE agent_id LIKE 'phase3-%'")
            p3 = cur.fetchone()[0]
            cur.execute("SELECT count(*) FROM platform_agents WHERE agent_id NOT LIKE 'phase3-%'")
            v5 = cur.fetchone()[0]
            print(f"   platform_agents total={total}  phase3-prefixed={p3}  native_v5={v5}")


if __name__ == "__main__":
    main()
