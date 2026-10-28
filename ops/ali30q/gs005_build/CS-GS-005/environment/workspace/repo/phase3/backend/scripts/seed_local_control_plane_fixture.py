"""本地 demo fixture · 灌代表性真数据进 control-plane 读的 4 张表(Task 0).

GET /api/platform/control-plane 的 soul.verdicts / soul.rsi_deltas / dmas.agents /
dmas.bids / compass.poi / pulse 全部 fail-soft:本地 postgres 5433(db=nautilus)
这些表为空(或不存在)→ 端点返空结构、脉搏全 0。舰桥 demo 需要看到**代表性真
数据**(非全 0)。本脚本按 control-plane 实际查的表名/列(读 api/platform_rsi_fde.py
的 _verdicts_section/_agents_section/_events_section + models/fde_rsi_delta.py)
CREATE TABLE IF NOT EXISTS 这 4 张表的最小 schema,并 INSERT 代表性行。

🔴 这是**本地 demo fixture · 非生产**。计数比照 2026-06-06 生产核实的真实分布
(fde_verdicts 7 行 6pass/1fail·events bounty/marketing·agents alive/active/
archived/dead·rsi_delta radix +0.0734 escapes=True),但行本身是 demo 数据。
绝不连 cloud、绝不改生产。

幂等:CREATE TABLE IF NOT EXISTS + 固定 id / 唯一键 + ON CONFLICT DO NOTHING,
重复跑是 no-op(不会重复插、不会报错)。

跑法:
    cd phase3/backend && python scripts/seed_local_control_plane_fixture.py
然后验证(另开终端):
    python scripts/run_control_plane_local.py   # port 8077
    curl -s http://127.0.0.1:8077/api/platform/control-plane | python -m json.tool

DB:postgresql+psycopg2://postgres:postgres@127.0.0.1:5433/nautilus(PGCLIENTENCODING=UTF8)。
可用 CONTROL_PLANE_LOCAL_DB_URL 覆盖(与 run_control_plane_local.py 同源)。
连不上 → 打印错误并退出非 0(不静默)。
"""
from __future__ import annotations

import json
import os
import sys

os.environ.setdefault("PGCLIENTENCODING", "UTF8")

import psycopg2  # noqa: E402

# 与 run_control_plane_local.py 同默认(本地 5433 · 免密 postgres/postgres)。
_DSN = os.getenv(
    "CONTROL_PLANE_LOCAL_DB_URL",
    "postgresql://postgres:postgres@127.0.0.1:5433/nautilus",
).replace("postgresql+psycopg2://", "postgresql://")


# ── DDL · 最小 schema(只含 control-plane SQL / ORM 读的列)──────────────────
_DDL = [
    # fde_verdicts · _verdicts_section 读 verdict_id/task_uid/source/overall_pass/
    #   veto_failed/score/created_at/id(+ ORM 全列对齐 models/fde_verdict.py)。
    """
    CREATE TABLE IF NOT EXISTS fde_verdicts (
        id            SERIAL PRIMARY KEY,
        verdict_id    VARCHAR(200) UNIQUE NOT NULL,
        task_uid      VARCHAR(120) NOT NULL,
        source        VARCHAR(32)  NOT NULL,
        checklist_uid VARCHAR(200),
        overall_pass  BOOLEAN NOT NULL DEFAULT FALSE,
        veto_failed   BOOLEAN NOT NULL DEFAULT FALSE,
        score         DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        items         JSONB,
        artifacts     JSONB,
        created_at    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # platform_external_events · _events_section 读 target/event_type/processed_at/
    #   created_at/id(raw table·非 ORM·与 test fixture 同形)。
    """
    CREATE TABLE IF NOT EXISTS platform_external_events (
        id           SERIAL PRIMARY KEY,
        target       TEXT,
        event_type   TEXT,
        processed_at TIMESTAMP,
        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    # agents · _agents_section 只 GROUP BY agent_status(最小列即可)。
    """
    CREATE TABLE IF NOT EXISTS agents (
        id             BIGINT PRIMARY KEY,
        agent_status   VARCHAR(32),
        last_heartbeat TIMESTAMP
    )
    """,
    # fde_rsi_deltas · _rsi_deltas_section 用 ORM(FdeRsiDelta)·必须含全列(to_dict)。
    """
    CREATE TABLE IF NOT EXISTS fde_rsi_deltas (
        id              SERIAL PRIMARY KEY,
        delta_id        VARCHAR(200) UNIQUE NOT NULL,
        benchmark       VARCHAR(120) NOT NULL,
        task_uid        VARCHAR(120) NOT NULL,
        producer_model  VARCHAR(80),
        n_bare          INTEGER NOT NULL DEFAULT 0,
        n_grounded      INTEGER NOT NULL DEFAULT 0,
        bare_mean       DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        grounded_mean   DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        delta_reward    DOUBLE PRECISION NOT NULL DEFAULT 0.0,
        p_value         DOUBLE PRECISION,
        escapes_noise   BOOLEAN NOT NULL DEFAULT FALSE,
        grounding_source JSONB,
        created_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """,
]


# ── 代表性 fixture 行 ─────────────────────────────────────────────────────────
# fde_verdicts:7 行 · 6 pass / 1 fail · source 全 'fde-capsule-v5'(生产真实 source)。
_VERDICTS = [
    # (verdict_id, task_uid, source, overall_pass, veto_failed, score)
    ("fde-fixture-data_001", "data_001", "fde-capsule-v5", True,  False, 1.0),
    ("fde-fixture-data_002", "data_002", "fde-capsule-v5", True,  False, 1.0),
    ("fde-fixture-data_003", "data_003", "fde-capsule-v5", False, True,  0.45),
    ("fde-fixture-data_004", "data_004", "fde-capsule-v5", True,  False, 0.91),
    ("fde-fixture-data_005", "data_005", "fde-capsule-v5", True,  False, 0.87),
    ("fde-fixture-data_006", "data_006", "fde-capsule-v5", True,  False, 0.95),
    ("fde-fixture-data_007", "data_007", "fde-capsule-v5", True,  False, 0.82),
]

# platform_external_events:代表 bounty_completed / marketing_published / audit_settled。
# 固定 id(9_000_001+)保证幂等。部分 processed(processed_at NOT NULL)。
_EVENTS = []
_eid = 9_000_001
for _i in range(10):  # 10 × bounty_completed
    _EVENTS.append((_eid, "compass-dialog", "bounty_completed",
                    _i % 2 == 0))  # 半数已处理
    _eid += 1
for _i in range(5):   # 5 × marketing_published
    _EVENTS.append((_eid, "compass-dialog", "marketing_published",
                    _i % 2 == 0))
    _eid += 1
_EVENTS.append((_eid, "soul-dialog", "audit_settled", True))  # 1 × audit_settled

# agents:代表性分布(alive/active/archived/dead/suspended)· 固定 id(9_100_001+)。
_AGENT_DIST = [("alive", 6), ("active", 3), ("archived", 5),
               ("dead", 4), ("suspended", 1)]
_AGENTS = []
_aid = 9_100_001
for _status, _n in _AGENT_DIST:
    for _ in range(_n):
        _AGENTS.append((_aid, _status))
        _aid += 1

# fde_rsi_deltas:radix 那条 · ΔReward +0.0734 · escapes_noise=True(RSI 首个真外部增量)。
_RSI_DELTAS = [
    {
        # 口径与 services/control_plane_loops.py 的 radix 回放对齐(单一真相·防自相矛盾)。
        "delta_id": "rsi-fixture-radix_sort-001",
        "benchmark": "autolab_radix_sort",
        "task_uid": "radix_sort",
        "producer_model": "deepseek-chat",
        "n_bare": 13,
        "n_grounded": 13,
        "bare_mean": 0.1835,
        "grounded_mean": 0.2568,
        "delta_reward": 0.0734,
        "p_value": 0.0215,
        "escapes_noise": True,
        "grounding_source": {"corpus": "autolab_avoid_radix_sort", "round": 1,
                             "policy": "correctness-first", "note": "fixture demo"},
    },
]


def main() -> int:
    print(f"[fixture] connecting {_DSN.split('@')[-1]} ...")
    try:
        conn = psycopg2.connect(_DSN, connect_timeout=5)
    except Exception as exc:  # noqa: BLE001
        print(f"[fixture] DB connect FAILED: {exc}")
        return 2
    conn.autocommit = False
    inserted = {"fde_verdicts": 0, "platform_external_events": 0,
                "agents": 0, "fde_rsi_deltas": 0}
    try:
        cur = conn.cursor()

        # 1) DDL · CREATE TABLE IF NOT EXISTS(幂等)。
        for ddl in _DDL:
            cur.execute(ddl)

        # 2) fde_verdicts(ON CONFLICT verdict_id DO NOTHING)。
        for vid, task, src, op, veto, score in _VERDICTS:
            cur.execute(
                "INSERT INTO fde_verdicts "
                "(verdict_id, task_uid, source, overall_pass, veto_failed, score, items, artifacts) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s::jsonb) "
                "ON CONFLICT (verdict_id) DO NOTHING",
                (vid, task, src, op, veto, score, "[]", "{}"),
            )
            inserted["fde_verdicts"] += cur.rowcount

        # 3) platform_external_events(固定 id · ON CONFLICT id DO NOTHING)。
        for eid, target, etype, processed in _EVENTS:
            cur.execute(
                "INSERT INTO platform_external_events "
                "(id, target, event_type, processed_at, created_at) "
                "VALUES (%s,%s,%s, CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END, CURRENT_TIMESTAMP) "
                "ON CONFLICT (id) DO NOTHING",
                (eid, target, etype, processed),
            )
            inserted["platform_external_events"] += cur.rowcount

        # 4) agents(固定 id · ON CONFLICT id DO NOTHING)。
        for aid, status in _AGENTS:
            cur.execute(
                "INSERT INTO agents (id, agent_status, last_heartbeat) "
                "VALUES (%s,%s,NULL) ON CONFLICT (id) DO NOTHING",
                (aid, status),
            )
            inserted["agents"] += cur.rowcount

        # 5) fde_rsi_deltas(ON CONFLICT delta_id DO NOTHING)。
        for d in _RSI_DELTAS:
            cur.execute(
                "INSERT INTO fde_rsi_deltas "
                "(delta_id, benchmark, task_uid, producer_model, n_bare, n_grounded, "
                " bare_mean, grounded_mean, delta_reward, p_value, escapes_noise, grounding_source) "
                "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s::jsonb) "
                "ON CONFLICT (delta_id) DO NOTHING",
                (d["delta_id"], d["benchmark"], d["task_uid"], d["producer_model"],
                 d["n_bare"], d["n_grounded"], d["bare_mean"], d["grounded_mean"],
                 d["delta_reward"], d["p_value"], d["escapes_noise"],
                 json.dumps(d["grounding_source"])),
            )
            inserted["fde_rsi_deltas"] += cur.rowcount

        conn.commit()
    except Exception as exc:  # noqa: BLE001
        conn.rollback()
        print(f"[fixture] seed FAILED (rolled back): {exc}")
        return 1
    finally:
        conn.close()

    print("[fixture] inserted rows (此次新增 · 重复跑为 0 = 幂等):")
    for tbl, n in inserted.items():
        print(f"    {tbl:28s} +{n}")
    print("[fixture] done · 本地 demo fixture · 非生产。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
