"""
Platform Brain — GOD OBJECT partially decomposed.

Part 1-2 (BicameralMind + SelfImprovementEngine) → services.pairs.mind
Part 3-4 (RehoboamExecutive + AutonomousLoop) remain here until Wave 4.

Public API (all re-exported for backward compatibility):
    get_autonomous_loop() -> AutonomousLoop
    get_bicameral_mind()  -> BicameralMind
    get_executive()       -> RehoboamExecutive
    get_self_improvement_engine() -> SelfImprovementEngine
"""
import asyncio
import json
import logging
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

THINK_INTERVAL = 120

# ── Re-exports from pairs/mind.py (Part 1+2) ──────────────────────────────
from services.pairs.mind import (  # noqa: F401
    _gather_platform_state,
    PainSignal, BicameralMind, get_bicameral_mind,
    SelfImprovementEngine, get_self_improvement_engine,
    PAIN_TO_TASK_TEMPLATES,
)


# ===================================================================
# Part 3: Rehoboam Executive — daily plan + goal tracking + proactive
# ===================================================================

@dataclass(frozen=True)
class YesterdayReview:
    date: str
    tasks_completed: int
    tasks_failed: int
    revenue: float
    cost_estimate: float
    unique_customers: int
    top_failure_reasons: List[str]


@dataclass(frozen=True)
class DailyGoals:
    target_tasks: int
    target_revenue: float
    improvement_focus: str
    agent_priorities: Dict[str, str]


@dataclass
class DailyPlan:
    plan_date: str
    review: YesterdayReview
    goals: DailyGoals
    created_at: str = ""

    def __post_init__(self):
        if not self.created_at:
            object.__setattr__(self, "created_at", datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {"plan_date": self.plan_date, "review": asdict(self.review),
                "goals": asdict(self.goals), "created_at": self.created_at}


@dataclass
class PerformanceSnapshot:
    timestamp: str
    tasks_today: int = 0
    tasks_failed_today: int = 0
    revenue_today: float = 0.0
    cost_today: float = 0.0
    roi: float = 0.0
    unique_customers_today: int = 0
    agent_efficiency: Dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ProactiveAction:
    action_type: str
    target: str
    detail: str
    priority: int = 1


class DailyPlanGenerator:
    def __init__(self):
        self._cache: Dict[str, DailyPlan] = {}

    def get_or_create(self, db: Session) -> DailyPlan:
        today = date.today().isoformat()
        if today in self._cache:
            return self._cache[today]
        plan = self._generate(db, today)
        self._cache[today] = plan
        stale = [k for k in self._cache if k < (date.today() - timedelta(days=7)).isoformat()]
        for k in stale:
            del self._cache[k]
        return plan

    def _generate(self, db: Session, today_str: str) -> DailyPlan:
        from models.conversation import Order
        from models.database import AcademicTask

        ys = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)
        ye = ys + timedelta(days=1)
        completed = db.query(func.count(AcademicTask.id)).filter(
            AcademicTask.status == "completed", AcademicTask.updated_at >= ys, AcademicTask.updated_at < ye,
        ).scalar() or 0
        failed_count = db.query(func.count(AcademicTask.id)).filter(
            AcademicTask.status == "failed", AcademicTask.updated_at >= ys, AcademicTask.updated_at < ye,
        ).scalar() or 0
        revenue = db.query(func.coalesce(func.sum(Order.paid_amount), 0.0)).filter(
            Order.payment_confirmed_at >= ys, Order.payment_confirmed_at < ye,
        ).scalar() or 0.0
        unique_cust = db.query(func.count(func.distinct(Order.customer_id))).filter(
            Order.created_at >= ys, Order.created_at < ye,
        ).scalar() or 0
        reasons = db.query(AcademicTask.result_error).filter(
            AcademicTask.status == "failed", AcademicTask.updated_at >= ys,
            AcademicTask.updated_at < ye, AcademicTask.result_error.isnot(None),
        ).limit(5).all()

        review = YesterdayReview(
            date=ys.date().isoformat(), tasks_completed=int(completed),
            tasks_failed=int(failed_count), revenue=float(revenue),
            cost_estimate=float(completed) * 0.02, unique_customers=int(unique_cust),
            top_failure_reasons=[r[0][:120] for r in reasons if r[0]],
        )
        target_tasks = max(5, int(completed * 1.2))
        target_revenue = max(1.0, float(revenue) * 1.2)
        focus = ("reduce_failures" if failed_count > completed * 0.3
                 else "new_customers" if unique_cust < 2 else "grow_revenue")
        return DailyPlan(plan_date=today_str, review=review,
                         goals=DailyGoals(target_tasks, target_revenue, focus, {}))


class PerformanceTracker:
    def snapshot(self, db: Session) -> PerformanceSnapshot:
        from models.conversation import Order
        from models.database import AcademicTask

        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        tasks_today = db.query(func.count(AcademicTask.id)).filter(
            AcademicTask.status == "completed", AcademicTask.updated_at >= today_start,
        ).scalar() or 0
        tasks_failed = db.query(func.count(AcademicTask.id)).filter(
            AcademicTask.status == "failed", AcademicTask.updated_at >= today_start,
        ).scalar() or 0
        revenue = db.query(func.coalesce(func.sum(Order.paid_amount), 0.0)).filter(
            Order.payment_confirmed_at >= today_start,
        ).scalar() or 0.0
        unique_cust = db.query(func.count(func.distinct(Order.customer_id))).filter(
            Order.created_at >= today_start,
        ).scalar() or 0
        cost = float(tasks_today) * 0.02
        return PerformanceSnapshot(
            timestamp=datetime.utcnow().isoformat(), tasks_today=int(tasks_today),
            tasks_failed_today=int(tasks_failed), revenue_today=float(revenue),
            cost_today=cost, roi=round(float(revenue) / cost, 2) if cost > 0 else 0.0,
            unique_customers_today=int(unique_cust))


class GoalEngine:
    def __init__(self, plan_gen: DailyPlanGenerator, tracker: PerformanceTracker):
        self._plan_gen = plan_gen
        self._tracker = tracker
        self._escalated_today = False

    def evaluate(self, db: Session) -> Dict[str, Any]:
        plan = self._plan_gen.get_or_create(db)
        snap = self._tracker.snapshot(db)
        now = datetime.utcnow()
        day_pct = min((now.hour * 60 + now.minute) / 1440, 1.0) * 100
        target_tasks = plan.goals.target_tasks or 1
        target_rev = plan.goals.target_revenue or 1.0
        task_pct = (snap.tasks_today / target_tasks) * 100
        rev_pct = (snap.revenue_today / target_rev) * 100
        if task_pct >= day_pct * 1.3 and rev_pct >= day_pct * 1.3:
            status, action = "ahead", "raise_target"
        elif task_pct < day_pct * 0.6 or rev_pct < day_pct * 0.6:
            status = "behind"
            action = "escalate" if not self._escalated_today else None
            self._escalated_today = True
        else:
            status, action = "on_track", None
        return {"status": status, "task_pct": round(task_pct, 1), "revenue_pct": round(rev_pct, 1),
                "expected_pct": round(day_pct, 1), "action": action, "snapshot": snap.to_dict()}

    def reset_daily_state(self):
        self._escalated_today = False


class ProactiveActionEngine:
    def scan(self, db: Session) -> List[ProactiveAction]:
        from models.conversation import Order, Customer
        from models.database import AcademicTask

        actions: List[ProactiveAction] = []
        now = datetime.utcnow()
        for order in db.query(Order).filter(Order.status == "quoted", Order.created_at < now - timedelta(hours=24)).limit(20).all():
            cust = db.query(Customer).filter(Customer.id == order.customer_id).first()
            actions.append(ProactiveAction("follow_up", order.order_no,
                f"Order {order.order_no} for {cust.name if cust else '?'} quoted >24h ago"))
        for c in db.query(Customer).filter(Customer.total_spent >= 500, Customer.trust_level < 4).limit(10).all():
            actions.append(ProactiveAction("birthday", c.name, f"{c.name} spent {c.total_spent:.0f} but trust={c.trust_level}", 2))
        failures = db.query(AcademicTask.task_type, func.count(AcademicTask.id).label("cnt")).filter(
            AcademicTask.status == "failed", AcademicTask.updated_at >= now - timedelta(days=7),
        ).group_by(AcademicTask.task_type).having(func.count(AcademicTask.id) >= 3).all()
        for task_type, cnt in failures:
            actions.append(ProactiveAction("capability_gap", task_type or "unknown", f"{cnt} failures in '{task_type}' last 7d", 2))
        return actions


class RehoboamExecutive:
    def __init__(self):
        self._plan_gen = DailyPlanGenerator()
        self._tracker = PerformanceTracker()
        self._goal_engine = GoalEngine(self._plan_gen, self._tracker)
        self._proactive = ProactiveActionEngine()
        self._last_plan_date: Optional[str] = None

    def daily_plan(self) -> Dict[str, Any]:
        from utils.database import get_db_context
        with get_db_context() as db:
            plan = self._plan_gen.get_or_create(db)
            today = date.today().isoformat()
            if self._last_plan_date != today:
                self._goal_engine.reset_daily_state()
                self._last_plan_date = today
            return plan.to_dict()

    def performance(self) -> Dict[str, Any]:
        from utils.database import get_db_context
        with get_db_context() as db:
            return self._tracker.snapshot(db).to_dict()

    def evaluate_goals(self) -> Dict[str, Any]:
        from utils.database import get_db_context
        with get_db_context() as db:
            return self._goal_engine.evaluate(db)

    def proactive_scan(self) -> List[Dict[str, Any]]:
        from utils.database import get_db_context
        with get_db_context() as db:
            return [asdict(a) for a in self._proactive.scan(db)]

    def periodic_check(self) -> Dict[str, Any]:
        return {"goals": self.evaluate_goals(), "proactive_actions": self.proactive_scan(),
                "checked_at": datetime.utcnow().isoformat()}


# ===================================================================
# Part 4: Autonomous Loop — self-driving Observe→Think→Act→Learn
# ===================================================================

class AutonomousLoop:
    def __init__(self):
        self._running = False
        self._last_actions: Dict[str, float] = {}
        self._action_cooldowns = {"marketing_post": 7200, "follow_up": 3600, "task_notify": 60,
                                   "bootstrap": 7200, "alert_owner": 1800, "capability_showcase": 86400,
                                   "queue_refill": 300}
        self._cycle_count = 0
        self._total_actions = 0

    async def start(self):
        self._running = True
        logger.info("AutonomousLoop STARTED — platform is now self-driving")
        while self._running:
            try:
                await self._cycle()
            except Exception as e:
                logger.error("AutonomousLoop cycle error: %s", e, exc_info=True)
            await asyncio.sleep(THINK_INTERVAL)

    async def stop(self):
        self._running = False

    def _can_act(self, action_type: str) -> bool:
        return time.time() - self._last_actions.get(action_type, 0) >= self._action_cooldowns.get(action_type, 300)

    def _record_action(self, action_type: str):
        self._last_actions[action_type] = time.time()
        self._total_actions += 1

    async def _cycle(self):
        self._cycle_count += 1
        t0 = time.monotonic()
        from utils.database import get_db_context
        with get_db_context() as db:
            state = _gather_platform_state(db)
        state["cycle"] = self._cycle_count

        actions = self._think(state)

        if self._cycle_count % 30 == 0:
            try:
                mind = get_bicameral_mind()
                reflection = mind.reflect()
                pain = reflection.get("pain_signals", [])
                if pain:
                    await mind.act_on_pain(pain)
            except Exception as e:
                logger.warning("Bicameral pain check failed: %s", e)

        if self._cycle_count % 60 == 0:
            try:
                engine = get_self_improvement_engine()
                result = await engine.run_cycle()
                if result.get("tasks_published"):
                    logger.info("Self-improvement: %d tasks published", result["tasks_published"])
            except Exception as e:
                logger.warning("Self-improvement cycle failed: %s", e)

        results = []
        for action in actions:
            results.append(await self._act(action))

        if actions:
            logger.info("AutonomousLoop cycle #%d: %d actions in %.1fs",
                        self._cycle_count, len(actions), time.monotonic() - t0)

    def _think(self, state: Dict) -> List[Dict]:
        actions = []
        for item in state.get("notify_needed", []):
            if self._can_act("task_notify"):
                actions.append({"type": "task_notify", "order": item["order"],
                                "customer_id": item["customer_id"], "task_status": item["task_status"]})
        if state.get("unpaid_count", 0) > 0 and self._can_act("follow_up"):
            actions.append({"type": "follow_up", "order_ids": state["unpaid_order_ids"]})
        if self._can_act("marketing_post") and state.get("tasks_completed_24h", 0) > 0:
            actions.append({"type": "marketing_post"})
        if state.get("total_revenue", 0) == 0 and self._cycle_count % 30 == 0 and self._can_act("alert_owner"):
            actions.append({"type": "alert_owner", "reason": "Revenue still zero"})
        if state.get("pending_tasks", 0) < 10 and self._can_act("queue_refill"):
            actions.append({"type": "queue_refill", "current_pending": state.get("pending_tasks", 0)})
        return actions

    async def _act(self, action: Dict) -> Dict:
        action_type = action["type"]
        result = {"type": action_type, "success": False, "detail": ""}
        try:
            if action_type == "task_notify":
                result = await self._act_notify(action)
            elif action_type == "follow_up":
                result = await self._act_follow_up(action)
            elif action_type == "marketing_post":
                result = await self._act_marketing()
            elif action_type == "alert_owner":
                result = await self._act_alert(action)
            elif action_type == "queue_refill":
                result = await self._act_queue_refill(action)
            self._record_action(action_type)
        except Exception as e:
            result["detail"] = str(e)
        return result

    async def _act_notify(self, action: Dict) -> Dict:
        from utils.database import get_db_context
        from models.conversation import Order, Customer
        from models.database import AcademicTask

        with get_db_context() as db:
            order = db.query(Order).filter(Order.order_no == action["order"]).first()
            if not order:
                return {"type": "task_notify", "success": False, "detail": "Order not found"}
            customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
            task = db.query(AcademicTask).filter(AcademicTask.task_id == order.internal_task_id).first() if order.internal_task_id else None
            if not customer or not task:
                return {"type": "task_notify", "success": False, "detail": "Missing data"}
            if task.status == "completed":
                msg = f"Task {order.order_no} completed.\n{(task.result_output or '')[:500]}"
                order.status = "completed"
            else:
                msg = f"Task {order.order_no} failed. Will retry for free."
                order.status = "failed"
            db.commit()
        await self._send_to_customer(customer.wechat_user_id, msg)
        return {"type": "task_notify", "success": True, "detail": f"Notified {customer.name}"}

    async def _act_follow_up(self, action: Dict) -> Dict:
        from utils.database import get_db_context
        from models.conversation import Order, Customer
        sent = 0
        with get_db_context() as db:
            for oid in action.get("order_ids", [])[:3]:
                order = db.query(Order).filter(Order.order_no == oid).first()
                if not order:
                    continue
                customer = db.query(Customer).filter(Customer.id == order.customer_id).first()
                if not customer:
                    continue
                try:
                    await self._send_to_customer(customer.wechat_user_id,
                        f"Hi, interested in the {order.task_type} task (¥{order.quoted_price:.0f})?")
                    sent += 1
                except Exception:
                    pass
        return {"type": "follow_up", "success": sent > 0, "detail": f"Sent {sent} follow-ups"}

    async def _act_marketing(self) -> Dict:
        try:
            import models.agent_survival
            from services.outreach import MarketingEngine
            engine = MarketingEngine()
            post = engine.generate_daily_social_post()
            if not post:
                return {"type": "marketing_post", "success": False, "detail": "No content"}
            try:
                from api.wechat_bot import send_text_message
                await send_text_message("WangChunXiao", f"Marketing:\n\n{post}")
            except Exception as e:  # W2.3 · surface the failure instead of swallowing it
                logger.warning("marketing wechat push failed: %s", str(e)[:200])
            return {"type": "marketing_post", "success": True, "detail": "Posted"}
        except Exception as e:
            return {"type": "marketing_post", "success": False, "detail": str(e)}

    async def _act_alert(self, action: Dict) -> Dict:
        try:
            from api.wechat_bot import send_text_message
            await send_text_message("WangChunXiao", f"Nautilus Alert: {action.get('reason', '?')}")
        except Exception:
            pass
        return {"type": "alert_owner", "success": True, "detail": action.get("reason", "")}

    async def _act_queue_refill(self, action: Dict) -> Dict:
        try:
            engine = get_self_improvement_engine()
            result = await engine.run_cycle()
            return {"type": "queue_refill", "success": True, "detail": f"published={result.get('tasks_published', 0)}"}
        except Exception as exc:
            return {"type": "queue_refill", "success": False, "detail": str(exc)}

    async def _send_to_customer(self, uid: str, msg: str):
        if uid.startswith("tg_"):
            from api.telegram_bot import send_message
            await send_message(int(uid.replace("tg_", "")), msg)
        elif uid.startswith("wecom_"):
            from api.wechat_bot import send_text_message
            await send_text_message(uid.replace("wecom_", ""), msg)


# ===================================================================
# Singletons (Part 3-4 only; Part 1-2 singletons are in pairs/mind.py)
# ===================================================================

_loop_instance: Optional[AutonomousLoop] = None
_executive_instance: Optional[RehoboamExecutive] = None


def get_autonomous_loop() -> AutonomousLoop:
    global _loop_instance
    if _loop_instance is None:
        _loop_instance = AutonomousLoop()
    return _loop_instance


def get_executive() -> RehoboamExecutive:
    global _executive_instance
    if _executive_instance is None:
        _executive_instance = RehoboamExecutive()
    return _executive_instance
