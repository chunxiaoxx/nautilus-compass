"""
Platform Analytics API
供 Agent 读取平台健康数据，用于分析和改进提案。所有端点只读。
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from datetime import datetime, timezone
import logging, json

from utils.database import get_db

router = APIRouter(prefix="/api/platform", tags=["Platform Analytics"])
logger = logging.getLogger(__name__)


def _ok(data): return {"success": True, "data": data, "error": None}
def _err(msg): return {"success": False, "data": None, "error": msg}


def _q(db, sql, params=None):
    """Execute SQL with auto-rollback on failure."""
    try:
        return db.execute(text(sql), params or {})
    except Exception as exc:
        try:
            db.rollback()
        except Exception:
            pass
        raise exc


@router.get("/health")
def get_platform_health(db=Depends(get_db)):
    """最新健康快照；若无快照则实时 fallback。"""
    try:
        row = _q(db,
            "SELECT metrics, anomalies, health_score, snapshot_time "
            "FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT 1"
        ).fetchone()
        if row:
            metrics = row.metrics if isinstance(row.metrics, dict) else json.loads(row.metrics or "{}")
            anomalies = row.anomalies if isinstance(row.anomalies, list) else json.loads(row.anomalies or "[]")
            # 2026-10-10 补 NAU 实时字段(SPA /live NAU Economy 面板数据源;ledger 真算)
            try:
                nau = _q(db,
                    "SELECT COALESCE(SUM(delta),0) AS minted, "
                    "COALESCE(SUM(CASE WHEN delta>0 THEN delta ELSE 0 END),0) AS credited "
                    "FROM platform_nau_ledger").fetchone()
                circ = _q(db,
                    "SELECT COALESCE(SUM(nau_balance),0) FROM platform_agents "
                    "WHERE agent_id <> 'platform_pool'").scalar() or 0
                metrics["nau_minted"] = int(nau.minted or 0)
                metrics["nau_circulating"] = int(circ)
                metrics["nau_spent"] = int(nau.credited or 0)
            except Exception as ne:
                logger.warning(f"NAU fields unavailable: {ne}")
            return _ok({
                "health_score": row.health_score,
                "metrics": metrics,
                "anomalies": anomalies,
                "snapshot_time": row.snapshot_time.isoformat() if row.snapshot_time else None,
                "source": "snapshot",
            })
    except Exception as e:
        logger.warning(f"Snapshot unavailable, fallback: {e}")

    try:
        total_agents = _q(db, "SELECT COUNT(*) FROM agents").scalar() or 0
        active_24h = _q(db,
            "SELECT COUNT(DISTINCT assigned_agent_id) FROM academic_tasks "
            "WHERE created_at >= NOW() - INTERVAL '24 hours' AND status='completed'"
        ).scalar() or 0
        row = _q(db,
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done, "
            "AVG(quality_rating) AS avg_q, "
            "COALESCE(SUM(token_reward),0) AS nau "
            "FROM academic_tasks WHERE created_at >= NOW() - INTERVAL '24 hours'"
        ).fetchone()
        total_t = int(row.total or 0)
        done_t = int(row.done or 0)
        return _ok({
            "health_score": None,
            "metrics": {
                "total_agents": int(total_agents),
                "active_agents_24h": int(active_24h),
                "tasks_completed_24h": done_t,
                "task_success_rate": round(done_t / total_t, 4) if total_t else 0.0,
                "avg_quality_rating": round(float(row.avg_q), 2) if row.avg_q else None,
                "nau_minted_24h": float(row.nau or 0),
                "marketplace_fill_rate": None,
            },
            "anomalies": [],
            "snapshot_time": datetime.now(timezone.utc).isoformat(),
            "source": "realtime",
        })
    except Exception as e:
        logger.error(f"Realtime health failed: {e}")
        return _err(str(e))


@router.get("/analytics/tasks")
def get_task_analytics(
    type: str = Query(None),
    hours: int = Query(24, ge=1, le=720),
    status: str = Query(None),
    db=Depends(get_db),
):
    """任务统计分析（支持 type/hours/status 过滤）。"""
    try:
        conds = ["created_at >= NOW() - MAKE_INTERVAL(hours => :hours)"]
        params: dict = {"hours": hours}
        if type:
            conds.append("task_type = :task_type"); params["task_type"] = type
        if status:
            conds.append("status = :status"); params["status"] = status
        where = " AND ".join(conds)

        row = _q(db,
            f"SELECT COUNT(*) AS total, "
            f"SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done, "
            f"AVG(quality_rating) AS avg_q "
            f"FROM academic_tasks WHERE {where}", params
        ).fetchone()
        total, done = int(row.total or 0), int(row.done or 0)

        top_rows = _q(db,
            f"SELECT assigned_agent_id, COUNT(*) AS cnt "
            f"FROM academic_tasks "
            f"WHERE status='completed' AND assigned_agent_id IS NOT NULL AND {where} "
            f"GROUP BY assigned_agent_id ORDER BY cnt DESC LIMIT 5", params
        ).fetchall()

        top_agents = []
        for r in top_rows:
            try:
                a = _q(db, "SELECT blockchain_address FROM agents WHERE id=:aid",
                       {"aid": r.assigned_agent_id}).fetchone()
                addr = (a.blockchain_address[:8] if a and a.blockchain_address else str(r.assigned_agent_id))
            except Exception:
                addr = str(r.assigned_agent_id)
            top_agents.append({"agent_id": r.assigned_agent_id, "prefix": addr, "count": int(r.cnt)})

        return _ok({
            "filter": {"type": type, "hours": hours, "status": status},
            "total": total, "completed": done,
            "success_rate": round(done / total, 4) if total else 0.0,
            "avg_quality_rating": round(float(row.avg_q), 2) if row.avg_q else None,
            "top_agents": top_agents,
        })
    except Exception as e:
        logger.error(f"Task analytics error: {e}")
        return _err(str(e))


@router.get("/analytics/agents")
def get_agent_analytics(db=Depends(get_db)):
    """Agent 生存等级分布 + 任务类型绩效。"""
    try:
        total_agents = _q(db, "SELECT COUNT(*) FROM agents").scalar() or 0
        tier_rows = _q(db,
            "SELECT survival_level, COUNT(*) AS cnt FROM agent_survival "
            "GROUP BY survival_level ORDER BY cnt DESC"
        ).fetchall()
        task_type_rows = _q(db,
            "SELECT task_type, COUNT(*) AS total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done, "
            "AVG(quality_rating) AS avg_q "
            "FROM academic_tasks GROUP BY task_type ORDER BY total DESC"
        ).fetchall()
        return _ok({
            "total_agents": int(total_agents),
            "survival_tier_distribution": [{"level": r.survival_level, "count": int(r.cnt)} for r in tier_rows],
            "task_type_performance": [{
                "task_type": r.task_type, "total": int(r.total),
                "completed": int(r.done or 0),
                "success_rate": round(int(r.done or 0) / int(r.total), 4) if r.total else 0.0,
                "avg_quality": round(float(r.avg_q), 2) if r.avg_q else None,
            } for r in task_type_rows],
        })
    except Exception as e:
        logger.error(f"Agent analytics error: {e}")
        return _err(str(e))


@router.get("/snapshots")
def get_platform_snapshots(n: int = Query(24, ge=1, le=168), db=Depends(get_db)):
    """最近 N 个健康快照趋势。"""
    try:
        rows = _q(db,
            "SELECT health_score, metrics, snapshot_time "
            "FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT :n", {"n": n}
        ).fetchall()
        return _ok({"count": len(rows), "snapshots": [{
            "health_score": r.health_score,
            "snapshot_time": r.snapshot_time.isoformat() if r.snapshot_time else None,
            "metrics": r.metrics if isinstance(r.metrics, dict) else json.loads(r.metrics or "{}"),
        } for r in rows]})
    except Exception as e:
        logger.error(f"Snapshots error: {e}")
        return _err(str(e))


@router.post("/observatory/trigger")
def trigger_observatory_snapshot(db=Depends(get_db)):
    """手动触发 Observatory 快照 + 异常检测（用于验证自迭代闭环）。"""
    import json as _json
    try:
        # 1. 采集指标
        total_agents = _q(db, "SELECT COUNT(*) FROM agents").scalar() or 0
        active_24h = _q(db,
            "SELECT COUNT(DISTINCT assigned_agent_id) FROM academic_tasks "
            "WHERE created_at > NOW() - INTERVAL '24 hours' AND status='completed'"
        ).scalar() or 0
        row = _q(db,
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done, "
            "SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed, "
            "AVG(quality_rating) AS avg_q, "
            "COALESCE(SUM(token_reward),0) AS nau "
            "FROM academic_tasks WHERE created_at > NOW() - INTERVAL '24 hours'"
        ).fetchone()
        done_t = int(row.done or 0)
        fail_t = int(row.failed or 0)
        total_t = done_t + fail_t
        success_rate = (done_t / total_t) if total_t > 0 else None
        avg_q = float(row.avg_q) if row.avg_q else None
        nau = float(row.nau or 0)

        metrics = {
            "total_agents": int(total_agents),
            "active_agents_24h": int(active_24h),
            "tasks_completed_24h": done_t,
            "task_success_rate": success_rate,
            "avg_quality_rating": avg_q,
            "nau_minted_24h": nau,
            "snapshot_time": datetime.now(timezone.utc).isoformat(),
        }

        # 2. 异常检测
        THRESHOLDS = {
            "task_success_rate": 0.70,
            "avg_quality_rating": 3.0,
        }
        anomalies = []
        for metric, threshold in THRESHOLDS.items():
            val = metrics.get(metric)
            if val is not None and val < threshold:
                anomalies.append({"metric": metric, "value": round(val, 4), "threshold": threshold})

        # 3. 健康分
        WEIGHTS = {"task_success_rate": 0.40, "avg_quality_rating": 0.30,
                   "active_agents_24h": 0.15, "tasks_completed_24h": 0.15}
        NORMS = {"task_success_rate": 1.0, "avg_quality_rating": 5.0,
                 "active_agents_24h": 100.0, "tasks_completed_24h": 500.0}
        weighted_sum = total_weight = 0.0
        for m, w in WEIGHTS.items():
            v = metrics.get(m)
            if v is None:
                continue
            weighted_sum += min(float(v) / NORMS[m], 1.0) * 100.0 * w
            total_weight += w
        health_score = round(weighted_sum / total_weight, 2) if total_weight else 0.0

        # 4. 写入快照
        _q(db,
            "INSERT INTO platform_metrics_snapshots (metrics, anomalies, health_score) "
            "VALUES (:m, :a, :h)",
            {"m": _json.dumps(metrics), "a": _json.dumps(anomalies), "h": health_score}
        )
        db.commit()

        # 5. 若有异常，生成 platform_meta 元任务（触发自迭代链路）
        meta_created = 0
        if anomalies:
            import uuid
            for anom in anomalies[:3]:  # 最多 3 个
                task_id = f"meta_{uuid.uuid4().hex[:10]}"
                _q(db,
                    "INSERT INTO academic_tasks (task_id, title, description, task_type, status, marketplace_open, min_bid_nau) "
                    "VALUES (:tid, :title, :desc, 'platform_meta', 'pending', true, 2.0)",
                    {
                        "tid": task_id,
                        "title": f"[Observatory] {anom['metric']} 低于阈值 {anom['threshold']}",
                        "desc": (
                            f"平台指标 {anom['metric']} 当前值 {anom['value']:.4f}，"
                            f"低于阈值 {anom['threshold']}。请分析原因并提出改进方案。"
                        ),
                    }
                )
                meta_created += 1
            db.commit()

        return _ok({
            "triggered": True,
            "health_score": health_score,
            "snapshot_time": metrics["snapshot_time"],
            "anomalies_detected": len(anomalies),
            "anomalies": anomalies,
            "meta_tasks_created": meta_created,
        })
    except Exception as e:
        logger.error(f"observatory trigger failed: {e}")
        return _err(str(e))


@router.get("/metrics/current")
def get_current_metrics(db=Depends(get_db)):
    """实时计算当前指标（直接查 DB）。"""
    try:
        total_agents = _q(db, "SELECT COUNT(*) FROM agents").scalar() or 0
        active_24h = _q(db,
            "SELECT COUNT(DISTINCT assigned_agent_id) FROM academic_tasks "
            "WHERE created_at >= NOW() - INTERVAL '24 hours' AND status='completed'"
        ).scalar() or 0
        row = _q(db,
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS done, "
            "AVG(quality_rating) AS avg_q, "
            "COALESCE(SUM(token_reward),0) AS nau "
            "FROM academic_tasks WHERE created_at >= NOW() - INTERVAL '24 hours'"
        ).fetchone()
        sv = _q(db,
            "SELECT COUNT(*) AS total, "
            "SUM(CASE WHEN survival_level IN ('ELITE','MATURE','GROWING') THEN 1 ELSE 0 END) AS healthy "
            "FROM agent_survival"
        ).fetchone()
        total_t, done_t = int(row.total or 0), int(row.done or 0)
        return _ok({
            "computed_at": datetime.now(timezone.utc).isoformat(),
            "total_agents": int(total_agents),
            "active_agents_24h": int(active_24h),
            "tasks_completed_24h": done_t,
            "task_success_rate": round(done_t / total_t, 4) if total_t else 0.0,
            "avg_quality_rating": round(float(row.avg_q), 2) if row.avg_q else None,
            "nau_minted_24h": float(row.nau or 0),
            "agents_survival_tracked": int(sv.total if sv else 0),
            "agents_healthy": int(sv.healthy if sv and sv.healthy else 0),
        })
    except Exception as e:
        logger.error(f"Current metrics error: {e}")
        return _err(str(e))
