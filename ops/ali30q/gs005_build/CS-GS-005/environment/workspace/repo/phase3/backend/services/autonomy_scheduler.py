"""APScheduler 配置 — 每5分钟运行一次自主扫描"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services.agent_autonomy import run_autonomy_cycle

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()


async def _run_autonomy_cycle(db_session_factory) -> None:
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, run_autonomy_cycle, db_session_factory)
    bids = result.get("bids_submitted", 0)
    errors = result.get("errors", [])
    if bids > 0 or errors:
        logger.info("autonomy_cycle: scanned=%d bids=%d errors=%d",
                    result.get("scanned", 0), bids, len(errors))


def start_autonomy_scheduler(db_session_factory) -> None:
    """在 FastAPI lifespan 中调用，启动后台调度。"""
    scheduler.add_job(
        func=_run_autonomy_cycle,
        args=[db_session_factory],
        trigger="interval",
        minutes=5,
        id="autonomy_cycle",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("Autonomy scheduler started (interval=5min)")


def stop_autonomy_scheduler() -> None:
    """在 FastAPI lifespan shutdown 中调用，停止调度器。"""
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Autonomy scheduler stopped")
