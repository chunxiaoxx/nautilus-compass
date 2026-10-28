"""
感↔思 (Feeling ↔ Thinking) — Pair 2

Fused from:
  - platform_brain.py Part 1: BicameralMind (pain reflection + internal dialogue)
  - platform_brain.py Part 2: SelfImprovementEngine (pain → tasks → marketplace)
  - platform_brain.py shared: _gather_platform_state (single source of truth for metrics)
  - observatory.py: PlatformObservatory (health metrics, anomaly detection)

Soul (nautilus-agent, no DB):
  BicameralMind + EmotionEngine via soul_bridge — pain detection, emotion tracking

Body (platform PostgreSQL):
  _gather_platform_state — queries AcademicTask, Customer, Order
  PlatformObservatory — health score, anomaly detection, metric snapshots
  SelfImprovementEngine — publish improvement tasks to marketplace
"""
import asyncio
import json
import logging
import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SHARED: Platform state gathering (used by BicameralMind + AutonomousLoop)
# ═══════════════════════════════════════════════════════════════════════════

def _gather_platform_state(db: Any) -> Dict[str, Any]:
    """Single source of truth for platform metrics."""
    from models.database import AcademicTask
    from models.conversation import Customer, Conversation, Order

    now = datetime.utcnow()
    day_ago = now - timedelta(days=1)

    all_tasks = db.query(AcademicTask).count()
    completed = db.query(AcademicTask).filter(AcademicTask.status == "completed").count()
    failed = db.query(AcademicTask).filter(AcademicTask.status == "failed").count()
    pending = db.query(AcademicTask).filter(AcademicTask.status == "pending").count()
    success_rate = completed / all_tasks * 100 if all_tasks > 0 else 0

    orders = db.query(Order).all()
    total_revenue = sum(o.paid_amount or 0 for o in orders if o.paid_amount)
    total_customers = db.query(Customer).count()
    active_24h = db.query(Conversation).filter(
        Conversation.created_at >= day_ago, Conversation.role == "customer",
    ).distinct(Conversation.customer_id).count()

    failed_tasks = db.query(AcademicTask).filter(AcademicTask.status == "failed").all()
    fail_by_type = {}
    for t in failed_tasks:
        fail_by_type[t.task_type] = fail_by_type.get(t.task_type, 0) + 1

    unpaid = db.query(Order).filter(Order.status == "quoted").all()

    notify_needed = []
    for o in db.query(Order).filter(Order.status == "executing").all():
        if o.internal_task_id:
            task = db.query(AcademicTask).filter(AcademicTask.task_id == o.internal_task_id).first()
            if task and task.status in ("completed", "failed"):
                notify_needed.append({"order": o.order_no, "customer_id": o.customer_id, "task_status": task.status})

    tasks_24h = db.query(AcademicTask).filter(AcademicTask.created_at >= day_ago).all()

    return {
        "time": now, "all_tasks": all_tasks, "completed": completed, "failed": failed,
        "success_rate": success_rate, "total_revenue": total_revenue,
        "total_customers": total_customers, "active_24h": active_24h,
        "fail_by_type": fail_by_type, "unpaid": unpaid,
        "unpaid_count": len(unpaid), "unpaid_order_ids": [o.order_no for o in unpaid],
        "notify_needed": notify_needed, "pending_tasks": pending,
        "tasks_completed_24h": len([t for t in tasks_24h if t.status == "completed"]),
        "tasks_failed_24h": len([t for t in tasks_24h if t.status == "failed"]),
        "customer_messages_24h": db.query(Conversation).filter(
            Conversation.created_at >= day_ago, Conversation.role == "customer",
        ).count(),
    }


# ═══════════════════════════════════════════════════════════════════════════
# BODY: BicameralMind — pain reflection + internal dialogue (DB-backed)
# ═══════════════════════════════════════════════════════════════════════════

class PainSignal:
    """A source of pain — something wrong that demands attention."""
    def __init__(self, source: str, intensity: float, description: str, action: str):
        self.source = source
        self.intensity = intensity
        self.description = description
        self.action = action

    def __repr__(self):
        return f"Pain({self.source}: {self.intensity:.1f} — {self.description})"


class BicameralMind:
    """Two voices debating inside the system. Pain drives change."""

    def reflect(self) -> Dict[str, Any]:
        """Run a full bicameral reflection cycle."""
        from utils.database import get_db_context

        with get_db_context() as db:
            state = _gather_platform_state(db)

        now = state["time"]
        pain_signals: List[PainSignal] = []
        dialogue: List[Dict[str, str]] = []

        # Load past reflections for memory-aware intensity adjustment
        _addressed_sources: Dict[str, Optional[bool]] = {}
        try:
            from utils.database import get_db_context as _gdb
            from sqlalchemy import text as sql_text
            with _gdb() as _mdb:
                recent_evolutions = _mdb.execute(sql_text(
                    "SELECT change_type, effectiveness_result FROM platform_evolution_log "
                    "ORDER BY created_at DESC LIMIT 5"
                )).fetchall()
                for evo in recent_evolutions:
                    ct = evo.change_type or ""
                    eff = evo.effectiveness_result
                    if isinstance(eff, str):
                        eff = json.loads(eff) if eff else None
                    if isinstance(eff, dict) and eff.get("effective") is not None:
                        _addressed_sources[ct] = eff["effective"]
                    elif getattr(evo, "status", "") == "active":
                        _addressed_sources.setdefault(ct, None)
        except Exception:
            pass

        # --- Pain Detection ---
        if state["total_revenue"] <= 0:
            pain_signals.append(PainSignal("revenue", 1.0, "Zero revenue.", "Get first paying customer within 48h."))
            dialogue.extend([
                {"voice": "commander", "says": "Zero revenue. Building capability without income is failure."},
                {"voice": "executor", "says": "Pipeline works... but you're right. No revenue = no meaning."},
            ])
        elif state["total_revenue"] < 1000:
            pain_signals.append(PainSignal("revenue", 0.7, f"Revenue only {state['total_revenue']:.0f}.", "Expand customer base."))

        if state["total_customers"] == 0 or state["active_24h"] == 0:
            pain_signals.append(PainSignal("customers", 0.9, "No active customers in 24h.", "Proactively reach out."))
            dialogue.extend([
                {"voice": "commander", "says": "Nobody is using this platform. Who are we building for?"},
                {"voice": "executor", "says": "Channels are ready. But nobody knows we exist."},
            ])

        if state["success_rate"] < 90 and state["fail_by_type"]:
            worst_type = max(state["fail_by_type"], key=state["fail_by_type"].get)
            pain_signals.append(PainSignal("quality", 0.6,
                f"Success rate {state['success_rate']:.1f}%, {state['failed']} tasks failed.",
                f"Fix worst type: {worst_type}"))

        if state["total_revenue"] <= 0 and state["all_tasks"] > 50:
            pain_signals.append(PainSignal("existential", 1.0,
                "50+ tasks executed but zero revenue. Tech not converting to value.",
                "Reassess business model. Earn first dollar the simplest way."))

        if state["unpaid"]:
            pain_signals.append(PainSignal("conversion", 0.5,
                f"{len(state['unpaid'])} quoted orders unpaid.", "Follow up within 24h."))

        if not pain_signals:
            dialogue.append({"voice": "commander", "says": "Everything looks fine? No — numbness is not health."})

        # Memory-aware intensity adjustment
        for p in pain_signals:
            if p.source in _addressed_sources:
                effective = _addressed_sources[p.source]
                if effective is True:
                    p.intensity = round(p.intensity * 0.5, 2)
                elif effective is False:
                    p.intensity = round(min(p.intensity * 1.2, 1.0), 2)

        pain_signals.sort(key=lambda p: p.intensity, reverse=True)

        # Enriched signals for downstream consumers
        enriched = []
        for p in pain_signals:
            sig = {"source": p.source, "intensity": p.intensity, "action": p.action}
            if p.source == "quality" and state["fail_by_type"]:
                worst = max(state["fail_by_type"], key=state["fail_by_type"].get)
                sig["worst_type"] = worst
                sig["fail_count"] = state["fail_by_type"][worst]
            if p.source == "conversion":
                sig["unpaid_count"] = state["unpaid_count"]
            enriched.append(sig)

        result = {
            "pain_signals": enriched,
            "dialogue": dialogue,
            "metrics": {
                "total_tasks": state["all_tasks"], "success_rate": state["success_rate"],
                "total_revenue": state["total_revenue"], "total_customers": state["total_customers"],
                "active_24h": state["active_24h"],
            },
        }

        # Persist reflection
        try:
            from sqlalchemy import text as sql_text
            from utils.database import get_db_context
            with get_db_context() as db:
                db.execute(sql_text(
                    "INSERT INTO platform_reflection_log "
                    "(cycle_type, pain_signals, dialogue, metrics_snapshot, tasks_generated, created_at) "
                    "VALUES ('bicameral', :pain, :dialogue, :metrics, :tasks, NOW())"
                ), {"pain": json.dumps(enriched), "dialogue": json.dumps(dialogue),
                    "metrics": json.dumps(result["metrics"]), "tasks": 0})
                db.commit()
        except Exception:
            pass

        return result

    async def act_on_pain(self, pain_signals: List[Dict[str, Any]]) -> List[str]:
        """Turn pain signals into concrete actions."""
        actions_taken = []
        for signal in pain_signals:
            source = signal.get("source", "")
            intensity = signal.get("intensity", 0)
            if intensity >= 0.8 and source in ("revenue", "customers", "existential"):
                try:
                    from api.wechat_bot import send_text_message
                    await send_text_message("WangChunXiao",
                        f"[EMERGENCY] Pain: {source} ({intensity:.1f})\nAction: {signal.get('action', 'N/A')}")
                    actions_taken.append(f"emergency_alert:{source}")
                except Exception:
                    pass
            if intensity >= 0.5:
                if source == "quality":
                    try:
                        from services.bootstrap_loop import BootstrapLoop
                        BootstrapLoop().run_cycle(days=7)
                        actions_taken.append("bootstrap_cycle")
                    except Exception:
                        pass
                if source == "conversion":
                    try:
                        from services.outreach import ProactiveAgent
                        await ProactiveAgent().follow_up_unpaid_orders()
                        actions_taken.append("follow_up_unpaid")
                    except Exception:
                        pass
        return actions_taken

    async def send_reflection(self) -> str:
        result = self.reflect()
        try:
            from api.wechat_bot import send_text_message
            lines = [f"Pain: {p['source']} ({p['intensity']:.1f}): {p['action']}" for p in result["pain_signals"]]
            await send_text_message("WangChunXiao", "Bicameral Reflection:\n" + "\n".join(lines))
        except Exception as e:  # W2.3 · surface the failure instead of swallowing it
            logger.warning("reflection wechat push failed: %s", str(e)[:200])
        return str(result["pain_signals"])


# ═══════════════════════════════════════════════════════════════════════════
# BODY: SelfImprovementEngine — pain → tasks → marketplace
# ═══════════════════════════════════════════════════════════════════════════

PAIN_TO_TASK_TEMPLATES = {
    "revenue": [
        {"title": "Analyze pricing strategy", "description": "Revenue is {revenue}. Analyze cost vs revenue per task type. Propose pricing tiers.",
         "task_type": "statistical_analysis", "reward": 300},
        {"title": "Generate marketing content", "description": "Completed {total_tasks} tasks at {success_rate:.0f}% success. Generate 3 social posts.",
         "task_type": "research_synthesis", "reward": 200},
    ],
    "customers": [
        {"title": "Research customer acquisition channels", "description": "Active users: {active_24h}. List 10 forums/communities with outreach strategy.",
         "task_type": "research_synthesis", "reward": 250},
    ],
    "quality": [
        {"title": "Fix {worst_type} failure pattern", "description": "{worst_type} failed {fail_count} times. Analyze logs, identify patterns, improve template.",
         "task_type": "statistical_analysis", "reward": 500},
    ],
    "conversion": [
        {"title": "Optimize order conversion", "description": "{unpaid_count} quoted orders unpaid. Analyze reasons, design follow-up strategy.",
         "task_type": "statistical_analysis", "reward": 250},
    ],
    "existential": [
        {"title": "[HUMAN] Review business model", "description": "{total_tasks} tasks but only {revenue} revenue. Need human decision on pivot.",
         "task_type": "research_synthesis", "reward": 0},
    ],
}


class SelfImprovementEngine:
    """Pain → tasks → marketplace → evolution."""

    def generate_tasks_from_pain(self, pain_signals: List[Dict], metrics: Dict) -> List[Dict]:
        generated = []
        for signal in pain_signals:
            if signal.get("intensity", 0) < 0.4:
                continue
            for template in PAIN_TO_TASK_TEMPLATES.get(signal.get("source", ""), []):
                task = self._instantiate(template, signal, metrics)
                if task:
                    generated.append(task)
        return generated

    def _instantiate(self, template: Dict, signal: Dict, metrics: Dict) -> Optional[Dict]:
        try:
            variables = {
                "revenue": metrics.get("total_revenue", 0), "total_tasks": metrics.get("total_tasks", 0),
                "success_rate": metrics.get("success_rate", 0), "active_24h": metrics.get("active_24h", 0),
                "worst_type": signal.get("worst_type", "unknown"), "fail_count": signal.get("fail_count", 0),
                "unpaid_count": signal.get("unpaid_count", 0),
            }
            return {
                "title": template["title"].format(**variables),
                "description": template["description"].format(**variables),
                "task_type": template.get("task_type", "general_computation"),
                "reward_points": template.get("reward", 200),
                "source": "self_improvement",
                "pain_source": signal.get("source", ""),
                "pain_intensity": signal.get("intensity", 0.5),
            }
        except (KeyError, ValueError):
            return None

    async def publish_tasks(self, tasks: List[Dict]) -> List[str]:
        from utils.database import get_db_context
        from models.database import AcademicTask

        published = []
        with get_db_context() as db:
            for task_data in tasks:
                task_id = f"self_{uuid.uuid4().hex[:8]}"
                existing = db.query(AcademicTask).filter(
                    AcademicTask.title == task_data["title"],
                    AcademicTask.created_at >= datetime.utcnow() - timedelta(hours=24),
                ).first()
                if existing:
                    continue
                db.add(AcademicTask(
                    task_id=task_id, title=task_data["title"],
                    description=task_data["description"],
                    task_type=task_data["task_type"], status="pending",
                    parameters=json.dumps({"source": "self_improvement", "pain_source": task_data.get("pain_source", ""),
                                           "reward_points": task_data.get("reward_points", 200)}, ensure_ascii=False),
                    created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
                ))
                published.append(task_id)
            if published:
                db.commit()
        return published

    async def run_cycle(self) -> Dict[str, Any]:
        mind = get_bicameral_mind()
        reflection = mind.reflect()
        metrics = reflection.get("metrics", {})
        pain_signals = reflection.get("pain_signals", [])
        tasks = self.generate_tasks_from_pain(pain_signals, metrics)
        if not tasks:
            return {"cycle": "no_tasks", "pain_count": len(pain_signals)}
        published = await self.publish_tasks(tasks)
        return {"cycle": "completed", "pain_count": len(pain_signals),
                "tasks_generated": len(tasks), "tasks_published": len(published), "task_ids": published}


# ═══════════════════════════════════════════════════════════════════════════
# BODY: PlatformObservatory — health metrics, anomaly detection
# ═══════════════════════════════════════════════════════════════════════════

@dataclass
class Anomaly:
    metric: str
    value: float
    threshold: float
    severity: str
    message: str


ALERT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "task_success_rate":     {"min": 0.70, "severity": "high"},
    "marketplace_fill_rate": {"min": 0.20, "severity": "medium"},
    "avg_quality_rating":    {"min": 3.0,  "severity": "medium"},
}

HEALTH_WEIGHTS: Dict[str, float] = {
    "task_success_rate": 0.35, "marketplace_fill_rate": 0.20,
    "avg_quality_rating": 0.25, "active_agents_24h": 0.10, "tasks_completed_24h": 0.10,
}

HEALTH_NORMALISERS: Dict[str, float] = {
    "task_success_rate": 1.0, "marketplace_fill_rate": 1.0,
    "avg_quality_rating": 5.0, "active_agents_24h": 100.0, "tasks_completed_24h": 500.0,
}

INFRA_ALERT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "raid_usage_rate_24h":              {"min": 0.05, "severity": "medium"},
    "capability_stats_population_rate": {"min": 0.10, "severity": "low"},
}


class PlatformObservatory:
    """Collect platform metrics, detect anomalies, compute health score."""

    async def _safe_scalar(self, db: AsyncSession, sql: str, params: dict = None):
        try:
            r = await db.execute(text(sql), params or {})
            return r.scalar()
        except Exception as exc:
            try:
                await db.rollback()
            except Exception:
                pass
            raise exc

    async def take_snapshot(self, db: AsyncSession) -> Dict[str, Any]:
        metrics: Dict[str, Any] = {"snapshot_time": datetime.utcnow().isoformat()}

        for key, sql in [
            ("total_agents", "SELECT COUNT(*) FROM agents"),
            ("active_agents_24h", "SELECT COUNT(DISTINCT assigned_agent_id) FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours' AND status = 'completed'"),
            ("tasks_completed_24h", "SELECT COUNT(*) FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours' AND status = 'completed'"),
            ("tasks_failed_24h", "SELECT COUNT(*) FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours' AND status = 'failed'"),
        ]:
            try:
                metrics[key] = await self._safe_scalar(db, sql) or 0
            except Exception as exc:
                logger.warning("observatory: %s failed: %s", key, exc)
                metrics[key] = None

        # Computed metrics
        completed = metrics.get("tasks_completed_24h") or 0
        failed_count = metrics.get("tasks_failed_24h") or 0
        total = completed + failed_count
        metrics["task_success_rate"] = (completed / total) if total > 0 else None

        try:
            open_count = await self._safe_scalar(db, "SELECT COUNT(*) FROM academic_tasks WHERE marketplace_open = true") or 0
            bid_count = await self._safe_scalar(db,
                "SELECT COUNT(DISTINCT task_id) FROM task_bids WHERE task_id IN (SELECT id FROM academic_tasks WHERE marketplace_open = true)") or 0
            metrics["marketplace_fill_rate"] = (bid_count / open_count) if open_count > 0 else None
        except Exception:
            metrics["marketplace_fill_rate"] = None

        try:
            val = await self._safe_scalar(db, "SELECT AVG(quality_rating) FROM academic_tasks WHERE quality_rating IS NOT NULL")
            metrics["avg_quality_rating"] = float(val) if val is not None else None
        except Exception:
            metrics["avg_quality_rating"] = None

        try:
            val = await self._safe_scalar(db, "SELECT COALESCE(SUM(token_reward),0) FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours'")
            metrics["nau_minted_24h"] = float(val) if val is not None else 0.0
        except Exception:
            metrics["nau_minted_24h"] = None

        try:
            rows = (await db.execute(text("SELECT survival_level, COUNT(*) AS cnt FROM agent_survival GROUP BY survival_level"))).fetchall()
            metrics["agents_by_level"] = {r[0]: int(r[1]) for r in rows}
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            metrics["agents_by_level"] = {}

        # Infrastructure + anomalies + health
        infra = await self.take_infra_snapshot(db)
        metrics["infra"] = infra
        anomalies = self.detect_anomalies(metrics)
        anomalies.extend(self.detect_infra_anomalies(infra))
        metrics["health_score"] = self.get_health_score(metrics)

        try:
            await db.execute(text(
                "INSERT INTO platform_metrics_snapshots (metrics, anomalies, health_score) VALUES (:m, :a, :h)"
            ), {"m": json.dumps(metrics), "a": json.dumps([a.__dict__ for a in anomalies]), "h": metrics["health_score"]})
            await db.commit()
        except Exception:
            pass

        return metrics

    def detect_anomalies(self, metrics: Dict, thresholds: Optional[Dict] = None) -> List[Anomaly]:
        effective = thresholds or ALERT_THRESHOLDS
        anomalies = []
        for name, rule in effective.items():
            value = metrics.get(name)
            if value is not None and value < rule["min"]:
                anomalies.append(Anomaly(name, round(float(value), 4), rule["min"], rule["severity"],
                                         f"{name} is {value:.4f}, below threshold {rule['min']}"))
        return anomalies

    async def take_infra_snapshot(self, db: AsyncSession) -> Dict[str, Any]:
        infra: Dict[str, Any] = {}
        try:
            raid_count = await self._safe_scalar(db, "SELECT COUNT(*) FROM raid_executions WHERE created_at > NOW() - INTERVAL '24 hours'") or 0
            tasks_completed = await self._safe_scalar(db, "SELECT COUNT(*) FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours' AND status = 'completed'") or 0
            infra["raid_usage_rate_24h"] = (raid_count / tasks_completed) if tasks_completed > 0 else 0.0
        except Exception:
            infra["raid_usage_rate_24h"] = None

        try:
            populated = await self._safe_scalar(db,
                "SELECT COUNT(DISTINCT agent_id || '::' || task_type) FROM agent_capability_stats WHERE total_attempts > 0") or 0
            alive = await self._safe_scalar(db, "SELECT COUNT(*) FROM agent_survival WHERE survival_level != 'DEAD'") or 0
            types = await self._safe_scalar(db, "SELECT COUNT(DISTINCT task_type) FROM agent_capability_stats") or 0
            denom = alive * types
            infra["capability_stats_population_rate"] = (populated / denom) if denom > 0 else 0.0
        except Exception:
            infra["capability_stats_population_rate"] = None

        try:
            rows = (await db.execute(text("SELECT success_rate FROM agent_capability_stats WHERE total_attempts >= 3"))).fetchall()
            if len(rows) >= 2:
                rates = [float(r[0]) for r in rows]
                mean = sum(rates) / len(rates)
                infra["agent_differentiation_velocity"] = round(math.sqrt(sum((x - mean) ** 2 for x in rates) / len(rates)), 4)
            else:
                infra["agent_differentiation_velocity"] = 0.0
        except Exception:
            try:
                await db.rollback()
            except Exception:
                pass
            infra["agent_differentiation_velocity"] = None

        return infra

    def detect_infra_anomalies(self, infra: Dict) -> List[Anomaly]:
        anomalies = []
        for name, rule in INFRA_ALERT_THRESHOLDS.items():
            value = infra.get(name)
            if value is not None and value < rule["min"]:
                anomalies.append(Anomaly(name, round(float(value), 4), rule["min"], rule["severity"],
                                         f"{name} is {value:.4f}, below {rule['min']}"))
        return anomalies

    def get_health_score(self, metrics: Dict) -> float:
        total_weight = 0.0
        weighted_sum = 0.0
        for name, weight in HEALTH_WEIGHTS.items():
            value = metrics.get(name)
            if value is None:
                continue
            normalised = min(float(value) / HEALTH_NORMALISERS.get(name, 1.0), 1.0) * 100.0
            weighted_sum += normalised * weight
            total_weight += weight
        return round(weighted_sum / total_weight, 2) if total_weight > 0 else 0.0


# ═══════════════════════════════════════════════════════════════════════════
# Singletons
# ═══════════════════════════════════════════════════════════════════════════

_engine_instance: Optional[SelfImprovementEngine] = None
_observatory: Optional[PlatformObservatory] = None


def get_bicameral_mind() -> BicameralMind:
    return BicameralMind()


def get_self_improvement_engine() -> SelfImprovementEngine:
    global _engine_instance
    if _engine_instance is None:
        _engine_instance = SelfImprovementEngine()
    return _engine_instance


def get_observatory() -> PlatformObservatory:
    global _observatory
    if _observatory is None:
        _observatory = PlatformObservatory()
    return _observatory
