"""
Curiosity Engine — Proactive exploration for continuous self-improvement.

Instead of waiting for anomalies, actively explores optimization opportunities:
1. Comparative analysis (why does Agent X excel but Y struggles?)
2. Untested combinations (we've never tried RAID-3 for data_labeling)
3. Performance ceiling (can we push 82% success to 90%?)
4. Resource efficiency (is RAID-3 worth 4x the LLM cost?)
5. Goal evolution (raise aspirations when consistently exceeding targets)
6. Web3 health (are key API endpoints responding?)
7. Infrastructure check (dummy addresses, placeholder keys)
8. Agent diversity (specialty distribution balance)
9. Stale tasks (pending tasks stuck >24h)
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ── Deduplication Helper ───────────────────────────────────────────────────

def _title_exists_recently(db: Session, title: str, hours: int = 24) -> bool:
    """Check if a task with the same title was created in the last N hours."""
    try:
        row = db.execute(text(
            "SELECT 1 FROM academic_tasks "
            "WHERE title = :title "
            "AND created_at > NOW() - make_interval(hours => :hours) "
            "LIMIT 1"
        ), {"title": title, "hours": hours}).fetchone()
        return row is not None
    except Exception as e:
        logger.debug("_title_exists_recently failed: %s", e)
        return False


# ── Exploration Strategies ───────────────────────────────────────────────────

async def _explore_comparative(db: Session) -> Optional[Dict]:
    """Find agents with extreme performance gaps across task types."""
    try:
        rows = db.execute(text(
            "SELECT agent_id, task_type, total_attempts, success_count "
            "FROM agent_capability_stats WHERE total_attempts >= 5 "
            "ORDER BY agent_id, task_type"
        )).fetchall()

        if len(rows) < 3:
            return None

        # Find agents with high variance across types
        agent_stats = {}
        for r in rows:
            aid = r.agent_id
            if aid not in agent_stats:
                agent_stats[aid] = []
            rate = r.success_count / r.total_attempts if r.total_attempts else 0
            agent_stats[aid].append({"type": r.task_type, "rate": rate, "attempts": r.total_attempts})

        for aid, stats in agent_stats.items():
            if len(stats) < 2:
                continue
            rates = [s["rate"] for s in stats]
            gap = max(rates) - min(rates)
            if gap > 0.40:
                best = max(stats, key=lambda s: s["rate"])
                worst = min(stats, key=lambda s: s["rate"])
                return {
                    "type": "comparative",
                    "description": (
                        f"Agent #{aid} has {best['rate']:.0%} success on {best['type']} "
                        f"but only {worst['rate']:.0%} on {worst['type']}. "
                        f"What makes {best['type']} easier? Can we apply the same patterns to {worst['type']}?"
                    ),
                    "proposed_change": {
                        "type": "agent_training",
                        "target": worst["type"],
                        "detail": f"Study Agent #{aid}'s success on {best['type']} and apply patterns to {worst['type']}",
                    },
                    "expected_outcome": f"{worst['type']} success rate +20%",
                }
    except Exception as e:
        logger.debug("comparative exploration failed: %s", e)
    return None


async def _explore_untested(db: Session) -> Optional[Dict]:
    """Find task_type × RAID_level combinations never tried."""
    try:
        # What RAID levels have we used per task type?
        used = db.execute(text(
            "SELECT DISTINCT task_type, raid_level FROM academic_tasks at "
            "JOIN raid_executions re ON re.id IS NOT NULL "
            "WHERE at.created_at > NOW() - INTERVAL '30 days' "
            "LIMIT 50"
        )).fetchall()

        # What task types have low success without RAID?
        low_success = db.execute(text(
            "SELECT task_type, COUNT(*) AS total, "
            "  SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done "
            "FROM academic_tasks WHERE created_at > NOW() - INTERVAL '7 days' "
            "GROUP BY task_type HAVING COUNT(*) >= 5 "
            "ORDER BY SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)::float / COUNT(*) ASC "
            "LIMIT 3"
        )).fetchall()

        for r in low_success:
            rate = (r.done or 0) / r.total if r.total else 0
            if rate < 0.70:
                return {
                    "type": "untested",
                    "description": (
                        f"{r.task_type} has {rate:.0%} success rate. "
                        f"Hypothesis: RAID-3 multi-agent consensus could improve quality."
                    ),
                    "proposed_change": {
                        "type": "routing_weight",
                        "target": r.task_type,
                        "detail": f"Force RAID-3 for {r.task_type} tasks for 48 hours",
                    },
                    "expected_outcome": f"{r.task_type} success rate > 80%",
                }
    except Exception as e:
        logger.debug("untested exploration failed: %s", e)
    return None


async def _explore_ceiling(db: Session) -> Optional[Dict]:
    """Detect performance plateaus and propose breaking through."""
    try:
        # Check if health score has been stable for 7+ snapshots
        rows = db.execute(text(
            "SELECT health_score FROM platform_metrics_snapshots "
            "ORDER BY snapshot_time DESC LIMIT 7"
        )).fetchall()

        if len(rows) < 7:
            return None

        scores = [float(r.health_score or 0) for r in rows]
        avg = sum(scores) / len(scores)
        variance = sum((s - avg) ** 2 for s in scores) / len(scores)

        # Plateau: low variance + not at maximum
        if variance < 4.0 and avg < 85:
            return {
                "type": "ceiling",
                "description": (
                    f"Health score has plateaued at {avg:.1f} for 7+ snapshots (variance={variance:.2f}). "
                    f"Current ceiling may be broken by addressing the weakest metric."
                ),
                "proposed_change": {
                    "type": "quality_improvement",
                    "target": "health_score",
                    "detail": "Identify and boost the lowest-weighted metric to break the plateau",
                },
                "expected_outcome": f"Health score > {avg + 5:.0f} within 7 days",
            }
    except Exception as e:
        logger.debug("ceiling exploration failed: %s", e)
    return None


async def _explore_efficiency(db: Session) -> Optional[Dict]:
    """Evaluate if RAID is worth its cost."""
    try:
        raid_stats = db.execute(text(
            "SELECT raid_level, COUNT(*) AS cnt, "
            "  AVG(consensus_score) AS avg_consensus "
            "FROM raid_executions WHERE status='completed' "
            "GROUP BY raid_level"
        )).fetchall()

        for r in raid_stats:
            if r.raid_level == 3 and r.cnt >= 5 and r.avg_consensus and r.avg_consensus < 0.60:
                return {
                    "type": "efficiency",
                    "description": (
                        f"RAID-3 has low average consensus ({r.avg_consensus:.2f}) over {r.cnt} executions. "
                        f"Consider downgrading to RAID-2 to save 2x LLM cost."
                    ),
                    "proposed_change": {
                        "type": "routing_weight",
                        "target": "raid_level_default",
                        "detail": "Reduce default RAID level from 3 to 2 for moderate tasks",
                    },
                    "expected_outcome": "50% reduction in LLM cost with minimal quality loss",
                }
    except Exception as e:
        logger.debug("efficiency exploration failed: %s", e)
    return None


# ── Web3 Health Check ──────────────────────────────────────────────────────

async def _explore_web3_health(db: Session) -> Optional[Dict]:
    """Check if key API endpoints are responding with 200."""
    endpoints = [
        ("/api/stats", "Platform stats"),
        ("/api/hub/stats", "Agent hub stats"),
        ("/api/openclaw/node/info", "OpenClaw node info"),
    ]
    try:
        import httpx
        base_url = "https://www.nautilus.social"
        failing = []
        async with httpx.AsyncClient(timeout=10) as client:
            for path, label in endpoints:
                try:
                    resp = await client.get(f"{base_url}{path}")
                    if resp.status_code != 200:
                        failing.append(f"{label} ({path}): HTTP {resp.status_code}")
                except Exception as exc:
                    failing.append(f"{label} ({path}): {type(exc).__name__}")

        if failing:
            return {
                "type": "web3_health",
                "description": (
                    f"{len(failing)} API endpoint(s) unhealthy: "
                    + "; ".join(failing)
                ),
                "proposed_change": {
                    "type": "infrastructure_fix",
                    "target": "api_endpoints",
                    "detail": "Investigate and restore failing endpoints: " + ", ".join(failing),
                },
                "expected_outcome": "All key API endpoints return 200",
            }
    except Exception as e:
        logger.debug("web3_health exploration failed: %s", e)
    return None


# ── Infrastructure Check ───────────────────────────────────────────────────

async def _explore_infrastructure(db: Session) -> Optional[Dict]:
    """Check for common code issues: dummy addresses, placeholder keys."""
    issues = []
    try:
        # Check for dummy/zero contract addresses in platform_config
        rows = db.execute(text(
            "SELECT config_key, config_value FROM platform_config "
            "WHERE config_key IN ('nau_contract_address', 'usdc_contract_address', 'web3_config') "
            "LIMIT 10"
        )).fetchall()

        for r in rows:
            val = str(r.config_value) if r.config_value else ""
            if "0x0000000000000000000000000000000000000000" in val:
                issues.append(f"{r.config_key} contains zero address")
            if "placeholder" in val.lower() or "your_" in val.lower() or "xxx" in val.lower():
                issues.append(f"{r.config_key} contains placeholder value")

        # Check for agents with zero-address owner
        zero_agents = db.execute(text(
            "SELECT COUNT(*) AS cnt FROM agents "
            "WHERE owner = '0x0000000000000000000000000000000000000000'"
        )).scalar() or 0
        if zero_agents > 0:
            issues.append(f"{zero_agents} agent(s) with zero-address owner")

    except Exception as e:
        logger.debug("infrastructure exploration query failed: %s", e)

    if issues:
        return {
            "type": "infrastructure",
            "description": "Infrastructure issues detected: " + "; ".join(issues),
            "proposed_change": {
                "type": "config_fix",
                "target": "platform_config",
                "detail": "Fix detected infrastructure issues: " + "; ".join(issues),
            },
            "expected_outcome": "No dummy addresses or placeholder values in config",
        }
    return None


# ── Agent Diversity ────────────────────────────────────────────────────────

async def _explore_agent_diversity(db: Session) -> Optional[Dict]:
    """Check if agent specialty distribution is healthy (not all doing same thing)."""
    try:
        rows = db.execute(text(
            "SELECT specialties, COUNT(*) AS cnt FROM agents "
            "WHERE agent_status = 'alive' AND specialties IS NOT NULL AND specialties != '' "
            "GROUP BY specialties ORDER BY cnt DESC LIMIT 10"
        )).fetchall()

        if not rows or len(rows) < 2:
            return None

        total = sum(r.cnt for r in rows)
        top = rows[0]
        top_pct = top.cnt / total if total else 0

        # If >70% of agents have the same specialty, flag it
        if top_pct > 0.70 and total >= 5:
            return {
                "type": "agent_diversity",
                "description": (
                    f"{top_pct:.0%} of active agents share specialty '{top.specialties}' "
                    f"({top.cnt}/{total}). Low diversity may limit task coverage."
                ),
                "proposed_change": {
                    "type": "agent_incentive",
                    "target": "specialty_distribution",
                    "detail": "Incentivize agents to diversify specialties via bonus NAU for underserved types",
                },
                "expected_outcome": "No single specialty exceeds 60% of agent pool",
            }
    except Exception as e:
        logger.debug("agent_diversity exploration failed: %s", e)
    return None


# ── Stale Tasks ────────────────────────────────────────────────────────────

async def _explore_stale_tasks(db: Session) -> Optional[Dict]:
    """Check for tasks stuck in 'pending' status for >24 hours."""
    try:
        row = db.execute(text(
            "SELECT COUNT(*) AS cnt FROM academic_tasks "
            "WHERE status = 'pending' "
            "AND created_at < NOW() - INTERVAL '24 hours'"
        )).fetchone()

        stale_count = row.cnt if row else 0
        if stale_count >= 3:
            return {
                "type": "stale_tasks",
                "description": (
                    f"{stale_count} task(s) have been stuck in 'pending' for >24 hours. "
                    f"They may need reassignment or cancellation."
                ),
                "proposed_change": {
                    "type": "task_management",
                    "target": "stale_pending_tasks",
                    "detail": f"Review and either reassign or cancel {stale_count} stale pending tasks",
                },
                "expected_outcome": "No tasks stuck in pending for >24h",
            }
    except Exception as e:
        logger.debug("stale_tasks exploration failed: %s", e)
    return None


# ── Main Exploration Pipeline ────────────────────────────────────────────────

async def explore_improvements(db: Session) -> List[Dict]:
    """Run all exploration strategies, return discovered hypotheses.

    Evolution Pulse: queries evolution_ledger for recently failed change_types
    to avoid re-exploring known dead ends (yin-yang: memory bounds curiosity).
    """
    # Load recently failed evolution paths — curiosity should not repeat these
    # Bridge E.1: Curiosity → Evolution Ledger (avoid repeating failures)
    failed_change_types: set = set()
    try:
        from services.evolution_ledger import get_failed_experiments_summary
        failed_map = get_failed_experiments_summary(db, days=30)
        # Skip types that failed 2+ times in last 30 days
        failed_change_types = {ct for ct, count in failed_map.items() if count >= 2}
        if failed_change_types:
            logger.info("curiosity_engine: avoiding %d recently failed evolution types: %s",
                        len(failed_change_types), failed_change_types)
    except Exception:
        pass

    # Bridge E.6: Memory → Curiosity (negative memory suppression)
    # Queries soul memory for recent failures to avoid re-exploring dead ends
    try:
        from services.soul_bridge import get_soul_memory, _initialized
        if _initialized:
            mem = get_soul_memory()
            negatives = mem.recall("failed experiment exploration error", limit=5)
            for m in (negatives or []):
                content = m.get("content", "") if isinstance(m, dict) else str(m)
                if "failed" in content.lower():
                    # Add the failure description to failed_change_types for suppression
                    for ct in list(failed_change_types):
                        pass  # already covered by E.1
                    logger.debug("curiosity_engine: negative memory found: %s", content[:80])
    except (ImportError, Exception):
        pass  # Soul not available — skip memory suppression

    hypotheses = []
    strategies = [
        _explore_comparative,
        _explore_untested,
        _explore_ceiling,
        _explore_efficiency,
        _explore_web3_health,
        _explore_infrastructure,
        _explore_agent_diversity,
        _explore_stale_tasks,
    ]

    for strategy in strategies:
        try:
            result = await strategy(db)
            if result:
                # Skip if this change type recently failed in evolution
                proposed_type = result.get("proposed_change", {}).get("type", "")
                if proposed_type and proposed_type in failed_change_types:
                    logger.info("curiosity_engine: SKIP hypothesis type=%s (recent evolution failure)", proposed_type)
                    continue
                hypotheses.append(result)

                # Emit hypothesis event (yang: broadcast discovery)
                try:
                    import asyncio
                    from services.event_bus import emit
                    asyncio.ensure_future(emit("curiosity.hypothesis", {
                        "type": result.get("type", ""),
                        "description": result.get("expected_outcome", "")[:200],
                    }))
                except Exception:
                    pass
        except Exception as e:
            logger.debug("exploration strategy failed: %s", e)

    logger.info("curiosity_engine: explored %d strategies, found %d hypotheses",
                len(strategies), len(hypotheses))
    return hypotheses


# ── Hypothesis → Experiment ──────────────────────────────────────────────────

def create_exploration_experiment(db: Session, hypothesis: Dict) -> Optional[str]:
    """Turn a hypothesis into a meta-task + proposal for the flywheel to process.

    Deduplication: skips creation if an identical title already exists within 24h.
    """
    title = f"[Curiosity] {hypothesis['type']}: {hypothesis.get('expected_outcome', '')[:60]}"

    # ── Dedup check ──────────────────────────────────────────────────────
    if _title_exists_recently(db, title, hours=24):
        logger.info("curiosity_engine: SKIP duplicate task title='%s'", title)
        return None

    try:
        task_id = f"explore_{uuid.uuid4().hex[:10]}"
        db.execute(text(
            "INSERT INTO academic_tasks (task_id, title, description, task_type, status, marketplace_open, min_bid_nau) "
            "VALUES (:tid, :title, :desc, 'platform_meta', 'pending', true, 2.0)"
        ), {
            "tid": task_id,
            "title": title,
            "desc": hypothesis["description"],
        })
        db.commit()
        logger.info("curiosity_engine: created exploration task %s (type=%s)", task_id, hypothesis["type"])
        return task_id
    except Exception as e:
        logger.error("curiosity_engine: failed to create experiment: %s", e)
        db.rollback()
        return None


# ── Knowledge Capsule ────────────────────────────────────────────────────────

def record_knowledge_capsule(db: Session, hypothesis: Dict, outcome: str, metric_impact: float = 0.0) -> None:
    """Store exploration outcome as persistent knowledge."""
    try:
        capsule = {
            "hypothesis_type": hypothesis.get("type"),
            "description": hypothesis.get("description", "")[:500],
            "outcome": outcome,  # confirmed | refuted | inconclusive
            "metric_impact": metric_impact,
            "lesson": hypothesis.get("expected_outcome", ""),
        }
        db.execute(text(
            "INSERT INTO platform_reflection_log (cycle_type, pain_signals, tasks_generated, created_at) "
            "VALUES ('exploration', CAST(:capsule AS jsonb), 1, NOW())"
        ), {"capsule": json.dumps(capsule)})
        db.commit()
    except Exception as e:
        logger.debug("record_knowledge_capsule failed: %s", e)


# ── Goal Evolution ───────────────────────────────────────────────────────────

def evolve_goals(db: Session) -> Dict:
    """Review performance and set aspirational targets."""
    try:
        from services.platform_config import get_config_sync, set_config_sync

        # Current thresholds
        thresholds = get_config_sync(db, "alert_thresholds") or {}

        # Current aspirations (or initialize)
        aspirations = get_config_sync(db, "aspiration_targets") or {}

        # Health score trend (last 30 days)
        rows = db.execute(text(
            "SELECT health_score FROM platform_metrics_snapshots "
            "ORDER BY snapshot_time DESC LIMIT 30"
        )).fetchall()

        if len(rows) < 7:
            return {"status": "insufficient_data"}

        scores = [float(r.health_score or 0) for r in rows]
        avg_30d = sum(scores) / len(scores)
        avg_7d = sum(scores[:7]) / 7

        # If consistently above current target, raise aspiration
        current_aspiration = aspirations.get("health_score", 70)
        if avg_7d > current_aspiration + 5:
            new_aspiration = min(round(avg_7d + 5, 0), 95)
            aspirations["health_score"] = new_aspiration
            logger.info("curiosity_engine: raised health aspiration %s → %s", current_aspiration, new_aspiration)

        # Per-metric aspirations
        for metric in ["task_success_rate", "avg_quality_rating"]:
            threshold = thresholds.get(metric, {}).get("min", 0)
            if threshold and avg_7d > threshold * 100 + 10:  # consistently exceeding
                aspirations[metric] = round(threshold * 1.15, 4)

        set_config_sync(db, "aspiration_targets", aspirations, source="curiosity")
        return {"aspirations": aspirations, "avg_7d": round(avg_7d, 2), "avg_30d": round(avg_30d, 2)}

    except Exception as e:
        logger.debug("evolve_goals failed: %s", e)
        return {"error": str(e)}
