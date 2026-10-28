# Schema 融合 Stage 3 真终结 · V5 → nautilus_production 单库

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 把 V5 的 31 platform_* 表合并到 nautilus_production · V5 改 DSN · 实现真单库 SoT(不是双向桥 · 不是 view UNION) · phase3 backend 几乎不动。

**Architecture:** 反向合并(V5 → phase3 库) · 比正向(phase3 → V5 库) 工作量小 5 倍。原因:V5 platform_* 表 30 全独立(无重名)· phase3 backend ORM 不需要改 · 只需 V5 改 .env 一行。冲突点只 1 个:`platform_metrics_snapshots` schema 微差(id int vs bigint · health_score double vs int)· 30min 内 reconcile。

**Tech Stack:** PostgreSQL 14 · pg_dump/restore · psycopg · systemd · ssh cloud

---

## Context · 真现状(2026-05-06 audit)

### Schema 对比
| 库 | 表数 | 关键真心脏 |
|---|---|---|
| nautilus_production (phase3) | 56 | agents 316 · tasks 31 · oauth/users/wallets/raid 完整 |
| nautilus_v5 | 31 | platform_agents 326(已 mirror phase3 + native v5) · platform_bounties 533 · platform_nau_ledger 204 · agent_tool_calls 110 · atoms 11104 · platform_proposals 53 · platform_audit 403 |

### 重名表(冲突)= 1 个
**`platform_metrics_snapshots`** — 双方都有 · schema 微差:
| 字段 | phase3 (nautilus_production) | v5 (nautilus_v5) |
|---|---|---|
| id | integer | **bigint** |
| snapshot_time | nullable | **not null** |
| health_score | double precision | **integer** |
| created_at | 有 | **无** |

reconcile 决策:**采纳 V5 schema 更严** + 加回 created_at(向后兼容 phase3 cron)。

### 独立表
- V5 独有:30 platform_* + agent_tool_calls + atoms + vec_atoms = 33 表 · 全无 phase3 名字冲突
- phase3 独有:55 表(tasks/users/wallets/raid_*/oauth_* 等) · V5 不需要 · 不动

### V5 真心脏数据(必须 0 丢)
- 326 platform_agents(包含 316 phase3-prefixed + 10 native v5 · Stage 2 已合并)
- 533 platform_bounties · 204 platform_nau_ledger · 110 agent_tool_calls · 11104 atoms

---

## Risks & Mitigations

**R1 · platform_metrics_snapshots 冲突 schema 不兼容**
- 缓解:Task 4 用真 ALTER 合并 · 双方旧 cron 都能跑(测试 phase3 P0.1 metric push + V5 daemon snapshot)
- 缓解:数据 dedupe 用 (snapshot_time, metrics::text MD5) 唯一性

**R2 · V5 改 DSN 后 production 真 down**
- 缓解:Task 7 atomic cutover · DSN 改 + restart 一条命令 · 失败 < 30s 回滚
- 缓解:Task 0 先 backup 双库 · pg_dump 全量

**R3 · sequence ID 冲突(bigint vs integer + 起始 ID)**
- 缓解:Task 4 用 setval 重设 sequence 起点 · 避免 phase3 P0.1 cron 与 V5 daemon 写入抢 ID

**R4 · V5 ORM 写入 nautilus_production 缺权限**
- 缓解:Task 2 GRANT ALL ON 31 V5 表给 nautilus_user · V5 改用 nautilus_user/nautilus2024 DSN

**R5 · 仍有未发现的隐藏依赖(view / FK / trigger)**
- 缓解:Task 1 真 audit(\\d \\df \\dv) · 写入 _tmp_patch/v5_dependencies.txt · 0 隐藏才进 Task 3

---

## Verification Plan

### Functional
- V5 daemon restart · 真连 nautilus_production · journalctl 0 ERROR · 30s
- V5 真 cycle 推进 · 选 1 工具 + 真写 platform_audit + 真扣 NAU
- phase3 backend 真启动(若 enable)· 看 platform_metrics_snapshots 真写入
- 326 platform_agents 真完整 · 533 platform_bounties 真完整

### Performance
- V5 cycle 时延 p99 < 5s(原本 2-4s · 跨库切换可接受)
- nautilus_production 连接数 < 30(双方共用)

### Rollback
- 保留 nautilus_v5 库 7 天 · 任何故障 V5 改回原 DSN 即活

---

## Tasks · 真实施(总估时 ~2h · 单 session 可成)

### Task 0 · 双库真 backup(15min)

**Files:**
- Create: `/tmp/backup_2026_05_06_stage3/nautilus_production_full.sql`
- Create: `/tmp/backup_2026_05_06_stage3/nautilus_v5_full.sql`
- Create: `/tmp/backup_2026_05_06_stage3/nautilus_v5_schema_only.sql`

**Step 1: SSH cloud · 真 pg_dump 双库**

```bash
ssh cloud 'mkdir -p /tmp/backup_2026_05_06_stage3 && \
  PGPASSWORD=nautilus2024 pg_dump -h 127.0.0.1 -U nautilus_user nautilus_production > /tmp/backup_2026_05_06_stage3/nautilus_production_full.sql && \
  PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 pg_dump -h 127.0.0.1 -U nautilus_v5 nautilus_v5 > /tmp/backup_2026_05_06_stage3/nautilus_v5_full.sql && \
  PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 pg_dump -h 127.0.0.1 -U nautilus_v5 -s nautilus_v5 > /tmp/backup_2026_05_06_stage3/nautilus_v5_schema_only.sql'
```

**Step 2: 验证大小合理**
```bash
ssh cloud 'ls -lh /tmp/backup_2026_05_06_stage3/'
# expect: nautilus_v5_full.sql > 5MB (含 11104 atoms) · nautilus_production_full.sql > 1MB
```

**Step 3: Commit**
```bash
git add docs/plans/2026-05-06-schema-fusion-stage3-final.md
git commit -m "plan: schema fusion stage 3 final · V5 → nautilus_production"
```

---

### Task 1 · 隐藏依赖 audit(15min)

**Files:**
- Create: `_tmp_patch/v5_dependencies.txt`

**Step 1: 列 V5 库所有 view / function / FK / trigger**

```bash
ssh cloud 'PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 psql -h 127.0.0.1 -U nautilus_v5 -d nautilus_v5 -c "
SELECT '\''view'\'' as kind, schemaname || '\''.'\'' || viewname as name FROM pg_views WHERE schemaname='\''public'\''
UNION ALL
SELECT '\''function'\'', n.nspname || '\''.'\'' || p.proname FROM pg_proc p JOIN pg_namespace n ON p.pronamespace=n.oid WHERE n.nspname='\''public'\''
UNION ALL
SELECT '\''trigger'\'', tgname FROM pg_trigger WHERE NOT tgisinternal
UNION ALL
SELECT '\''fk'\'', conname FROM pg_constraint WHERE contype='\''f'\'' AND connamespace=(SELECT oid FROM pg_namespace WHERE nspname='\''public'\'')
"' | tee _tmp_patch/v5_dependencies.txt
```

**Step 2: 0 dependency 验证 · 否则 Task 4 必须额外迁**
```
expect: 仅 platform_metrics_snapshots 相关 · 0 跨表 FK · 0 view · 0 trigger
```

---

### Task 2 · V5 schema dump + reconcile metrics_snapshots(20min)

**Files:**
- Create: `_tmp_patch/v5_schema_filtered.sql` · 不含 platform_metrics_snapshots
- Create: `_tmp_patch/reconcile_metrics_snapshots.sql`

**Step 1: 拆 V5 schema dump · 排除 metrics_snapshots(冲突表)**

```bash
ssh cloud "
  # full dump excluding the conflict table
  PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 pg_dump \
    -h 127.0.0.1 -U nautilus_v5 \
    --no-owner --no-acl \
    --exclude-table=platform_metrics_snapshots \
    nautilus_v5 > /tmp/backup_2026_05_06_stage3/v5_filtered.sql
  ls -lh /tmp/backup_2026_05_06_stage3/v5_filtered.sql
"
```

**Step 2: 写 reconcile 脚本 · 把 phase3 的 platform_metrics_snapshots 升级到 V5 schema**

```sql
-- _tmp_patch/reconcile_metrics_snapshots.sql

BEGIN;

-- Step 1: backup phase3 旧数据
CREATE TABLE IF NOT EXISTS _backup_metrics_snapshots_phase3 AS
  SELECT * FROM platform_metrics_snapshots;

-- Step 2: ALTER 升级到 V5 schema(id bigint · health_score int · snapshot_time not null)
ALTER TABLE platform_metrics_snapshots
  ALTER COLUMN id TYPE bigint,
  ALTER COLUMN snapshot_time SET NOT NULL,
  ALTER COLUMN health_score TYPE integer USING health_score::integer,
  ALTER COLUMN health_score SET NOT NULL,
  ALTER COLUMN health_score SET DEFAULT 50,
  ALTER COLUMN anomalies SET NOT NULL;
-- created_at 留 · phase3 兼容

-- Step 3: setval sequence 避免 V5 import 时 ID 冲突
SELECT setval('platform_metrics_snapshots_id_seq',
  (SELECT COALESCE(MAX(id), 0) FROM platform_metrics_snapshots) + 1000);

COMMIT;
```

**Step 3: 提交脚本**
```bash
git add _tmp_patch/reconcile_metrics_snapshots.sql
git commit -m "patch: stage 3 task 2 · reconcile platform_metrics_snapshots"
```

---

### Task 3 · 真 restore V5 31 表进 nautilus_production(10min)

**Files:**
- Modify: nautilus_production database (add V5 platform_* tables + data)

**Step 1: 在 nautilus_production 跑 reconcile**

```bash
ssh cloud "
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production \
    -f /home/ubuntu/nautilus-core/_tmp_patch/reconcile_metrics_snapshots.sql
"
```

**Step 2: scp reconcile + V5 dump 文件 到 cloud(若不存)** (本地写完已 scp)

**Step 3: psql 真 import V5 31 表(不含 metrics_snapshots)**

```bash
ssh cloud "
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production \
    < /tmp/backup_2026_05_06_stage3/v5_filtered.sql 2>&1 | tail -30
"
```

**Step 4: 单独迁 platform_metrics_snapshots 数据(append V5 数据进 phase3 表)**

```bash
ssh cloud "
  PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 pg_dump \
    -h 127.0.0.1 -U nautilus_v5 \
    --data-only --table=platform_metrics_snapshots \
    --no-owner nautilus_v5 \
    | grep -v '^SET\\|^SELECT pg_catalog' \
    > /tmp/backup_2026_05_06_stage3/v5_metrics_data.sql
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production \
    < /tmp/backup_2026_05_06_stage3/v5_metrics_data.sql 2>&1 | tail -10
"
```

**Step 5: 验证 nautilus_production 真有 V5 数据**

```bash
ssh cloud "
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production -c \"
    SELECT 'agents' as t, count(*) FROM agents
    UNION ALL SELECT 'platform_agents', count(*) FROM platform_agents
    UNION ALL SELECT 'platform_bounties', count(*) FROM platform_bounties
    UNION ALL SELECT 'platform_nau_ledger', count(*) FROM platform_nau_ledger
    UNION ALL SELECT 'agent_tool_calls', count(*) FROM agent_tool_calls
    UNION ALL SELECT 'atoms', count(*) FROM atoms
    UNION ALL SELECT 'platform_audit', count(*) FROM platform_audit;
  \"
"
# expect: agents=316 · platform_agents=326 · platform_bounties=533 · platform_nau_ledger=204 · agent_tool_calls=110 · atoms=11104 · platform_audit=403
```

**Step 6: Commit**
```bash
git commit --allow-empty -m "ops: stage 3 task 3 · V5 31 tables imported into nautilus_production"
```

---

### Task 4 · GRANT 权限给 nautilus_user(5min)

**Step 1: 让 nautilus_user 真拥有 V5 表权限**

```bash
ssh cloud "
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production -c \"
    GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO nautilus_user;
    GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO nautilus_user;
  \"
"
```

---

### Task 5 · V5 改 DSN 切到 nautilus_production · atomic cutover(10min)

**Files:**
- Modify: `/home/ubuntu/nautilus-v5/.env` (V5_POSTGRES_DSN)
- Modify: `/etc/systemd/system/nautilus-v5-singleton.service` env file 引用(若有)

**Step 1: 真改 V5 .env**

```bash
ssh cloud "
  sudo cp /home/ubuntu/nautilus-v5/.env /home/ubuntu/nautilus-v5/.env.bak.stage3
  sudo sed -i 's|V5_POSTGRES_DSN=.*|V5_POSTGRES_DSN=postgresql://nautilus_user:nautilus2024@127.0.0.1:5432/nautilus_production|' /home/ubuntu/nautilus-v5/.env
  grep V5_POSTGRES_DSN /home/ubuntu/nautilus-v5/.env
"
```

**Step 2: restart V5 daemon**

```bash
ssh cloud "
  sudo systemctl restart nautilus-v5-singleton
  sleep 5
  sudo systemctl is-active nautilus-v5-singleton
  sudo journalctl -u nautilus-v5-singleton -n 30 --no-pager 2>&1 | tail -30
"
# expect: active · 0 ERROR
```

**Step 3: 真 V5 cycle 验证(30s 内 1 cycle)**

```bash
ssh cloud "
  sleep 30
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production -c \"
    SELECT count(*) FROM platform_audit WHERE created_at > NOW() - interval '2 minutes';
  \"
"
# expect: ≥ 1 (V5 真写到 platform_audit)
```

**Step 4: Commit**
```bash
git commit --allow-empty -m "ops: stage 3 task 5 · V5 DSN cutover · single SoT in nautilus_production"
```

---

### Task 6 · phase3 backend 验证(若 enable · 5min)

**注:** phase3 backend nautilus-backend.service 当前 stop · 这步只验证 import 不崩。完整启动留 plan/memoized-coalescing-diffie.md(需 ORM 大改)。

**Step 1: 看 phase3 是否能 import 全部 model**

```bash
ssh cloud "
  cd /home/ubuntu/nautilus-mvp/phase3/backend
  python3 -c 'from models.database import Agent, Tenant, User; print(\"phase3 ORM 真 import 成功\")' 2>&1
"
```

**Step 2: 如有 import 错 · 留 memory · 不阻塞 cutover**(本 plan 范围:V5 真单库 SoT)

---

### Task 7 · 真 fdw 桥撤销 + 旧 unified_agents view 清理(10min)

**注:** 既然 V5 + phase3 共库 nautilus_production · postgres_fdw 桥 + unified_agents view 都不需要了。

**Step 1: 删 nautilus_v5 里的 phase3_remote schema(原 fdw)**

```bash
ssh cloud "
  PGPASSWORD=be85b6d692ceae2a0d9b50d7a02c8156 psql -h 127.0.0.1 -U nautilus_v5 -d nautilus_v5 -c \"
    DROP SCHEMA IF EXISTS phase3_remote CASCADE;
    DROP EXTENSION IF EXISTS postgres_fdw CASCADE;
  \" 2>&1 | tail -5
"
```

**Step 2: 删 nautilus_production 里的 v5_remote schema + unified_agents view**

```bash
ssh cloud "
  PGPASSWORD=nautilus2024 psql -h 127.0.0.1 -U nautilus_user -d nautilus_production -c \"
    DROP VIEW IF EXISTS unified_agents CASCADE;
    DROP SCHEMA IF EXISTS v5_remote CASCADE;
  \" 2>&1 | tail -5
"
```

**Step 3: phase3 backend api/agents.py 删除我之前加的 /unified endpoint(中间方案)**

```bash
# 用 Python file patcher 删除 marker block
python3 _tmp_patch/strip_unified_endpoint.py
scp ... agents.py
```

(脚本另写 · 简单 marker delete)

---

### Task 8 · Memory + 真 commit + 状态更新(15min)

**Files:**
- Create: `~/.claude/projects/.../memory/session_20260506_schema_fusion_stage3_complete.md`
- Modify: `MEMORY.md`

**Step 1: 写真 memory · 不再"真"过度**

```markdown
---
name: session_20260506_schema_fusion_stage3_complete
description: "2026-05-06 schema fusion stage 3 完成 · V5 31 表合进 nautilus_production · V5 改 DSN · 单库 SoT 真活"
type: project
---

## 真完成
- V5 31 表(31 platform_* + agent_tool_calls + atoms + vec_atoms - 1 重名 reconcile = 30 dump + 1 alter)真 import nautilus_production
- platform_metrics_snapshots schema reconcile · 升级到 V5 严 schema · phase3 旧数据 backup 留
- V5 改 DSN 真切到 nautilus_user@nautilus_production
- nautilus-v5-singleton.service 重启 · 真 active · 真 cycle 推进
- 双向 fdw 桥真撤(phase3_remote / v5_remote schema 删)
- unified_agents view 真删(中间方案不再用)
- nautilus_v5 库降级为 backup · 7 天后真删

## 真验证
- platform_audit 30s 内有真新 row(V5 真写 nautilus_production)
- 326 platform_agents · 533 bounties · 11104 atoms · 全数据真无丢

## Why · How to apply
- 用户原话"应该真正融合而不是双向桥" — 单库 SoT 是真终结
- 反向合并(V5 → phase3 库) 比正向(phase3 → V5 库) 工作量小 5 倍
- phase3 ORM 不需改 · V5 改 DSN 一行
```

**Step 2: 更新 MEMORY.md 加入 Stage 3 entry**

**Step 3: Commit + push**
```bash
git add memory/ docs/plans/ _tmp_patch/
git commit -m "feat: schema fusion stage 3 final · V5 → nautilus_production single SoT"
git push origin master
```

---

## Done Definition

- [ ] V5 systemd active · 0 ERROR · 真连 nautilus_production
- [ ] V5 真 cycle 推进 · platform_audit 真新 row
- [ ] 326 platform_agents · 533 bounties · 11104 atoms 真完整
- [ ] phase3 backend ORM 真无 import 错
- [ ] fdw 桥 + unified_agents view 真撤
- [ ] nautilus_v5 库保留 7 天 backup · 然后真删
- [ ] memory + MEMORY.md 真写 · git commit + push

---

## Out of Scope

- phase3 backend 真启动 17 cron(需 docs/plans/memoized-coalescing-diffie.md Stage 2-7 大改 ORM · 留下次 session)
- phase3 schema 升级到 platform_* 表名(纯命名不动 · 不影响真融合)
- nautilus_v5 库真删(7 天 cooldown)
