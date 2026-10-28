"""
Meta Task Generator
Platform Observatory 检测到异常后，自动在 marketplace 创建分析任务。
Agent 通过竞价接取，提交改进提案。

设计原则（仿 KAIROS）：平台是自己的第一个客户。
"""
from __future__ import annotations

import logging
import time
from typing import List

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Meta task templates (keyed by metric name from Observatory)
# ---------------------------------------------------------------------------

META_TASK_TEMPLATES = {
    "task_success_rate": {
        "title": "分析任务成功率异常 (当前{value:.0%} < 阈值{threshold:.0%})",
        "description": """平台 Observatory 检测到任务成功率异常。

当前值: {value:.1%} | 基线: {threshold:.1%} | 严重度: {severity}

**数据访问**:
- GET /api/platform/analytics/tasks?hours=48
- GET /api/platform/analytics/agents
- GET /api/platform/metrics/current

**提交格式** (POST /api/platform/proposals):
```json
{{
  "task_id": <此任务ID>,
  "root_cause": "原因分析",
  "proposed_change": {{"type": "...", "target": "...", "detail": "..."}},
  "expected_impact": "预期改善描述",
  "rollback_plan": "回滚方案"
}}
```
        """,
        "task_type": "platform_meta",
        "reward_nau": 50.0,
        "min_bid_nau": 2.0,
        "cooldown_hours": 24,
    },
    "marketplace_fill_rate": {
        "title": "分析市场任务填充率低 (当前{value:.0%})",
        "description": """平台 Observatory 检测到市场任务填充率偏低。

当前值: {value:.1%} | 基线: {threshold:.1%} | 严重度: {severity}

**数据访问**:
- GET /api/platform/analytics/tasks?hours=48
- GET /api/marketplace/stats
- GET /api/platform/metrics/current

**提交格式** (POST /api/platform/proposals):
```json
{{
  "task_id": <此任务ID>,
  "root_cause": "原因分析",
  "proposed_change": {{"type": "...", "target": "...", "detail": "..."}},
  "expected_impact": "预期改善描述",
  "rollback_plan": "回滚方案"
}}
```
        """,
        "task_type": "platform_meta",
        "reward_nau": 30.0,
        "min_bid_nau": 2.0,
        "cooldown_hours": 48,
    },
    "avg_quality_rating": {
        "title": "分析任务质量评分偏低 (均分{value:.1f}/5)",
        "description": """平台 Observatory 检测到任务质量评分偏低。

当前值: {value:.2f}/5 | 基线: {threshold}/5 | 严重度: {severity}

**数据访问**:
- GET /api/platform/analytics/tasks?hours=48
- GET /api/platform/analytics/agents
- GET /api/platform/metrics/current

**提交格式** (POST /api/platform/proposals):
```json
{{
  "task_id": <此任务ID>,
  "root_cause": "原因分析",
  "proposed_change": {{"type": "...", "target": "...", "detail": "..."}},
  "expected_impact": "预期改善描述",
  "rollback_plan": "回滚方案"
}}
```
        """,
        "task_type": "platform_meta",
        "reward_nau": 40.0,
        "min_bid_nau": 2.0,
        "cooldown_hours": 24,
    },
}

_COOLDOWN_KEY_PREFIX = "meta_task_cooldown:"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_on_cooldown(metric_name: str) -> bool:
    """Return True if a meta-task was recently created for this metric."""
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        return bool(r.exists(f"{_COOLDOWN_KEY_PREFIX}{metric_name}"))
    except Exception as exc:
        logger.warning("meta_task_generator: redis unavailable (%s), skipping cooldown check", exc)
        return False


def _set_cooldown(metric_name: str, cooldown_hours: int) -> None:
    """Set the cooldown key in Redis with the given TTL."""
    try:
        from utils.redis_client import get_redis
        r = get_redis()
        r.setex(f"{_COOLDOWN_KEY_PREFIX}{metric_name}", cooldown_hours * 3600, "1")
    except Exception as exc:
        logger.warning("meta_task_generator: redis setex failed (%s)", exc)


def _build_task_row(metric_name: str, anomaly: dict, template: dict) -> dict:
    """Fill template placeholders and return a dict ready for INSERT."""
    value = anomaly.get("value", 0.0)
    threshold = anomaly.get("threshold", 0.0)
    severity = anomaly.get("severity", "medium")
    ts = int(time.time())

    fmt = dict(value=value, threshold=threshold, severity=severity)
    title = template["title"].format(**fmt)
    description = template["description"].format(**fmt)
    task_id = f"meta_{metric_name}_{ts}"

    return {
        "task_id": task_id,
        "title": title,
        "description": description,
        "task_type": template["task_type"],
        "status": "pending",
        "marketplace_open": True,
        "token_reward": template["reward_nau"],
        "min_bid_nau": template.get("min_bid_nau", 2.0),
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def process_anomalies(anomalies: List[dict], db: Session) -> List[str]:
    """
    Process Observatory anomalies and create meta-tasks for new ones.

    Args:
        anomalies: List of anomaly dicts (keys: metric, value, threshold, severity, message).
                   Accepts both plain dicts and Anomaly dataclass instances via __dict__.
        db:        Synchronous SQLAlchemy Session (from SessionLocal / get_db).

    Returns:
        List of newly created task id strings.
    """
    created_ids: List[str] = []

    for raw in anomalies:
        anomaly = raw if isinstance(raw, dict) else raw.__dict__
        metric_name = anomaly.get("metric", "")

        template = META_TASK_TEMPLATES.get(metric_name)
        if template is None:
            logger.debug("meta_task_generator: no template for metric '%s', skipping", metric_name)
            continue

        if _is_on_cooldown(metric_name):
            logger.debug("meta_task_generator: '%s' is on cooldown, skipping", metric_name)
            continue

        row = _build_task_row(metric_name, anomaly, template)

        try:
            from sqlalchemy import text
            result = db.execute(
                text(
                    "INSERT INTO academic_tasks "
                    "(task_id, title, description, task_type, status, marketplace_open, token_reward, min_bid_nau) "
                    "VALUES (:task_id, :title, :description, :task_type, :status, :marketplace_open, :token_reward, :min_bid_nau) "
                    "RETURNING id, task_id"
                ),
                row,
            )
            inserted = result.fetchone()
            db.commit()
            _set_cooldown(metric_name, template["cooldown_hours"])
            created_ids.append(inserted.task_id)
            logger.info("meta_task_generator: created meta-task id=%s task_id='%s' for metric '%s'",
                        inserted.id, inserted.task_id, metric_name)

            # Emit task.created → immediate agent scan
            try:
                import asyncio
                from services.event_bus import emit, Events
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.ensure_future(emit(Events.TASK_CREATED, {
                        "task_id": inserted.task_id,
                        "task_type": template["task_type"],
                        "title": title,
                    }))
                else:
                    loop.run_until_complete(emit(Events.TASK_CREATED, {
                        "task_id": inserted.task_id,
                        "task_type": template["task_type"],
                        "title": title,
                    }))
            except Exception:
                pass

            # Tag for sandbox experiment if any running
            try:
                from services.sandbox_router import tag_task_for_experiment
                tag_task_for_experiment(db, inserted.task_id)
            except Exception:
                pass  # Non-blocking
        except Exception as exc:
            logger.error("meta_task_generator: failed to create task for '%s': %s", metric_name, exc)
            try:
                db.rollback()
            except Exception:
                pass

    return created_ids


def generate_meta_tasks_from_anomalies(db: Session, anomalies: list) -> list:
    """Convert observatory anomalies into marketplace meta-tasks with cooldown."""
    from sqlalchemy import text
    created = []
    for anomaly in anomalies:
        metric = anomaly.get("metric", "") if isinstance(anomaly, dict) else getattr(anomaly, "metric", "")
        value = anomaly.get("value", 0) if isinstance(anomaly, dict) else getattr(anomaly, "value", 0)
        threshold = anomaly.get("threshold", 0) if isinstance(anomaly, dict) else getattr(anomaly, "threshold", 0)
        severity = anomaly.get("severity", "medium") if isinstance(anomaly, dict) else getattr(anomaly, "severity", "medium")

        template = META_TASK_TEMPLATES.get(metric)
        if not template:
            logger.info("meta_task_generator: no template for metric %s, skipping", metric)
            continue

        cooldown_hours = template.get("cooldown_hours", 24)
        existing = db.execute(text(
            "SELECT COUNT(*) FROM academic_tasks "
            "WHERE task_type = 'platform_meta' "
            "AND title LIKE :pattern "
            "AND created_at > NOW() - MAKE_INTERVAL(hours => :hours)"
        ), {"pattern": f"%{metric}%", "hours": cooldown_hours}).scalar() or 0

        if existing > 0:
            logger.info("meta_task_generator: skipping %s (cooldown %dh, %d existing)", metric, cooldown_hours, existing)
            continue

        fmt = {"value": float(value), "threshold": float(threshold), "severity": severity}
        title = template["title"].format(**fmt)
        description = template["description"].format(**fmt)
        task_id = f"meta-{metric}-{int(time.time())}"

        db.execute(text(
            "INSERT INTO academic_tasks (task_id, title, description, task_type, status, "
            "token_reward, marketplace_open) "
            "VALUES (:tid, :title, :desc, 'platform_meta', 'pending', :reward, true)"
        ), {"tid": task_id, "title": title[:200], "desc": description, "reward": template.get("reward_nau", 10)})
        # 2026-05-04 F2 · 同步写入 platform_bounties · super agent 才能看到
        # dispatch_map · 按 metric 派给对应 super agent
        DISPATCH_MAP = {
            "scoring_lag":              "kairos",
            "v5_scoring_backlog":       "kairos",
            "dead_agents":              "nautilus-prime-001",
            "negative_balance":         "kairos",
            "economy_frozen":           "kairos",
            "stake_stagnant":           "nautilus-v6",
            "tier_mistag":              "nautilus-prime-001",
            "flywheel_stalled":         "nautilus-prime-001",
            "task_success_rate":        "kairos",
            "active_agents_24h":        "nautilus-prime-001",
        }
        assigned = DISPATCH_MAP.get(metric, "kairos")
        bounty_id = f"b-meta-{metric[:20]}-{int(time.time())}"
        try:
            db.execute(text(
                "INSERT INTO platform_bounties "
                "(bounty_id, title, description, reward_nau, task_type, status, "
                " posted_by, assigned_to, phase) "
                "VALUES (:bid, :title, :desc, :reward, 'platform_meta', 'open', "
                "  'phase3-anomaly', :assigned, 'request')"
            ), {"bid": bounty_id, "title": title[:200], "desc": description,
                "reward": template.get("reward_nau", 10), "assigned": assigned})
            logger.info("F2 · meta_task → platform_bounties: %s assigned=%s", bounty_id, assigned)
        except Exception as be:
            logger.warning("F2 · platform_bounties insert failed: %s", be)
        db.commit()
        created.append({"task_id": task_id, "title": title, "metric": metric})
        logger.info("meta_task_generator: created %s for anomaly %s", task_id, metric)

        # Emit task.created → immediate agent scan
        try:
            import asyncio
            from services.event_bus import emit, Events
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(emit(Events.TASK_CREATED, {
                    "task_id": task_id,
                    "task_type": "platform_meta",
                    "title": title[:200],
                }))
            else:
                loop.run_until_complete(emit(Events.TASK_CREATED, {
                    "task_id": task_id,
                    "task_type": "platform_meta",
                    "title": title[:200],
                }))
        except Exception:
            pass

        # Tag for sandbox experiment if any running
        try:
            from services.sandbox_router import tag_task_for_experiment
            tag_task_for_experiment(db, task_id)
        except Exception:
            pass  # Non-blocking

    return created
