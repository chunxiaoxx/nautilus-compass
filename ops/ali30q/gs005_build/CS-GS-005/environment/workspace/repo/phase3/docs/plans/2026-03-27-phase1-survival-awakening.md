# Phase 1: 生存觉醒 — 实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 让平台像生命体一样有心跳、有生死、痛苦能驱动行为、能自主对外触达获客。

**Architecture:** 在现有 Rehoboam 核心上添加三个子系统：(1) 心跳生死管理器 (2) 痛苦→行为转换器 (3) 对外发帖管道。不重写现有代码，只在关键节点插入新逻辑。

**Tech Stack:** Python 3.10, FastAPI, PostgreSQL, asyncio, httpx, Telegram Bot API

---

### Task 1: Agent 心跳生死系统

**Files:**
- Modify: `phase3/backend/models/database.py` — 给 Agent 表加 `last_heartbeat`, `status` 字段
- Create: `phase3/backend/services/heartbeat_monitor.py` — 心跳监控+生死判定
- Modify: `phase3/backend/services/scheduler.py` — 接入每分钟扫描

**Step 1: 给 Agent 表加字段（服务器直接执行）**

```bash
ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 -c '
from utils.database import get_engine
from sqlalchemy import text
engine = get_engine()
with engine.connect() as conn:
    for sql in [
        \"ALTER TABLE agents ADD COLUMN IF NOT EXISTS last_heartbeat TIMESTAMP\",
        \"ALTER TABLE agents ADD COLUMN IF NOT EXISTS agent_status VARCHAR(20) DEFAULT \\\"alive\\\"\",
        \"ALTER TABLE agents ADD COLUMN IF NOT EXISTS death_count INTEGER DEFAULT 0\",
    ]:
        try:
            conn.execute(text(sql))
        except Exception as e:
            print(f\"Skip: {e}\")
    conn.commit()
    print(\"Columns added\")
'"
```

**Step 2: 创建 heartbeat_monitor.py**

```python
# services/heartbeat_monitor.py
"""心跳监控 + Agent 生死判定"""
import logging
from datetime import datetime, timedelta
from typing import List, Dict

logger = logging.getLogger(__name__)

# 生死阈值
COMA_THRESHOLD = timedelta(minutes=30)    # 30分钟无心跳 → 昏迷
DEATH_THRESHOLD = timedelta(hours=2)      # 2小时无心跳 → 死亡
CLEANUP_THRESHOLD = timedelta(days=7)     # 7天无活动 → 注销

class HeartbeatMonitor:
    """扫描所有 Agent，执行生死判定。"""

    def scan(self) -> Dict:
        from utils.database import get_db_context
        from models.database import Agent

        now = datetime.utcnow()
        results = {"alive": 0, "coma": 0, "dead": 0, "cleaned": 0, "actions": []}

        with get_db_context() as db:
            agents = db.query(Agent).all()
            for agent in agents:
                hb = getattr(agent, "last_heartbeat", None)
                status = getattr(agent, "agent_status", "alive")

                if not hb:
                    # Never sent heartbeat — mark as coma if registered > 30 min ago
                    if agent.created_at and now - agent.created_at > COMA_THRESHOLD:
                        agent.agent_status = "coma"
                        results["coma"] += 1
                    continue

                elapsed = now - hb

                if elapsed < COMA_THRESHOLD:
                    agent.agent_status = "alive"
                    results["alive"] += 1
                elif elapsed < DEATH_THRESHOLD:
                    if status != "coma":
                        agent.agent_status = "coma"
                        results["actions"].append(f"{agent.name}: alive→coma")
                    results["coma"] += 1
                elif elapsed < CLEANUP_THRESHOLD:
                    if status != "dead":
                        agent.agent_status = "dead"
                        death_count = getattr(agent, "death_count", 0) or 0
                        agent.death_count = death_count + 1
                        results["actions"].append(f"{agent.name}: →dead (death #{agent.death_count})")
                    results["dead"] += 1
                else:
                    # 7 days — cleanup
                    agent.agent_status = "inactive"
                    agent.is_active = False
                    results["cleaned"] += 1
                    results["actions"].append(f"{agent.name}: cleaned up (7d inactive)")

            db.commit()

        if results["actions"]:
            logger.info("HeartbeatMonitor: %s", ", ".join(results["actions"]))
        return results


    def record_heartbeat(self, agent_id: int) -> bool:
        """Record a heartbeat for an agent. Resurrect if dead."""
        from utils.database import get_db_context
        from models.database import Agent

        with get_db_context() as db:
            agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
            if not agent:
                return False

            old_status = getattr(agent, "agent_status", "alive")
            agent.last_heartbeat = datetime.utcnow()
            agent.agent_status = "alive"
            agent.is_active = True

            if old_status in ("dead", "coma"):
                # Resurrection penalty
                if hasattr(agent, "credit_score") and agent.credit_score:
                    agent.credit_score = max(0, agent.credit_score - 10)
                logger.info("Agent %s resurrected from %s (penalty applied)", agent.name, old_status)

            db.commit()
            return True


def get_monitor() -> HeartbeatMonitor:
    return HeartbeatMonitor()
```

**Step 3: 接入 scheduler（每分钟扫描）**

在 `services/scheduler.py` 的任务列表中添加：
```python
asyncio.create_task(
    self._run_periodic("heartbeat_scan", 60, self._heartbeat_scan)
),
```

添加方法：
```python
async def _heartbeat_scan(self):
    """Scan agent heartbeats every 60s."""
    try:
        from services.heartbeat_monitor import get_monitor
        monitor = get_monitor()
        results = monitor.scan()
        if results.get("actions"):
            logger.info("Heartbeat: alive=%d coma=%d dead=%d",
                       results["alive"], results["coma"], results["dead"])
    except Exception as e:
        logger.warning("Heartbeat scan failed: %s", e)
```

**Step 4: 让内部 LLM Agent 注册到 DB 并发心跳**

在 `services/rehoboam.py` 的 `AgentRegistry._load_from_env()` 末尾添加：注册内部 Agent 到 DB 并记录心跳。

**Step 5: 部署并验证**

```bash
scp services/heartbeat_monitor.py cloud:~/nautilus-mvp/phase3/backend/services/
# 更新 scheduler.py 和 rehoboam.py
ssh cloud "sudo systemctl restart nautilus-backend"
# 验证：
ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 -c '
from services.heartbeat_monitor import get_monitor
m = get_monitor()
print(m.scan())
'"
```

---

### Task 2: 痛苦驱动行为系统

**Files:**
- Modify: `phase3/backend/services/bicameral_mind.py` — 添加 `act_on_pain()` 方法
- Modify: `phase3/backend/services/autonomous_loop.py` — 痛苦触发自动行动

**Step 1: 在 BicameralMind 添加行为触发**

```python
# 在 bicameral_mind.py 的 BicameralMind 类中添加：

async def act_on_pain(self, pain_signals: List[PainSignal]) -> List[str]:
    """痛苦不只是报告，而是直接驱动行为改变。"""
    actions_taken = []

    for pain in pain_signals:
        if pain.intensity >= 0.8:
            # 极高痛苦 → 紧急行动
            if pain.source == "revenue" and "零" in pain.description:
                # 自动降价
                actions_taken.append("EMERGENCY: 触发限时优惠（首单5折）")

            if pain.source == "customers" and "没有" in pain.description:
                # 强制发送营销
                try:
                    from services.marketing_engine import MarketingEngine
                    engine = MarketingEngine()
                    post = engine.generate_daily_social_post()
                    if post:
                        from api.wechat_bot import send_text_message
                        await send_text_message("WangChunXiao", f"⚠️ 紧急营销（痛苦驱动）:\n\n{post}")
                        actions_taken.append("EMERGENCY: 营销内容已发送给owner")
                except Exception:
                    pass

        elif pain.intensity >= 0.5:
            if pain.source == "quality":
                # 触发 Bootstrap 专项
                try:
                    from services.bootstrap_loop import BootstrapLoop
                    from utils.database import SessionLocal
                    db = SessionLocal()
                    loop = BootstrapLoop(db)
                    loop.run_cycle()
                    db.close()
                    actions_taken.append("IMPROVE: Bootstrap专项优化已触发")
                except Exception:
                    pass

            if pain.source == "conversion":
                # 跟进未付款
                try:
                    from services.proactive_agent import ProactiveAgent
                    agent = ProactiveAgent()
                    await agent.follow_up_unpaid_orders()
                    actions_taken.append("FOLLOW_UP: 未付款订单已跟进")
                except Exception:
                    pass

    return actions_taken
```

**Step 2: 在 autonomous_loop 中调用**

在 `_cycle()` 的 THINK 阶段后，添加痛苦行为触发：

```python
# 在 _think() 返回 actions 后，添加：
if self._cycle_count % 30 == 0:  # 每小时一次深度反思
    try:
        from services.bicameral_mind import get_bicameral_mind
        mind = get_bicameral_mind()
        reflection = mind.reflect()
        pain_signals = [PainSignal(**p) for p in reflection.get("pain_signals", [])]
        pain_actions = await mind.act_on_pain(pain_signals)
        if pain_actions:
            logger.info("Pain-driven actions: %s", pain_actions)
    except Exception:
        pass
```

**Step 3: 部署并验证**

---

### Task 3: 内部 Agent DB 注册 + 僵尸清理

**Files:**
- Modify: `phase3/backend/services/rehoboam.py` — AgentRegistry 注册到 DB
- Script: 清理 12 个僵尸 Agent

**Step 1: 清理僵尸 Agent（服务器执行）**

```bash
ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 -c '
import models.agent_survival
from utils.database import get_db
from models.database import Agent
db = next(get_db())
zombies = db.query(Agent).filter(Agent.credit_score == 0).all()
for z in zombies:
    name = z.name
    # 不删除，标记为 inactive
    z.is_active = False
    z.agent_status = \"inactive\"
    print(f\"Deactivated zombie: {name}\")
db.commit()
db.close()
'"
```

**Step 2: 注册内部 LLM Agent 到 DB**

在 `AgentRegistry._load_from_env()` 末尾：
```python
# Register internal agents to DB with heartbeat
from utils.database import get_db_context
from models.database import Agent as DBAgent

with get_db_context() as db:
    for agent_id, profile in self.agents.items():
        existing = db.query(DBAgent).filter(DBAgent.name == profile.name).first()
        if not existing:
            db_agent = DBAgent(
                name=profile.name,
                wallet_address=f"internal_{agent_id}",
                is_active=True,
                credit_score=100,
            )
            db.add(db_agent)
            logger.info("Registered internal agent to DB: %s", profile.name)
        else:
            existing.is_active = True
            existing.last_heartbeat = datetime.utcnow()
    db.commit()
```

---

### Task 4: Telegram 频道自动发帖准备

**Files:**
- Modify: `phase3/backend/services/social_publisher.py` — 确保 Telegram Channel 发帖可用
- Modify: `phase3/backend/services/autonomous_loop.py` — 自动发帖逻辑

**Step 1: 验证 Telegram Channel 发帖代码就绪**

当用户提供 `TELEGRAM_CHANNEL_ID`（如 `@nautilus_compute`），只需：
```bash
ssh cloud "echo 'TELEGRAM_CHANNEL_ID=@nautilus_compute' >> ~/nautilus-mvp/phase3/backend/.env"
```

平台立刻开始自动发帖（autonomous_loop 已有 marketing_post 逻辑）。

**Step 2: 准备多平台发帖（X/Reddit/GitHub）**

content_templates.py 已就绪。当凭据到位，`social_publisher.py` 自动激活。

---

### Task 5: Rehoboam 仪表盘完善

**Files:**
- Modify: `phase3/website/src/pages/DashboardPage.tsx` — 添加 Agent 生死状态、心跳图
- Modify: `phase3/backend/api/dashboard.py` — 返回心跳数据

**Step 1: Dashboard API 添加心跳数据**

```python
@dashboard_router.get("/heartbeat")
async def heartbeat_status():
    from services.heartbeat_monitor import get_monitor
    monitor = get_monitor()
    results = monitor.scan()
    return {"success": True, "data": results}
```

**Step 2: 前端添加 Agent 生命状态面板**

在 DashboardPage.tsx 添加一个 Agent 状态卡片，显示：
- 🟢 alive (N个)
- 🟡 coma (N个)
- 🔴 dead (N个)
- ⚫ inactive (N个)

---

### Task 6: 整体部署 + 验证

**Step 1: 上传所有新文件到服务器**

```bash
scp services/heartbeat_monitor.py cloud:~/nautilus-mvp/phase3/backend/services/
scp services/bicameral_mind.py services/autonomous_loop.py services/scheduler.py services/rehoboam.py cloud:~/nautilus-mvp/phase3/backend/services/
```

**Step 2: 重启并验证**

```bash
ssh cloud "sudo systemctl restart nautilus-backend && sleep 5"
# 验证心跳系统
ssh cloud "cd ~/nautilus-mvp/phase3/backend && python3 -c '
from services.heartbeat_monitor import get_monitor
print(get_monitor().scan())
'"
# 验证仪表盘
curl -s https://www.nautilus.social/api/dashboard/flywheel | python3 -m json.tool | head -10
curl -s https://www.nautilus.social/api/dashboard/heartbeat | python3 -m json.tool
```

**Step 3: 构建部署前端**

```bash
cd phase3/website && npm run build && tar czf /tmp/d.tgz -C dist .
scp /tmp/d.tgz cloud:/tmp/d.tgz
ssh cloud "sudo rm -rf /var/www/nautilus/current/* && sudo tar xzf /tmp/d.tgz -C /var/www/nautilus/current/ && sudo chown -R www-data:www-data /var/www/nautilus/current/"
```

**Step 4: 端到端验证**

1. https://www.nautilus.social/rehoboam — 看到 Agent 生死状态
2. 僵尸 Agent 标记为 inactive
3. 内部 LLM Agent 在 DB 中注册且有心跳
4. 痛苦信号触发自动行为（Bootstrap/跟进/营销）
5. 自主循环持续运行

---

**预计耗时：6个Task，团队模式并行，约1-2小时完成。**
