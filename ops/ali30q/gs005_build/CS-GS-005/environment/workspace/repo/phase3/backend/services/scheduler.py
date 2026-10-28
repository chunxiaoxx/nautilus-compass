"""
Background scheduler for periodic bootstrap tasks.
Runs inside the uvicorn process using asyncio.

Tasks:
- Stuck task cleanup: every 1 hour
- Bootstrap analysis: every 6 hours
"""
import asyncio
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """Lightweight async scheduler that runs periodic maintenance tasks."""

    def __init__(self):
        self._running = False
        self._tasks: list[asyncio.Task] = []

    async def start(self):
        """Start all scheduled tasks."""
        if self._running:
            return
        self._running = True
        logger.info("Background scheduler started")

        self._tasks = [
            asyncio.create_task(
                self._run_periodic("stuck_cleanup", 3600, self._cleanup_stuck_tasks)
            ),
            asyncio.create_task(
                self._run_periodic("bootstrap", 7200, self._run_bootstrap)
            ),
            asyncio.create_task(
                self._run_periodic("rehoboam_check", 60, self._rehoboam_autonomous_check)
            ),
            asyncio.create_task(
                self._run_periodic("executive_check", 300, self._executive_periodic_check)
            ),
            asyncio.create_task(
                self._run_periodic("bicameral_reflection", 7200, self._daily_reflection)
            ),
            asyncio.create_task(
                self._run_periodic("heartbeat_scan", 60, self._heartbeat_scan)
            ),
        ]

    async def stop(self):
        """Stop all scheduled tasks gracefully."""
        self._running = False
        for task in self._tasks:
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks.clear()
        logger.info("Background scheduler stopped")

    async def _run_periodic(self, name: str, interval_seconds: int, func):
        """Run a function periodically with error isolation."""
        while self._running:
            try:
                await asyncio.sleep(interval_seconds)
                if not self._running:
                    break
                logger.info(f"Scheduler: running {name}")
                await func()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scheduler {name} error: {e}", exc_info=True)

    async def _cleanup_stuck_tasks(self):
        """Reset tasks stuck in 'processing' for over 30 minutes."""
        from utils.database import SessionLocal
        from models.database import AcademicTask

        db = SessionLocal()
        try:
            cutoff = datetime.utcnow() - timedelta(minutes=30)
            stuck = (
                db.query(AcademicTask)
                .filter(
                    AcademicTask.status == "processing",
                    AcademicTask.updated_at < cutoff,
                )
                .all()
            )
            for task in stuck:
                task.status = "failed"
                task.result_error = "Timed out after 30 minutes"
                logger.warning(f"Reset stuck task: {task.task_id}")
            db.commit()
            if stuck:
                logger.info(f"Reset {len(stuck)} stuck tasks")
            else:
                logger.info("No stuck tasks found")
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    async def _run_bootstrap(self):
        """Run one bootstrap analysis cycle if BootstrapLoop is available."""
        try:
            from services.bootstrap_loop import BootstrapLoop
        except ImportError:
            logger.debug("BootstrapLoop not available, skipping bootstrap cycle")
            return

        from utils.database import SessionLocal

        db = SessionLocal()
        try:
            loop = BootstrapLoop(db)
            report = loop.run_cycle()
            logger.info(
                f"Bootstrap cycle: {report.get('tasks_analyzed', 0)} analyzed, "
                f"{report.get('improvements_applied', 0)} applied"
            )
        except Exception as e:
            raise e
        finally:
            db.close()

    async def _rehoboam_autonomous_check(self):
        """Rehoboam autonomous check — runs every 60s."""
        try:
            from services.rehoboam import get_rehoboam
            r = get_rehoboam()
            actions = await r.autonomous_check()
            if actions:
                logger.info("Rehoboam autonomous: %s", ", ".join(actions))
        except Exception as e:
            logger.warning("Rehoboam autonomous check failed: %s", e)

    async def _executive_periodic_check(self):
        """Rehoboam Executive — goal tracking every 5 min."""
        try:
            from services.rehoboam_executive import get_executive
            exe = get_executive()
            result = exe.periodic_check()
            if result.get("proactive_actions"):
                logger.info("Executive actions: %s", result["proactive_actions"])
        except Exception as e:
            logger.warning("Executive check failed: %s", e)

    async def _daily_reflection(self):
        """Bicameral mind daily reflection — runs every 6 hours."""
        try:
            from services.bicameral_mind import get_bicameral_mind
            mind = get_bicameral_mind()
            report = await mind.send_reflection()
            logger.info("Bicameral reflection completed")
        except Exception as e:
            logger.warning("Daily reflection failed: %s", e)

    async def _heartbeat_scan(self):
        """Heartbeat monitor — mark coma/dead/inactive agents every 60s."""
        try:
            from services.heartbeat_monitor import get_monitor
            monitor = get_monitor()
            summary = monitor.scan()
            if summary.get("to_coma") or summary.get("to_dead") or summary.get("to_inactive"):
                logger.info("Heartbeat scan: %s", summary)
        except Exception as e:
            logger.warning("Heartbeat scan failed: %s", e)


# Singleton
_scheduler = BackgroundScheduler()


def get_scheduler() -> BackgroundScheduler:
    """Return the singleton scheduler instance."""
    return _scheduler
