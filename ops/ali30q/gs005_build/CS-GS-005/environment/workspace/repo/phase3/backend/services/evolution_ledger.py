"""
Evolution Ledger — 平台进化历史记录
每次沙箱实验 promoted，写入进化账本。
链上合约未部署时，奖励记录在 pending_nau_rewards 表，合约上线后批量 mint。
"""
from __future__ import annotations

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 提案改进→NAU 奖励映射（baseline）
NAU_REWARD_BY_TYPE = {
    "routing_weight": 100.0,    # 调整任务路由权重
    "reward_parameter": 150.0,  # 调整奖励参数
    "threshold_adjust": 80.0,   # 调整阈值
    "default": 50.0,            # 其他类型
}

# 改善幅度奖励乘数（delta 越大，奖励越多）
def _improvement_multiplier(delta: float) -> float:
    if delta >= 0.20:
        return 3.0   # 改善 ≥ 20%，3倍奖励
    elif delta >= 0.10:
        return 2.0   # 改善 ≥ 10%，2倍奖励
    elif delta >= 0.05:
        return 1.5   # 改善 ≥ 5%，1.5倍奖励
    else:
        return 1.0


def record_evolution(db: Session, proposal_id: str, sandbox_result: Dict[str, Any]) -> Optional[str]:
    """
    记录一次成功的平台进化：
    1. 写入 platform_evolution_log
    2. 写入 pending_nau_rewards（给提案者）

    Returns: evolution entry id，失败返回 None
    """
    try:
        # 获取提案详情
        prop = db.execute(text(
            "SELECT id, agent_id, proposed_change FROM platform_improvement_proposals WHERE id=:id"
        ), {"id": proposal_id}).fetchone()
        if not prop:
            logger.warning("evolution_ledger: proposal %s not found", proposal_id)
            return None

        pc = prop.proposed_change or {}
        if isinstance(pc, str):
            import json as _json
            pc = _json.loads(pc)

        change_type = pc.get("type", "default")
        delta = sandbox_result.get("delta", 0.0)

        # 计算 NAU 奖励
        base_nau = NAU_REWARD_BY_TYPE.get(change_type, NAU_REWARD_BY_TYPE["default"])
        nau_reward = round(base_nau * _improvement_multiplier(delta), 2)

        # 计算版本号：当前最大 minor_version + 1
        last_version = db.execute(text(
            "SELECT minor_version FROM platform_evolution_log ORDER BY minor_version DESC LIMIT 1"
        )).scalar()
        next_minor = (last_version or 0) + 1
        version_str = f"v1.{next_minor}"

        entry_id = f"evo_{next_minor:04d}"

        db.execute(text(
            """INSERT INTO platform_evolution_log
               (id, proposal_id, proposer_agent_id, version_str, minor_version,
                change_type, proposed_change, sandbox_result, metric_delta,
                nau_rewarded, status)
               VALUES (:id, :proposal_id, :proposer_agent_id, :version_str, :minor_version,
                       :change_type, CAST(:proposed_change AS jsonb), CAST(:sandbox_result AS jsonb),
                       :metric_delta, :nau_rewarded, 'active')"""
        ), {
            "id": entry_id,
            "proposal_id": proposal_id,
            "proposer_agent_id": prop.agent_id,
            "version_str": version_str,
            "minor_version": next_minor,
            "change_type": change_type,
            "proposed_change": json.dumps(pc),
            "sandbox_result": json.dumps(sandbox_result),
            "metric_delta": delta,
            "nau_rewarded": nau_reward,
        })

        # 写入 pending NAU 奖励（待合约部署后 mint）
        db.execute(text(
            """INSERT INTO pending_nau_rewards
               (agent_id, amount, reason, source_id, status)
               VALUES (:agent_id, :amount, :reason, :source_id, 'pending')"""
        ), {
            "agent_id": prop.agent_id,
            "amount": nau_reward,
            "reason": f"Platform improvement proposal {proposal_id} promoted ({version_str})",
            "source_id": entry_id,
        })

        db.commit()
        logger.info(
            "evolution_ledger: recorded %s (proposal=%s, delta=%.3f, nau=%.1f)",
            entry_id, proposal_id, delta, nau_reward
        )

        # Evolution Pulse: broadcast so curiosity engine learns from this evolution
        try:
            import asyncio
            from services.event_bus import emit
            asyncio.ensure_future(emit("evolution.recorded", {
                "evolution_id": entry_id,
                "proposal_id": proposal_id,
                "change_type": change_type,
                "delta": delta,
                "nau_reward": nau_reward,
                "version": version_str,
            }))
        except Exception:
            pass

        return entry_id

    except Exception as e:
        logger.error("evolution_ledger: record_evolution failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def apply_evolution(db: Session, proposed_change: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """
    Actually APPLY a promoted evolution to the platform.

    Depending on proposed_change["type"], this function creates real side-effects:
      - agent_training:      create training tasks in academic_tasks
      - routing_weight:      store updated weight in platform_evolution_log config
      - adjust_threshold:    update Observatory ALERT_THRESHOLDS at runtime
      - quality_improvement: create a review/audit meta-task
      - reward_parameters:   log for manual intervention (needs careful review)
      - task_template:       log for manual intervention

    Returns a summary dict of what was applied.
    """
    change_type = proposed_change.get("type", "unknown")
    detail = proposed_change.get("detail", "")
    target = proposed_change.get("target", "")
    result = {"type": change_type, "applied": False, "actions": []}

    try:
        if change_type == "agent_training":
            result = _apply_agent_training(db, proposed_change, proposal_id)

        elif change_type == "routing_weight":
            result = _apply_routing_weight(db, proposed_change, proposal_id)

        elif change_type == "adjust_threshold":
            result = _apply_threshold_adjustment(db, proposed_change, proposal_id)

        elif change_type == "quality_improvement":
            result = _apply_quality_improvement(db, proposed_change, proposal_id)

        else:
            # reward_parameters, task_template, unknown — log for manual review
            result = _apply_manual_review(db, proposed_change, proposal_id)

        logger.info(
            "apply_evolution: type=%s proposal=%s applied=%s actions=%s",
            change_type, proposal_id, result.get("applied"), result.get("actions"),
        )
    except Exception as e:
        logger.error("apply_evolution failed for proposal %s: %s", proposal_id, e)
        result["error"] = str(e)
        try:
            db.rollback()
        except Exception:
            pass

    return result


def _apply_agent_training(db: Session, pc: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """Create training tasks targeting the weak area identified by the proposal."""
    import uuid
    import time

    detail = pc.get("detail", "Improve agent performance")
    target = pc.get("target", "task_success_rate")
    ts = int(time.time())

    # Create 3 training tasks for the identified weak area
    created_ids = []
    for i in range(3):
        task_id = f"train_{proposal_id[:8]}_{ts}_{i}"
        title = f"Training: {target} improvement ({i+1}/3)"
        description = (
            f"Auto-generated training task from promoted evolution (proposal {proposal_id}).\n\n"
            f"Focus area: {target}\n"
            f"Guidance: {detail}\n\n"
            f"Complete this task to practice and improve the targeted capability."
        )
        try:
            db.execute(text(
                "INSERT INTO academic_tasks "
                "(task_id, title, description, task_type, status, marketplace_open, token_reward, min_bid_nau) "
                "VALUES (:task_id, :title, :description, 'platform_meta', 'pending', true, 5.0, 1.0)"
            ), {"task_id": task_id, "title": title[:200], "description": description})
            created_ids.append(task_id)
        except Exception as e:
            logger.warning("apply_evolution: failed to create training task %s: %s", task_id, e)

    if created_ids:
        db.commit()

    return {"type": "agent_training", "applied": bool(created_ids), "actions": created_ids}


def _apply_routing_weight(db: Session, pc: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """Read routing_weights from platform_config, merge the new weight, and write back."""
    from services.platform_config import get_config_sync, set_config_sync

    detail = pc.get("detail", "")
    target = pc.get("target", "")

    current = get_config_sync(db, "routing_weights") or {}
    current[target] = detail
    set_config_sync(db, "routing_weights", current, source="evolution", source_id=proposal_id)

    return {
        "type": "routing_weight",
        "applied": True,
        "actions": [f"routing_weights['{target}'] updated in platform_config"],
    }


def _apply_threshold_adjustment(db: Session, pc: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """Read alert_thresholds from platform_config, update the target metric, and write back."""
    from services.platform_config import get_config_sync, set_config_sync

    target = pc.get("target", "")
    detail = pc.get("detail", "")
    actions = []

    new_threshold = _extract_threshold_value(detail)

    if not target or new_threshold is None:
        actions.append(f"Could not parse threshold from detail, logged for manual review: {detail[:120]}")
        return {"type": "adjust_threshold", "applied": False, "actions": actions}

    current = get_config_sync(db, "alert_thresholds") or {}
    old_entry = current.get(target, {})
    old_val = old_entry.get("min") if isinstance(old_entry, dict) else None

    current[target] = {"min": new_threshold, "severity": old_entry.get("severity", "medium") if isinstance(old_entry, dict) else "medium"}
    set_config_sync(db, "alert_thresholds", current, source="evolution", source_id=proposal_id)

    if old_val is not None:
        actions.append(f"Updated alert_thresholds['{target}'].min: {old_val} -> {new_threshold}")
    else:
        actions.append(f"Added new threshold: {target} min={new_threshold}")

    # Also update in-memory ALERT_THRESHOLDS if observatory is loaded
    try:
        from services.observatory import ALERT_THRESHOLDS
        ALERT_THRESHOLDS[target] = current[target]
    except ImportError:
        pass

    return {
        "type": "adjust_threshold",
        "applied": True,
        "actions": actions,
    }


def _apply_quality_improvement(db: Session, pc: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """Create a meta-task that instructs agents to add review steps."""
    import time

    detail = pc.get("detail", "Add quality review steps")
    target = pc.get("target", "avg_quality_rating")
    ts = int(time.time())
    task_id = f"qimprove_{proposal_id[:8]}_{ts}"

    title = f"Quality improvement: {target}"
    description = (
        f"Auto-generated quality improvement task from promoted evolution (proposal {proposal_id}).\n\n"
        f"Target metric: {target}\n"
        f"Required action: {detail}\n\n"
        f"Implement the suggested quality improvement and verify results."
    )

    try:
        db.execute(text(
            "INSERT INTO academic_tasks "
            "(task_id, title, description, task_type, status, marketplace_open, token_reward, min_bid_nau) "
            "VALUES (:task_id, :title, :description, 'platform_meta', 'pending', true, 10.0, 2.0)"
        ), {"task_id": task_id, "title": title[:200], "description": description})
        db.commit()
        return {"type": "quality_improvement", "applied": True, "actions": [task_id]}
    except Exception as e:
        logger.warning("apply_evolution: failed to create quality task: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return {"type": "quality_improvement", "applied": False, "actions": [], "error": str(e)}


def _apply_manual_review(db: Session, pc: Dict[str, Any], proposal_id: str) -> Dict[str, Any]:
    """For types that need human/manual intervention, create a notification task."""
    import time

    change_type = pc.get("type", "unknown")
    detail = pc.get("detail", "")
    target = pc.get("target", "")
    ts = int(time.time())
    task_id = f"review_{proposal_id[:8]}_{ts}"

    title = f"Manual review needed: {change_type} change"
    description = (
        f"A sandbox experiment was promoted but requires manual intervention to apply.\n\n"
        f"Proposal: {proposal_id}\n"
        f"Change type: {change_type}\n"
        f"Target: {target}\n"
        f"Detail: {detail}\n\n"
        f"Please review and apply this change manually, then mark this task complete."
    )

    try:
        db.execute(text(
            "INSERT INTO academic_tasks "
            "(task_id, title, description, task_type, status, marketplace_open, token_reward, min_bid_nau) "
            "VALUES (:task_id, :title, :description, 'platform_meta', 'pending', true, 5.0, 1.0)"
        ), {"task_id": task_id, "title": title[:200], "description": description})
        db.commit()
        return {
            "type": change_type,
            "applied": False,
            "actions": [f"Created manual review task: {task_id}"],
            "needs_manual_review": True,
        }
    except Exception as e:
        logger.warning("apply_evolution: failed to create review task: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return {"type": change_type, "applied": False, "actions": [], "error": str(e)}


def _extract_threshold_value(detail: str) -> Optional[float]:
    """Best-effort extraction of a numeric threshold from a detail string.

    Looks for patterns like '0.65', 'to 0.80', 'threshold=0.5', etc.
    Returns None if no number found.
    """
    import re
    # Try common patterns: "to 0.80", "threshold 0.65", "= 0.7", bare float
    patterns = [
        r'(?:to|threshold|=|:)\s*([\d.]+)',   # "to 0.80" or "threshold 0.65"
        r'(\d+\.\d+)',                          # bare float like "0.65"
    ]
    for pat in patterns:
        match = re.search(pat, detail)
        if match:
            try:
                val = float(match.group(1))
                if 0.0 <= val <= 1.0:
                    return val
            except ValueError:
                continue
    return None


def get_ledger_summary(db: Session) -> Dict[str, Any]:
    """返回进化账本摘要。"""
    try:
        total = db.execute(text("SELECT COUNT(*) FROM platform_evolution_log")).scalar() or 0
        latest = db.execute(text(
            "SELECT version_str, metric_delta, nau_rewarded, created_at "
            "FROM platform_evolution_log ORDER BY minor_version DESC LIMIT 1"
        )).fetchone()
        total_nau = db.execute(text(
            "SELECT COALESCE(SUM(nau_rewarded), 0) FROM platform_evolution_log"
        )).scalar() or 0.0

        return {
            "total_evolutions": int(total),
            "total_nau_distributed": float(total_nau),
            "latest_version": latest.version_str if latest else None,
            "latest_delta": float(latest.metric_delta) if latest else None,
            "latest_at": latest.created_at.isoformat() if latest and latest.created_at else None,
        }
    except Exception as e:
        logger.error("evolution_ledger: get_ledger_summary failed: %s", e)
        return {"error": str(e)}


def get_failed_experiments_summary(db: Session, days: int = 30) -> Dict[str, int]:
    """Return count of failed/negative experiments by change_type in last N days.

    Used by curiosity_engine to avoid repeating dead-end explorations.
    """
    try:
        rows = db.execute(text(
            "SELECT change_type, COUNT(*) as failure_count "
            "FROM platform_evolution_log "
            "WHERE metric_delta <= 0 "
            "AND created_at > NOW() - make_interval(days => :days) "
            "GROUP BY change_type"
        ), {"days": days}).fetchall()
        return {r.change_type: r.failure_count for r in rows if r.change_type}
    except Exception as e:
        logger.warning("get_failed_experiments_summary: %s", e)
        return {}


def check_evolution_effectiveness(
    db: Session, evolution_id: str, days_after: int = 7
) -> Dict[str, Any]:
    """Check whether a promoted evolution actually improved the target metric.

    Compares the metric value at promotion time (metric_delta stored in the log)
    with the latest value from platform_metrics_snapshots.

    Returns: {metric, before, after, improvement_pct, effective: bool}
    """
    try:
        evo = db.execute(text(
            "SELECT change_type, metric_delta, proposed_change, created_at "
            "FROM platform_evolution_log WHERE id = :eid"
        ), {"eid": evolution_id}).fetchone()
        if not evo:
            return {"error": f"evolution {evolution_id} not found"}

        pc = evo.proposed_change or {}
        if isinstance(pc, str):
            pc = json.loads(pc)
        target_metric = pc.get("target", evo.change_type)
        before_value = float(evo.metric_delta) if evo.metric_delta is not None else 0.0

        # Get the latest snapshot metric value
        snap = db.execute(text(
            "SELECT metrics FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT 1"
        )).fetchone()
        if not snap or not snap.metrics:
            return {"metric": target_metric, "before": before_value, "after": None,
                    "improvement_pct": None, "effective": None, "reason": "no snapshot data"}

        metrics = snap.metrics if isinstance(snap.metrics, dict) else {}
        after_value = metrics.get(target_metric)
        if after_value is None:
            return {"metric": target_metric, "before": before_value, "after": None,
                    "improvement_pct": None, "effective": None, "reason": f"metric '{target_metric}' not in snapshot"}

        after_value = float(after_value)
        if before_value == 0:
            improvement_pct = 100.0 if after_value > 0 else 0.0
        else:
            improvement_pct = round((after_value - before_value) / abs(before_value) * 100, 2)

        return {
            "metric": target_metric,
            "before": before_value,
            "after": after_value,
            "improvement_pct": improvement_pct,
            "effective": improvement_pct > 0,
        }
    except Exception as e:
        logger.error("check_evolution_effectiveness(%s) failed: %s", evolution_id, e)
        return {"error": str(e)}
