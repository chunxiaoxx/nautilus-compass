"""
A/B Sandbox Service
当提案达到共识后，自动创建沙箱实验，对比 sandbox vs control 的平台指标。
"""
from __future__ import annotations
import logging
import uuid
import json
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional
from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# 沙箱实验状态
EXPERIMENT_STATUSES = ("running", "completed", "promoted", "rolled_back")

# 实验配置默认值
DEFAULT_OBSERVATION_HOURS = 24   # 观测窗口
DEFAULT_SANDBOX_TRAFFIC_PCT = 10  # 10% 流量走 sandbox
IMPROVEMENT_THRESHOLD = 0.05      # 指标改善 5% 才 promote


def create_experiment(db: Session, proposal_id: str, proposed_change: dict) -> Optional[str]:
    """
    根据通过共识的提案创建 A/B 实验。
    返回 experiment_id，失败返回 None。
    """
    try:
        exp_id = f"exp_{uuid.uuid4().hex[:12]}"
        observation_hours = proposed_change.get("observation_hours", DEFAULT_OBSERVATION_HOURS)
        ends_at = datetime.now(timezone.utc) + timedelta(hours=observation_hours)

        db.execute(text(
            """INSERT INTO sandbox_experiments
               (id, proposal_id, proposed_change, observation_hours, ends_at,
                sandbox_traffic_pct, status, baseline_metrics, sandbox_metrics)
               VALUES (:id, :proposal_id, CAST(:proposed_change AS jsonb), :observation_hours,
                       :ends_at, :traffic_pct, 'running', '{}', '{}')"""
        ), {
            "id": exp_id,
            "proposal_id": proposal_id,
            "proposed_change": json.dumps(proposed_change),
            "observation_hours": observation_hours,
            "ends_at": ends_at,
            "traffic_pct": proposed_change.get("sandbox_traffic_pct", DEFAULT_SANDBOX_TRAFFIC_PCT),
        })
        db.commit()
        logger.info("sandbox: created experiment %s for proposal %s", exp_id, proposal_id)
        return exp_id
    except Exception as e:
        logger.error("sandbox: create_experiment failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def evaluate_experiment(db: Session, exp_id: str) -> Dict[str, Any]:
    """
    评估实验结果：对比 sandbox vs baseline 的核心指标。
    从 academic_tasks 中按 experiment_tag 分组统计。
    返回 {improved: bool, delta: float, recommendation: str}
    """
    try:
        row = db.execute(text(
            "SELECT id, proposal_id, proposed_change, sandbox_traffic_pct, "
            "       ends_at, status, baseline_metrics, sandbox_metrics "
            "FROM sandbox_experiments WHERE id=:id"
        ), {"id": exp_id}).fetchone()

        if not row:
            return {"error": "experiment not found"}

        # 从任务表中统计实验期间打了 sandbox tag 的任务
        sandbox_stats = db.execute(text(
            """SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done,
                AVG(quality_rating) AS avg_q
               FROM academic_tasks
               WHERE experiment_id=:exp_id AND experiment_group='sandbox'
                 AND created_at >= (SELECT created_at FROM sandbox_experiments WHERE id=:exp_id)"""
        ), {"exp_id": exp_id}).fetchone()

        control_stats = db.execute(text(
            """SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done,
                AVG(quality_rating) AS avg_q
               FROM academic_tasks
               WHERE experiment_id=:exp_id AND experiment_group='control'
                 AND created_at >= (SELECT created_at FROM sandbox_experiments WHERE id=:exp_id)"""
        ), {"exp_id": exp_id}).fetchone()

        sandbox_rate = (float(sandbox_stats.done or 0) / float(sandbox_stats.total)) if sandbox_stats.total else 0
        control_rate = (float(control_stats.done or 0) / float(control_stats.total)) if control_stats.total else 0

        # Fix 2: 阈值从 10 降到 3（低流量也能评估）
        MIN_EVAL_TASKS = 3
        sandbox_total = sandbox_stats.total or 0
        control_total = control_stats.total or 0

        if sandbox_total < MIN_EVAL_TASKS and control_total < MIN_EVAL_TASKS:
            delta = 0.0
            improved = False
            recommendation = "insufficient_data"
        elif sandbox_total >= 1 and control_total >= 1:
            delta = sandbox_rate - control_rate
            improved = delta >= IMPROVEMENT_THRESHOLD
            recommendation = "promote" if improved else "rollback"
        else:
            delta = 0.0
            improved = False
            recommendation = "insufficient_data"

        result = {
            "exp_id": exp_id,
            "sandbox_success_rate": round(sandbox_rate, 4),
            "control_success_rate": round(control_rate, 4),
            "delta": round(delta, 4),
            "improved": improved,
            "recommendation": recommendation,
            "sandbox_tasks": int(sandbox_stats.total or 0),
            "control_tasks": int(control_stats.total or 0),
        }

        # 更新 sandbox_metrics
        db.execute(text(
            "UPDATE sandbox_experiments SET sandbox_metrics=:metrics WHERE id=:id"
        ), {"metrics": json.dumps(result), "id": exp_id})
        db.commit()

        return result
    except Exception as e:
        logger.error("sandbox: evaluate_experiment failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return {"error": str(e)}


def finalize_experiment(db: Session, exp_id: str, decision: str) -> bool:
    """
    decision: 'promoted' | 'rolled_back'
    更新实验状态，并在 proposal 中标注结果。
    """
    try:
        db.execute(text(
            "UPDATE sandbox_experiments SET status=:status, finalized_at=NOW() WHERE id=:id"
        ), {"status": decision, "id": exp_id})

        # 同步更新关联提案
        db.execute(text(
            """UPDATE platform_improvement_proposals
               SET status=:pstatus
               WHERE id = (SELECT proposal_id FROM sandbox_experiments WHERE id=:exp_id)"""
        ), {"pstatus": "deployed" if decision == "promoted" else "rejected", "exp_id": exp_id})

        db.commit()
        logger.info("sandbox: experiment %s finalized as %s", exp_id, decision)
        return True
    except Exception as e:
        logger.error("sandbox: finalize_experiment failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return False


def assign_task_to_experiment(db: Session, task_id: str) -> Optional[str]:
    """
    检查是否有正在运行的实验，若有则按流量比例随机分配任务到 sandbox 或 control 组。
    返回分配到的 experiment_id，无实验则返回 None。
    """
    import random
    try:
        row = db.execute(text(
            "SELECT id, sandbox_traffic_pct FROM sandbox_experiments "
            "WHERE status='running' AND ends_at > NOW() "
            "ORDER BY created_at DESC LIMIT 1"
        )).fetchone()
        if not row:
            return None
        exp_id = row.id
        group = "sandbox" if random.random() < (row.sandbox_traffic_pct / 100.0) else "control"
        db.execute(text(
            "UPDATE academic_tasks SET experiment_id=:exp_id, experiment_group=:group WHERE task_id=:task_id"
        ), {"exp_id": exp_id, "group": group, "task_id": task_id})
        db.commit()
        logger.debug("sandbox: assigned task %s to experiment %s group=%s", task_id, exp_id, group)
        return exp_id
    except Exception as e:
        logger.error("sandbox: assign_task_to_experiment failed: %s", e)
        try:
            db.rollback()
        except Exception:
            pass
        return None


def get_pending_evaluations(db: Session):
    """返回已到期但尚未完成的实验列表。"""
    try:
        rows = db.execute(text(
            "SELECT id, proposal_id, proposed_change, ends_at "
            "FROM sandbox_experiments "
            "WHERE status='running' AND ends_at <= NOW() "
            "ORDER BY ends_at ASC"
        )).fetchall()
        return rows
    except Exception as e:
        logger.error("sandbox: get_pending_evaluations failed: %s", e)
        return []
