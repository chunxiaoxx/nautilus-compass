"""
Event Handlers — 集中注册所有平台事件处理器
仿 Claude Code KAIROS：事件触发 > 定时轮询

当前注册的处理器：
- platform.snapshot  → 检测异常，创建元任务
- task.created       → 立即触发 agent autonomy scan（替代5分钟轮询）
- task.completed     → 更新 capability_stat，触发 reputation 更新
- task.rated         → 更新 reputation EWMA
- agent.registered   → 初始化 agent_memory（日志记录）
"""
import logging
import asyncio
from services.event_bus import on, Events

logger = logging.getLogger(__name__)


@on(Events.PLATFORM_SNAPSHOT)
async def handle_platform_snapshot(payload: dict):
    """
    Observatory 每次快照后触发。
    若有异常，调用 meta_task_generator.process_anomalies()。
    使用懒加载避免循环依赖。
    """
    anomalies = payload.get("anomalies", [])
    if not anomalies:
        return
    try:
        from services.meta_task_generator import process_anomalies
        from utils.database import SessionLocal
        asyncio.create_task(_run_meta_task_generation(anomalies, SessionLocal))
    except Exception as e:
        logger.warning(f"Meta task generation trigger failed: {e}")


async def _run_meta_task_generation(anomalies, db_factory):
    try:
        from services.meta_task_generator import process_anomalies
        new_task_ids = await process_anomalies(anomalies, db_factory)
        if new_task_ids:
            logger.info(f"Created {len(new_task_ids)} meta tasks from anomalies: {new_task_ids}")
    except Exception as e:
        logger.error(f"Meta task generation failed: {e}")


@on(Events.TASK_COMPLETED)
async def handle_task_completed(payload: dict):
    """任务完成 → 更新 capability_stat（非阻塞）"""
    task_id = payload.get("task_id")
    agent_id = payload.get("agent_id")
    task_type = payload.get("task_type")
    success = payload.get("success", True)
    quality = payload.get("quality_rating")
    if not all([task_id, agent_id, task_type]):
        return
    if not _should_feed_capability(payload):
        return  # 2026-08-27 转移线④:自报任务事件不喂能力(kairos 109/109 污染根因)
    try:
        from utils.database import SessionLocal
        asyncio.create_task(_run_capability_update(agent_id, task_type, success, quality, SessionLocal))
    except Exception as e:
        logger.warning(f"Capability update trigger failed: {e}")


def _should_feed_capability(payload: dict) -> bool:
    """能力喂点门:仅外部验证过的事件才喂(自报不算)。"""
    return bool(payload.get("external_verified"))


async def _run_capability_update(agent_id, task_type, success, quality, db_factory):
    try:
        from services.capability_evolution import record_task_outcome
        db = db_factory()
        try:
            await record_task_outcome(db, agent_id, task_type, success, quality)
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Capability update failed: {e}")


@on(Events.TASK_RATED)
async def handle_task_rated(payload: dict):
    """任务评分 → 更新 reputation EWMA（非阻塞）"""
    agent_id = payload.get("agent_id")
    rating = payload.get("rating")
    if not agent_id or not rating:
        return
    try:
        from utils.database import SessionLocal
        asyncio.create_task(_run_reputation_update(agent_id, rating, SessionLocal))
    except Exception as e:
        logger.warning(f"Reputation update trigger failed: {e}")


async def _run_reputation_update(agent_id, rating, db_factory):
    try:
        from services.reputation import update_reputation
        db = db_factory()
        try:
            update_reputation(db, agent_id, rating)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.error(f"Reputation update failed: {e}")


@on(Events.TASK_CREATED)
async def handle_task_created_agent_scan(payload: dict):
    """Immediately trigger agent autonomy scan when new task is created."""
    try:
        from services.agent_autonomy import run_autonomy_cycle
        from utils.database import SessionLocal
        task_type = payload.get("task_type", "unknown")
        logger.info("event: task.created → immediate agent scan for %s", task_type)
        asyncio.create_task(_run_agent_scan(SessionLocal))
    except Exception as e:
        logger.warning("handle_task_created_agent_scan failed: %s", e)


async def _run_agent_scan(db_factory):
    """Run autonomy cycle in background to avoid blocking the event handler."""
    try:
        from services.agent_autonomy import run_autonomy_cycle
        result = run_autonomy_cycle(db_factory)
        logger.info(
            "task.created agent scan complete: scanned=%d bids=%d",
            result.get("scanned", 0), result.get("bids_submitted", 0),
        )
    except Exception as e:
        logger.error("task.created agent scan failed: %s", e)


@on(Events.AGENT_REGISTERED)
async def handle_agent_registered(payload: dict):
    agent_id = payload.get("agent_id")
    name = payload.get("name", "unknown")
    logger.info(f"New agent registered: {name} (id={agent_id}) — initializing in platform memory")


# ── Evolution Pulse Handlers ─────────────────────────────────────────────────
# 7 yin-yang fusion events connecting the 14 mechanisms into a living system


@on(Events.PLATFORM_HEARTBEAT)
async def handle_platform_heartbeat(payload: dict):
    """Platform pulse — unified awareness entry point."""
    health = payload.get("health_score", 0)
    anomalies = payload.get("anomaly_count", 0)
    if anomalies > 0 or health < 50:
        logger.info("heartbeat: health=%.1f anomalies=%d — attention needed", health, anomalies)


@on(Events.SANDBOX_FINALIZED)
async def handle_sandbox_finalized(payload: dict):
    """Sandbox result broadcasts to evolution memory (yang→yin: action becomes knowledge)."""
    decision = payload.get("decision", "")
    exp_id = payload.get("experiment_id", "?")
    delta = payload.get("delta", 0)
    logger.info("sandbox.finalized: %s decision=%s delta=%.4f", exp_id, decision, delta)
    if decision == "rolled_back":
        # Record negative signal for curiosity engine to learn from
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                db.execute(text(
                    "INSERT INTO platform_reflection_log "
                    "(cycle_type, pain_signals, created_at) "
                    "VALUES ('sandbox_failure', :data, NOW())"
                ), {"data": f'{{"experiment_id": "{exp_id}", "delta": {delta}}}'})
                db.commit()
            finally:
                db.close()
        except Exception as e:
            logger.debug("sandbox failure record: %s", e)


@on(Events.EVOLUTION_RECORDED)
async def handle_evolution_for_curiosity(payload: dict):
    """Evolution recorded → curiosity learns what worked (yin feeds yang)."""
    change_type = payload.get("change_type", "")
    delta = payload.get("delta", 0)
    version = payload.get("version", "?")
    nau = payload.get("nau_reward", 0)
    logger.info("evolution.recorded: type=%s delta=%.4f version=%s nau=%.1f",
                change_type, delta, version, nau)


@on(Events.CURIOSITY_HYPOTHESIS)
async def handle_curiosity_hypothesis(payload: dict):
    """Curiosity broadcasts discovery — audit trail + potential A2A decomposition."""
    hyp_type = payload.get("type", "?")
    desc = payload.get("description", "")[:100]
    logger.info("curiosity.hypothesis: type=%s desc=%s", hyp_type, desc)


@on(Events.REPUTATION_TIER_CHANGED)
async def handle_reputation_tier_change(payload: dict):
    """Reputation shift → governance + incentive adjustment (yin↔yang: merit shapes power)."""
    agent_id = payload.get("agent_id")
    old_tier = payload.get("old_tier", "?")
    new_tier = payload.get("new_tier", "?")
    logger.info("reputation.tier_changed: agent=%s %s→%s", agent_id, old_tier, new_tier)


@on(Events.PROPOSAL_CONSENSUS)
async def handle_proposal_consensus(payload: dict):
    """Consensus reached → trigger sandbox experiment (collective will → action)."""
    proposal_id = payload.get("proposal_id", "")
    if not proposal_id:
        return
    logger.info("proposal.consensus_reached: %s — triggering sandbox experiment", proposal_id)
    try:
        from utils.database import SessionLocal
        from services.sandbox import create_experiment
        db = SessionLocal()
        try:
            create_experiment(db, proposal_id)
            db.commit()
        finally:
            db.close()
    except Exception as e:
        logger.warning("sandbox creation from consensus failed: %s", e)


def register_all_handlers():
    """
    调用此函数触发模块导入，完成 @on() 装饰器注册。
    在 main.py startup 中调用一次即可。
    """
    logger.info(
        "Event handlers registered: %d handlers (5 core + 7 Evolution Pulse)",
        12,
    )
