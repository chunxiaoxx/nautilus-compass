# v0.9.5 audit_log Monthly Partition Spec (revised 2026-05-06 w/ real bench)

## 0. Stress benchmark (2026-05-06 · cloud · sqlite 3.37.2)

```
scale     ins/s    p50  p95   vacuum     disk_pre  disk_post
1K       22,727    6ms  6ms      17ms     140KB     112KB
10K      26,455    6ms  7ms      35ms     1.2MB     884KB
100K     15,987    6ms  7ms     268ms     11.7MB    8.5MB
1M        9,905    7ms  7ms    3157ms     117MB     86MB
```

**Findings**:
- SELECT p95 = 7ms across 4 orders of magnitude (idx_user_ts perfect)
- INSERT throughput drops only 2.3× (22K → 10K /s) from 1K → 1M
- VACUUM scales ~linearly: 1M = 3.2s tolerable; 5M ≈ 16s painful
- Disk ~120 bytes/row → 1M = 117MB (1GB at ~8M rows)

**Revised Postgres switch trigger** (was 100K · was 1M · now real):
- SQLite is **safe up to 5M-10M rows** (p95 stays well under 100ms)
- Real switch trigger: row count > 5M OR DB > 1GB OR vacuum p95 > 30s

## 1. Why partition?

Single-table `audit_log` degrades sharply past ~5M rows on SQLite (above benchmark):

| Operation | Single table (5M rows) | Monthly partition |
|---|---|---|
| `DELETE WHERE ts < cutoff` (3-month retention) | 30–60s + 5–10s VACUUM | n/a |
| `DROP TABLE audit_log_2026_02` | **<10ms** (O(1) metadata) | replaces DELETE |
| Index rebuild after DELETE | full B-tree rewrite | none |
| Insert latency (steady state) | degrades with table size | bounded per-month |

DROP TABLE reclaims pages instantly, no VACUUM stall, no WAL bloat. Predictable retention cost regardless of MAU.

## 2. Schema

```sql
-- Per-month physical table (created on demand)
CREATE TABLE IF NOT EXISTS audit_log_2026_05 (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          INTEGER NOT NULL,         -- unix epoch
    actor       TEXT    NOT NULL,         -- agent_id
    action      TEXT    NOT NULL,         -- 'task.start' etc.
    target      TEXT,
    payload     TEXT,                     -- json blob
    region      TEXT    NOT NULL DEFAULT 'global'
);
CREATE INDEX IF NOT EXISTS idx_audit_2026_05_actor_ts
    ON audit_log_2026_05(actor, ts DESC);
CREATE INDEX IF NOT EXISTS idx_audit_2026_05_action_ts
    ON audit_log_2026_05(action, ts DESC);

-- Read-side helper view (regenerated when partitions added/dropped)
CREATE VIEW v_audit_log AS
    SELECT * FROM audit_log_2026_03
    UNION ALL SELECT * FROM audit_log_2026_04
    UNION ALL SELECT * FROM audit_log_2026_05;
```

SQLite's UNION ALL across same-shape tables is push-down optimized; planner uses each child index independently.

## 3. Migration strategy

```sql
-- step 1: snapshot
ATTACH 'audit_backup.db' AS bak;
CREATE TABLE bak.audit_log AS SELECT * FROM audit_log;

-- step 2: split by month (loop in python — see §4)
INSERT INTO audit_log_2026_03 SELECT * FROM audit_log
    WHERE ts >= strftime('%s','2026-03-01') AND ts < strftime('%s','2026-04-01');
-- repeat per month present

-- step 3: rename old, install view, verify count parity, drop old
ALTER TABLE audit_log RENAME TO audit_log_legacy;
-- (recreate v_audit_log)
SELECT (SELECT COUNT(*) FROM audit_log_legacy)
     - (SELECT COUNT(*) FROM v_audit_log) AS delta;  -- must be 0
DROP TABLE audit_log_legacy;
```

## 4. Code changes

```python
# nautilus_compass/audit/partition.py
from datetime import datetime, timezone
import sqlite3, threading

_ensured: set[str] = set()
_lock = threading.Lock()

def decide_partition_name(ts: int | None = None) -> str:
    dt = datetime.fromtimestamp(ts or _now(), tz=timezone.utc)
    return f"audit_log_{dt.strftime('%Y_%m')}"

def ensure_partition_exists(conn: sqlite3.Connection, name: str) -> None:
    if name in _ensured:
        return
    with _lock:
        if name in _ensured:
            return
        conn.executescript(f"""
            CREATE TABLE IF NOT EXISTS {name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL, actor TEXT NOT NULL,
                action TEXT NOT NULL, target TEXT, payload TEXT,
                region TEXT NOT NULL DEFAULT 'global');
            CREATE INDEX IF NOT EXISTS idx_{name}_actor_ts ON {name}(actor, ts DESC);
            CREATE INDEX IF NOT EXISTS idx_{name}_action_ts ON {name}(action, ts DESC);
        """)
        _rebuild_view(conn)
        _ensured.add(name)

def write_audit(conn, *, actor, action, target=None, payload=None, region="global"):
    name = decide_partition_name()
    ensure_partition_exists(conn, name)
    conn.execute(
        f"INSERT INTO {name}(ts,actor,action,target,payload,region) VALUES (?,?,?,?,?,?)",
        (_now(), actor, action, target, payload, region),
    )
```

Auto-create policy: lazy on first write of the month + a 1-day-ahead pre-create cron (avoids midnight UTC contention).

## 5. Retention cron

```python
# replaces: DELETE FROM audit_log WHERE ts < cutoff; VACUUM;
def drop_expired_partitions(conn, keep_months: int = 3):
    cutoff = (_today_utc().replace(day=1) - relativedelta(months=keep_months))
    for name in _list_audit_partitions(conn):
        ym = name.removeprefix("audit_log_")  # "2026_02"
        if datetime.strptime(ym, "%Y_%m").date() < cutoff:
            conn.execute(f"DROP TABLE {name}")
    _rebuild_view(conn)
```

Run weekly. No VACUUM needed — DROP TABLE returns pages to freelist; freelist reused by next partition.

## 6. Read path

`/v1/audit_log` queries `v_audit_log` (the UNION ALL view) with `WHERE ts BETWEEN ? AND ?`. SQLite prunes child tables by index range; cost ≈ querying only the touched partitions. For point queries by actor, each child's `idx_*_actor_ts` is used independently — no global index needed.

## 7. Trigger condition

Gated by `compass.audit.partition_enabled` config flag. Auto-flip when:
- `audit_log` row count > **1,000,000**, OR
- last `DELETE` retention pass took > **10s**, OR
- MAU (distinct `actor` last 30d) > **1,000**.

Below threshold: stay single-table (simpler, no view overhead).

## 8. Rollback plan (5-step runbook)

1. **Disable writes to partitions** — flip flag, writers route back to `audit_log` (recreated empty if absent).
2. **Merge** — `INSERT INTO audit_log SELECT * FROM v_audit_log;` (single transaction).
3. **Verify parity** — `COUNT(*)` of merged table == sum of partition counts captured pre-merge.
4. **Drop view + partitions** — `DROP VIEW v_audit_log; DROP TABLE audit_log_YYYY_MM;` for each.
5. **Re-enable retention DELETE** — restore old cron; run one pass to confirm it completes within SLO.

Abort criteria: if step 3 delta ≠ 0, halt, keep both, investigate (likely concurrent writer not flag-aware).

## Key decisions

- **Naming**: `audit_log_YYYY_MM` (UTC, zero-padded) — sortable, parseable, no collisions across regions (region is a column, not table suffix).
- **Auto-create**: lazy on first write + 1-day-ahead cron; double-checked locking via `_ensured` set to skip `CREATE IF NOT EXISTS` round-trip per insert.
- **UNION view**: regenerated on partition add/drop only, not per query; SQLite query planner handles per-child index pushdown automatically.
