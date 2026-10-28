# HANDOFF #015 · Slice B sentinel followup · fresh session 入口

**写于**: 2026-05-29 session 4 收尾(Path A + B + D + Slice B HTTP-only ~4-5h)
**为**: 下个 fresh session
**默认主线**: Path B-followup(Slice B sentinel 真闭环)

---

## 🎯 Fresh-session 第 1 句 prompt(paste 用)

最短:
```
接 handoff #015 · Slice B sentinel followup · 1 migration + daemon P2 wire + sentinel test · ~1h
```

完整:
```
接 handoff #015 · 默认 Path B-followup 主线 · Slice B sentinel 真闭环:
1. ALTER agent_dispatch_log ADD COLUMN task_spec TEXT NOT NULL DEFAULT ''
2. api/soul.py dispatch 也存 task_spec
3. goal_stack._next_p2_agent_dispatch 返 task_spec field
4. daemon.run_once call select_goal_with_source · P2-shape adapter · _emit_goal_source_to_latest_cycle + _mark_dispatch_shipped helpers
5. test_daemon_picks_p2_dispatch sentinel
开 worktree + TDD + PR
```

候选其他 path 见下方 §4.

---

## 1. 当前真状态

- master tip: `e5f9d58a7` (PR #75 Inc 2 closeout 最新)
- cloud `~/nautilus-mvp` HEAD: 含 Slice 5+6+A code · backend live · 8 nautilus failed systemd → 0
- cloud `~/nautilus-soul-workspace` HEAD: `a31236bb2` 5/28 · daemon.py + goal_stack.py 已 scp 到 Slice A 接线 helpers · 但 `run_once` 未 wire
- 5 PR:
  - **#75 ✅ MERGED** Inc 2 closeout
  - **#76 ✅ MERGED** Inc 3 Slice A
  - **#79 ⏳ draft** dashboard heartbeat 500→200 fix(9 lines · low-risk)
  - **#80 ⏳ draft** daemon 自驱 P3 self-improve(sentinel attempt 副产物 · 看 spec 决定)
  - **#81 ⏳ draft** Slice B HTTP-only(270 LOC · 6 tests)

---

## 2. 关键 gotchas(踩过的坑 · 不再踩)

1. **Slice A wiring 仅 helpers** · `daemon.run_once` line 345 仍 call `goal_selector.select_goal()` · 不是 end-to-end · 不要再写 "Slice A BINDING-DONE"
2. **cloud 双 workspace** · `nautilus-mvp` 跑 backend · `nautilus-soul-workspace` 跑 daemon · sync 须双向
3. **"Nobody is using" 硬编码** · 出自 `phase3/backend/services/pairs/mind.py:154-155` · 不是 emergent signal · 不要拿来当 anchor 信号
4. **anchor #5 列名复发 6+ 次** · 每次 SQL 前先 `\d <table>` · 不猜:
   - `platform_agents` PK = `agent_id` varchar(128) 不是 `id`
   - `platform_nau_ledger` 用 `delta` int 不是 `direction`
   - `pending_nau_rewards` 用 `status` 不是 `source_type`
   - `platform_agent_keys` 只有 `key_hash` 没有 `api_key_hash`/`plaintext_key`
5. **`backend is-active` ≠ HTTP 200** · sync-agent-engine.sh pre-step 慢启动 · sleep ≥ 8s 后再 probe HTTP
6. **systemctl mask 不能 mask 已有 unit file** · 用 `disable timer + reset-failed service` 替代
7. **dashboard.py edit 不要用 python heredoc + 单引号 + triple-string 嵌套** · scp 本地 + Edit tool + scp 回 · 上次自爆 backend HTTP 000

---

## 3. Slice B sentinel followup 详细 plan(默认主线)

### 3.1 Migration

```python
# phase3/backend/alembic/versions/<rev>_inc3_slice_b_task_spec_col.py
"""inc3 slice B · agent_dispatch_log.task_spec column

Revision: <auto>
Revises: a1b2c3d4e5f6
"""
from alembic import op

def upgrade():
    op.execute(
        "ALTER TABLE agent_dispatch_log "
        "ADD COLUMN IF NOT EXISTS task_spec TEXT NOT NULL DEFAULT ''"
    )

def downgrade():
    op.execute("ALTER TABLE agent_dispatch_log DROP COLUMN IF EXISTS task_spec")
```

加 `scripts/cloud_apply_inc3_slice_b_followup.sh` raw-SQL bypass(anchor #5 模式)

### 3.2 api/soul.py 修

```python
# _insert_agent_dispatch_log signature 加 task_spec
def _insert_agent_dispatch_log(
    *, db, agent_id, task_spec, task_spec_hash, task_type
) -> int:
    res = db.execute(
        text("INSERT INTO agent_dispatch_log "
             "(agent_id, task_spec, task_spec_hash, task_type) "
             "VALUES (:aid, :spec, :hash, :tt) RETURNING id"),
        {"aid": agent_id, "spec": task_spec, "hash": task_spec_hash, "tt": task_type},
    )
    ...

# soul_dispatch handler 传 body.task_spec
row_id = _insert_agent_dispatch_log(
    db=db, agent_id=agent_id, task_spec=body.task_spec,
    task_spec_hash=task_spec_hash, task_type=body.task_type,
)
```

### 3.3 goal_stack.py 修

```python
def _next_p2_agent_dispatch():
    ...
    cur.execute(
        "SELECT id, agent_id, task_spec, task_spec_hash, task_type "
        "FROM agent_dispatch_log WHERE ship_outcome IS NULL "
        "ORDER BY created_at ASC LIMIT 1"
    )
    row = cur.fetchone()
    ...
    return {
        "id": f"dispatch-{row[0]}",
        "agent_id": row[1],
        "task_spec": row[2],          # NEW
        "task_spec_hash": row[3],
        "task_type": row[4] or "code",
    }
```

### 3.4 daemon.py wiring(关键)

```python
# 替换 line 345
goal_tuple = select_goal_with_source()
goal, source = goal_tuple if goal_tuple else (None, None)

# P2 goal 没 description 字段 · 用 task_spec 补
if source is not None and source.value == "p2_agent_dispatch":
    goal["description"] = goal["task_spec"]

# 流程后续不变(yaml-path ship)
# After PR opened · 加 2 个 emit:
url = pr_gate.create_draft_pr(branch, pr_title, body)
_emit_goal_source_to_latest_cycle(source)
if source and source.value == "p2_agent_dispatch":
    dispatch_id = int(goal["id"].split("-")[1])
    _mark_dispatch_shipped(dispatch_id, outcome="shipped", cycle_id=url)
```

加 2 helpers:

```python
def _emit_goal_source_to_latest_cycle(source):
    """Update most-recent engine_cycle_outcomes row created in last 5 min."""
    if source is None: return
    dsn = os.getenv("DATABASE_URL")
    if not dsn: return
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "UPDATE engine_cycle_outcomes SET goal_source = %s "
            "WHERE cycle_id = (SELECT cycle_id FROM engine_cycle_outcomes "
            "WHERE goal_source IS NULL AND created_at > NOW() - INTERVAL '5 minutes' "
            "ORDER BY created_at DESC LIMIT 1)",
            (source.value,)
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("emit_goal_source failed: %s", exc)

def _mark_dispatch_shipped(dispatch_id, outcome, cycle_id):
    """UPDATE agent_dispatch_log row · marks P2 row consumed."""
    dsn = os.getenv("DATABASE_URL")
    if not dsn: return
    try:
        import psycopg2
        conn = psycopg2.connect(dsn)
        cur = conn.cursor()
        cur.execute(
            "UPDATE agent_dispatch_log SET ship_outcome = %s, cycle_id = %s "
            "WHERE id = %s",
            (outcome, cycle_id, dispatch_id)
        )
        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning("mark_dispatch_shipped failed: %s", exc)
```

### 3.5 Sentinel test

```python
# phase3/soul/tests/test_daemon_picks_p2_dispatch.py
def test_daemon_run_once_picks_p2_when_yaml_empty(monkeypatch):
    fake_p2 = {"id": "dispatch-99", "task_spec": "Add docstring", "task_spec_hash": "abc"*8 + "x"*40, "task_type": "code", "agent_id": 9000002}
    monkeypatch.setattr("soul.goal_stack._next_p1_governance", lambda: None)
    monkeypatch.setattr("soul.goal_stack._next_p2_agent_dispatch", lambda: fake_p2)
    ...
    # mock _load_engine + ship + pr_gate
    # assert _emit_goal_source_to_latest_cycle called with P2_AGENT_DISPATCH
    # assert _mark_dispatch_shipped called with 99
```

### 3.6 Cloud verify(BINDING-DONE)

```bash
# 1. apply migration on cloud
ssh cloud "cd ~/nautilus-mvp && bash scripts/cloud_apply_inc3_slice_b_followup.sh"

# 2. scp daemon.py + goal_stack.py to BOTH workspaces
scp daemon.py cloud:~/nautilus-mvp/phase3/soul/daemon.py
scp daemon.py cloud:~/nautilus-soul-workspace/phase3/soul/daemon.py
scp goal_stack.py cloud:~/nautilus-mvp/phase3/soul/goal_stack.py
scp goal_stack.py cloud:~/nautilus-soul-workspace/phase3/soul/goal_stack.py

# 3. scp soul.py (dispatch handler)
scp api/soul.py cloud:~/nautilus-mvp/phase3/backend/api/soul.py

# 4. restart backend
ssh cloud "sudo systemctl restart nautilus-backend && sleep 10"

# 5. INSERT sentinel dispatch row with REAL task_spec
ssh cloud 'PGPASSWORD=nautilus2024 psql ... INSERT ... task_spec='\''Add docstring to phase3/soul/__init__.py · MINIMAL CHANGE'\'' ...'

# 6. trigger daemon
ssh cloud "sudo systemctl start nautilus-soul.service"

# 7. wait 60s + verify
ssh cloud 'sleep 60 && PGPASSWORD=... psql -c "SELECT cycle_id, goal_source FROM engine_cycle_outcomes ORDER BY created_at DESC LIMIT 1;"'
# expect: goal_source = 'p2_agent_dispatch'

ssh cloud 'PGPASSWORD=... psql -c "SELECT id, ship_outcome, cycle_id FROM agent_dispatch_log WHERE id = <sentinel-id>;"'
# expect: ship_outcome != NULL, cycle_id != NULL
```

BINDING-DONE 4 criteria:
- ✅ migration applied · task_spec col exists
- ✅ sentinel test PASS local
- ✅ goal_source = 'p2_agent_dispatch' on engine_cycle_outcomes
- ✅ agent_dispatch_log row ship_outcome populated

预计 ~30-40 LOC + 1 migration + 1 test + cloud verify · ~1-1.5h

---

## 4. 候选其他 path

| Path | 触发条件 |
|---|---|
| **5 PR cleanup**(快 · 30min)| 用户要先收 PR 再开新 |
| Slice C(`config` task type)| 用户决定 B-followup defer · 跳到下个 task type 试水 |
| Slice D(`schema-migration` + INBOUND)| user 决定跳过 Slice C |
| Path D-action(unpause customer)| user 改变 5/27 pivot · option α/β/γ |
| Path B-extra(GRANT view + raid-trigger 复查)| user 澄清 GRANT view 具体 anomaly |

---

## 5. R3 / anchor 提醒

- R3 4h: 本 session 已 4-5h 软越界 · 下 session fresh 计时
- anchor #2: option δ 维持 · 客户 timing 归用户 · 不主动 unpause
- anchor #3: B-followup 是 product loop 推进 · 不是 D 维护(closes Slice A wiring gap)
- anchor #5: SQL 前 `\d <table>` 验列名 · 已复发 6+ 次
- anchor #6: dashboard "Nobody" 是硬编码 · 不当 emergent signal

---

## 6. Parking lot(不开新 session 处理)

- inc3-soul-engine 物理 worktree dir cleanup(cwd-lock · 任一 fresh session 开头 `rm -rf` 即可)
- nautilus-mvp vs nautilus-soul-workspace 单 source-of-truth 决策(架构层面)
- pairs/mind.py 硬编码 dialogue 是否改 data-driven
- platform-health-monitor 是否砍 heartbeat check(若 PR #79 merge 后)
