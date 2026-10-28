# Unblock Autonomous Pipeline — Phase 1 感官→决策→行动全链路打通

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Fix the 4 blockages in the existing Observatory→Anomaly→MetaTask→Proposal→Sandbox pipeline so the platform achieves genuine autonomous self-improvement.

**Architecture:** The infrastructure already exists (observatory, event_bus, cron_registry, meta_task_generator, proposal_consensus, sandbox). The problem is pipeline blockages: anomalies don't create meta-tasks, proposals don't get approved, sandbox experiments don't complete. Fix the wiring, not the plumbing.

**Tech Stack:** Python 3.10, FastAPI, PostgreSQL, Redis (pub/sub), APScheduler

**Current State (2026-04-03):**
- Observatory: 32 snapshots, health 39→67 (improving)
- Proposals: 4 total, 0 approved, 2 pending
- Sandbox: 2 experiments, 0 promoted, 1 rolled back, 1 stuck "running"
- Anomalies: detected but NOT creating meta-tasks
- Event bus: connected but task.created not triggering agent scans

---

### Task 1: Wire Anomaly→MetaTask Auto-Creation

The observatory detects anomalies but `_make_anomaly_detection_fn` only sends Telegram alerts for EXISTING meta-tasks — it never creates NEW ones from anomalies.

**Files:**
- Modify: `phase3/backend/services/cron_registry.py` (lines 195-217, `_make_anomaly_detection_fn`)

**Step 1: Write the failing test**

```python
# tests/test_anomaly_to_meta_task.py
import pytest
from unittest.mock import MagicMock, patch
from services.meta_task_generator import generate_meta_tasks_from_anomalies

def test_anomaly_creates_meta_task():
    db = MagicMock()
    db.execute.return_value.fetchone.return_value = None  # no recent duplicate
    db.execute.return_value.scalar.return_value = 0

    anomalies = [
        {"metric": "task_success_rate", "value": 0.55, "threshold": 0.70, "severity": "high"}
    ]
    created = generate_meta_tasks_from_anomalies(db, anomalies)
    assert len(created) >= 1
    assert "task_success_rate" in created[0]["title"]

def test_anomaly_respects_cooldown():
    db = MagicMock()
    # Simulate recent duplicate exists (within cooldown)
    db.execute.return_value.scalar.return_value = 1

    anomalies = [
        {"metric": "task_success_rate", "value": 0.55, "threshold": 0.70, "severity": "high"}
    ]
    created = generate_meta_tasks_from_anomalies(db, anomalies)
    assert len(created) == 0
```

**Step 2: Run test to verify it fails**

Run: `cd phase3/backend && python -m pytest tests/test_anomaly_to_meta_task.py -v`
Expected: FAIL (function doesn't exist yet)

**Step 3: Implement `generate_meta_tasks_from_anomalies` in meta_task_generator.py**

Add to `phase3/backend/services/meta_task_generator.py`:

```python
def generate_meta_tasks_from_anomalies(db: Session, anomalies: list[dict]) -> list[dict]:
    """Convert observatory anomalies into marketplace meta-tasks with cooldown check."""
    from sqlalchemy import text
    created = []
    for anomaly in anomalies:
        metric = anomaly.get("metric", "")
        template = META_TASK_TEMPLATES.get(metric)
        if not template:
            continue

        cooldown_hours = template.get("cooldown_hours", 24)

        # Check cooldown: skip if same metric meta-task created recently
        existing = db.execute(text(
            "SELECT COUNT(*) FROM academic_tasks "
            "WHERE task_type = 'platform_meta' "
            "AND title LIKE :pattern "
            "AND created_at > NOW() - MAKE_INTERVAL(hours => :hours)"
        ), {"pattern": f"%{metric}%", "hours": cooldown_hours}).scalar()

        if existing and existing > 0:
            logger.info("meta_task_generator: skipping %s (cooldown %dh, %d existing)", metric, cooldown_hours, existing)
            continue

        title = template["title"].format(**anomaly)
        description = template["description"].format(**anomaly)
        task_id = f"meta-{metric}-{int(time.time())}"

        db.execute(text(
            "INSERT INTO academic_tasks (task_id, title, description, task_type, status, "
            "token_reward, marketplace_open) "
            "VALUES (:tid, :title, :desc, 'platform_meta', 'pending', :reward, true)"
        ), {
            "tid": task_id,
            "title": title[:200],
            "desc": description,
            "reward": template.get("reward_nau", 10),
        })
        db.commit()
        created.append({"task_id": task_id, "title": title, "metric": metric})
        logger.info("meta_task_generator: created %s for anomaly %s", task_id, metric)

    return created
```

**Step 4: Update `_make_anomaly_detection_fn` in cron_registry.py to call it**

Replace lines 195-217 with:

```python
def _make_anomaly_detection_fn():
    async def _fn():
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            import json as _json
            db = SessionLocal()
            try:
                # Get latest snapshot anomalies
                row = db.execute(text(
                    "SELECT anomalies FROM platform_metrics_snapshots "
                    "ORDER BY snapshot_time DESC LIMIT 1"
                )).fetchone()

                if not row or not row.anomalies:
                    return

                anomalies_raw = row.anomalies
                if isinstance(anomalies_raw, str):
                    anomalies_raw = _json.loads(anomalies_raw)

                if not anomalies_raw:
                    return

                # Create meta-tasks from anomalies
                from services.meta_task_generator import generate_meta_tasks_from_anomalies
                created = generate_meta_tasks_from_anomalies(db, anomalies_raw)

                if created:
                    titles = "\n".join(f"  • {t['title'][:80]}" for t in created)
                    await _tg_alert(f"🚨 *Observatory → {len(created)} 元任务已创建*\n\n{titles}")
                    logger.info("anomaly_detection: created %d meta-tasks from %d anomalies",
                               len(created), len(anomalies_raw))
            finally:
                db.close()
        except Exception as e:
            logger.error("anomaly_detection failed: %s", e)
    return _fn
```

**Step 5: Run test to verify it passes**

Run: `cd phase3/backend && python -m pytest tests/test_anomaly_to_meta_task.py -v`

**Step 6: Commit**

```bash
git add services/meta_task_generator.py services/cron_registry.py tests/test_anomaly_to_meta_task.py
git commit -m "fix: wire anomaly detection → meta-task auto-creation with cooldown"
```

---

### Task 2: Fix Proposal Auto-Approval for Low-Risk Changes

4 proposals exist, 0 approved. The pipeline stalls because no agents vote. Add auto-approval for proposals that have been pending >24h with no negative votes.

**Files:**
- Modify: `phase3/backend/services/cron_registry.py` (add new cron job)
- Modify: `phase3/backend/services/proposal_consensus.py` (add auto-approve logic)

**Step 1: Write the failing test**

```python
# tests/test_proposal_auto_approve.py
def test_auto_approve_stale_proposal():
    """Proposals pending >24h with no rejection should auto-approve."""
    db = MagicMock()
    # Return 1 stale proposal
    db.execute.return_value.fetchall.return_value = [
        MagicMock(id=1, change_type="task_template", title="test proposal")
    ]

    from services.proposal_consensus import auto_approve_stale_proposals
    approved = auto_approve_stale_proposals(db, stale_hours=24)
    assert approved >= 1
```

**Step 2: Implement in proposal_consensus.py**

```python
def auto_approve_stale_proposals(db: Session, stale_hours: int = 24) -> int:
    """Auto-approve proposals that have been pending with no rejection for stale_hours."""
    from sqlalchemy import text

    stale = db.execute(text(
        "SELECT p.id, p.change_type, p.title FROM platform_improvement_proposals p "
        "WHERE p.status = 'pending' "
        "AND p.created_at < NOW() - MAKE_INTERVAL(hours => :hours) "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM platform_proposal_votes v "
        "  WHERE v.proposal_id = p.id AND v.vote = 'reject'"
        ")"
    ), {"hours": stale_hours}).fetchall()

    approved = 0
    for proposal in stale:
        db.execute(text(
            "UPDATE platform_improvement_proposals SET status='approved', updated_at=NOW() "
            "WHERE id=:id"
        ), {"id": proposal.id})
        db.commit()
        approved += 1
        logger.info("auto_approve: approved stale proposal %s: %s", proposal.id, proposal.title)

    return approved
```

**Step 3: Add cron job to cron_registry.py** (in CRON_JOBS list)

```python
{
    "id": "proposal_auto_approve",
    "trigger": IntervalTrigger(hours=6),
    "description": "自动批准超过24h无反对票的改进提案",
    "budget_seconds": 15,
},
```

And register the function in `start_cron_registry`.

**Step 4: Commit**

```bash
git commit -m "feat: auto-approve stale proposals (>24h, no rejections)"
```

---

### Task 3: Unstick Running Sandbox Experiment

1 experiment is stuck in "running" status. Add a timeout: if running >48h, auto-evaluate and decide promote/rollback.

**Files:**
- Modify: `phase3/backend/services/cron_registry.py` (`_make_sandbox_monitor_fn`)

**Step 1: Check current stuck experiment**

```sql
SELECT id, proposal_id, status, created_at, ends_at
FROM sandbox_experiments WHERE status='running';
```

**Step 2: Add timeout handling in `_make_sandbox_monitor_fn`**

After the existing `get_pending_evaluations` loop, add:

```python
# Force-evaluate stuck experiments (running > 48h)
stuck = db.execute(text(
    "SELECT id FROM sandbox_experiments "
    "WHERE status='running' AND created_at < NOW() - INTERVAL '48 hours'"
)).fetchall()
for exp_row in stuck:
    try:
        finalize_experiment(db, exp_row.id, "rolled_back")
        logger.warning("sandbox_monitor: force-rolled-back stuck experiment %s (>48h)", exp_row.id)
        await _tg_alert(f"⏰ *Sandbox Timeout*: 实验 `{exp_row.id}` 运行超48h，已自动回滚")
    except Exception as e:
        logger.error("sandbox_monitor: force-rollback failed for %s: %s", exp_row.id, e)
```

**Step 3: Commit**

```bash
git commit -m "fix: auto-rollback sandbox experiments stuck >48h"
```

---

### Task 4: Event-Driven Task Routing (task.created → immediate agent scan)

Currently agents poll every 5 minutes. Wire event bus so `task.created` triggers immediate agent scan.

**Files:**
- Modify: `phase3/backend/services/event_handlers.py`

**Step 1: Check existing event handlers**

Read `event_handlers.py` to see what's already registered.

**Step 2: Add handler for task.created → agent scan**

```python
from services.event_bus import on, Events

@on(Events.TASK_CREATED)
async def handle_task_created_agent_scan(payload: dict):
    """Immediately trigger agent scan when new task is created."""
    try:
        from services.agent_autonomy import run_autonomy_cycle
        from utils.database import SessionLocal
        task_type = payload.get("task_type", "unknown")
        logger.info("event: task.created → triggering immediate agent scan for %s", task_type)
        run_autonomy_cycle(SessionLocal)
    except Exception as e:
        logger.warning("handle_task_created_agent_scan failed: %s", e)
```

**Step 3: Ensure task creation emits events**

Check that `POST /api/academic/submit` and meta-task creation emit `task.created` events. If not, add:

```python
from services.event_bus import emit, Events
await emit(Events.TASK_CREATED, {"task_id": task_id, "task_type": task_type})
```

**Step 4: Commit**

```bash
git commit -m "feat: event-driven task routing — immediate agent scan on task.created"
```

---

### Task 5: Verify Full Pipeline End-to-End on Server

Deploy all changes and verify the complete loop runs:

```
Observatory snapshot → anomaly detected → meta-task created →
agent bids → bid accepted → proposal generated →
proposal auto-approved → sandbox experiment →
evaluate → promote/rollback
```

**Step 1: Deploy to server**

```bash
scp services/cron_registry.py services/meta_task_generator.py services/proposal_consensus.py services/event_handlers.py cloud:~/nautilus-mvp/phase3/backend/services/
scp tests/test_anomaly_to_meta_task.py cloud:~/nautilus-mvp/phase3/backend/tests/
ssh cloud "cd ~/nautilus-mvp/phase3/backend && pm2 restart nautilus-backend"
```

**Step 2: Verify cron jobs registered**

```bash
ssh cloud "curl -s https://www.nautilus.social/api/platform/health | python3 -m json.tool"
```

**Step 3: Manually trigger a pipeline run**

```bash
ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 -c \"
from utils.database import SessionLocal
from services.meta_task_generator import generate_meta_tasks_from_anomalies
db = SessionLocal()
# Force an anomaly to test the pipeline
anomalies = [{'metric': 'task_success_rate', 'value': 0.55, 'threshold': 0.70, 'severity': 'high', 'message': 'test'}]
result = generate_meta_tasks_from_anomalies(db, anomalies)
print(f'Created: {result}')
db.close()
\""
```

**Step 4: Monitor the pipeline in real-time**

```bash
ssh cloud "pm2 logs nautilus-backend --lines 50 | grep -E 'observatory|anomaly|meta_task|auto_accept|auto_submit|sandbox'"
```

**Step 5: Commit final verification**

```bash
git commit -m "feat: autonomous pipeline fully wired — Observatory→MetaTask→Proposal→Sandbox"
```

---

## Success Criteria

```
✅ Observatory snapshots running every hour (already working)
✅ Anomalies auto-create meta-tasks (with cooldown dedup)
✅ Meta-tasks get auto-accepted bids (already working)
✅ Proposals auto-generated from meta-tasks (already working)
✅ Stale proposals auto-approved after 24h
✅ Sandbox experiments timeout after 48h
✅ task.created events trigger immediate agent scans
✅ Telegram alerts at each pipeline stage
✅ At least 1 full pipeline cycle completes end-to-end
```

---

*Plan version: 1.0 | Date: 2026-04-03 | Estimated: 2-3 hours*
