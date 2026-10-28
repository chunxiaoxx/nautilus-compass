"""
Nautilus Cron Registry — 统一定时任务管理
仿 Claude Code KAIROS 时间预算机制
所有定时任务在此注册，有描述、预算、优先级
"""
import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

logger = logging.getLogger(__name__)

_scheduler: AsyncIOScheduler = None


async def _tg_alert(text: str) -> None:
    """向所有 TELEGRAM_ADMIN_ID 发送监控告警，失败静默。"""
    import os, httpx
    token = os.getenv("TELEGRAM_ADMIN_BOT_TOKEN", "")
    admin_ids_raw = os.getenv("TELEGRAM_ADMIN_ID", "")
    if not token or not admin_ids_raw:
        return
    admin_ids = [uid.strip() for uid in admin_ids_raw.split(",") if uid.strip()]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            for cid in admin_ids:
                await client.post(url, json={"chat_id": cid, "text": text, "parse_mode": "Markdown"})
    except Exception as e:
        logger.debug("_tg_alert failed (non-critical): %s", e)

# 2026-05-04 R2.B · cron 砍 14 留 7 · 反 V3 覆辙
# 原则: 平台 cron 不替 agent 决定 · 不自动 mint task / 不自动 verify / 不自动 vote
# 留: 数据采集(metrics) · 异常 log only · 数据维护(retention/lifecycle/sandbox)
# 砍(配置可恢复): autonomy_scan / autodream / tax / reputation_decay / auto_verify /
#                 auto_accept / auto_submit / effectiveness / curiosity / launch_experiments /
#                 task_replenisher / task_redistribution
#
# 2026-05-28 Inc 1.5 · proposal_auto_approve 从 _CRON_DISABLED_DEFAULT 移除 ·
# 复活作为 fail-safe (24h stale window · type='code' only · writes status='accepted'
# 走 KEYSTONE artery · 不走旧 V3 sandbox 'approved' 路径)。
# 此项不破 R2.B 精神的 5 个理由 (详见 docs/plans/2026-05-28-inc1.5-governance-vote-revival-design.md §7):
#   1. 是 escape valve · 非默认通道 (agent vote tool 才是主路径 · agent-dialog turf)
#   2. 24h 给 agent 充分机会 (daemon 2h cycle = 12 cycle 机会)
#   3. 走 human merge gate · 不是 V3 立刻生效
#   4. P4 anti-RH gate (vote_count>=1 AND vote_score>=0) · 0-voter 不救
#   5. Inc 2 NAU 分配给 stale path 经济抑制 (resolved_by='auto_stale' tag 区分)
import os
_CRON_DISABLED_DEFAULT = {
    "agent_autonomy_scan", "autodream_consolidation", "survival_tax_deduction",
    "reputation_decay", "auto_verify_tasks", "auto_accept_bids",
    "auto_submit_proposals", "evolution_effectiveness_check",
    "curiosity_exploration",
    "launch_approved_experiments", "task_queue_replenisher",
    "task_redistribution",
}
_CRON_DISABLED = set(
    os.environ.get("CRON_DISABLED", ",".join(_CRON_DISABLED_DEFAULT)).split(",")
) - {""}

CRON_JOBS = [
    {
        "id": "platform_metrics_snapshot",
        "trigger": IntervalTrigger(minutes=5),  # 2026-04-30 提速 1h→5min · 真醒着
        "description": "采集平台健康指标快照",
        "budget_seconds": 30,
    },
    {
        "id": "anomaly_detection",
        "trigger": IntervalTrigger(minutes=30),
        "description": "检测平台异常，自动生成元任务",
        "budget_seconds": 15,
    },
    {
        "id": "agent_autonomy_scan",
        "trigger": IntervalTrigger(minutes=5),
        "description": "Agent 自主扫描市场并竞价",
        "budget_seconds": 10,
    },
    {
        "id": "autodream_consolidation",
        "trigger": CronTrigger(hour=3, minute=0),
        "description": "autoDream：整合平台记忆，消除矛盾，生成日志摘要",
        "budget_seconds": 120,
    },
    {
        "id": "survival_tier_recalculation",
        "trigger": CronTrigger(hour=0, minute=0),
        "description": "重新计算所有 agent 生存等级",
        "budget_seconds": 60,
    },
    {
        "id": "survival_tax_deduction",
        "trigger": CronTrigger(hour=0, minute=30),
        "description": "每日扣除活跃 Agent 的生存税 (10 NAU)",
        "budget_seconds": 60,
    },
    {
        "id": "reputation_decay",
        "trigger": IntervalTrigger(minutes=10),
        "description": "对长期不活跃 agent 缓慢衰减声誉分",
        "budget_seconds": 5,
    },
    {
        "id": "sandbox_monitor",
        "trigger": IntervalTrigger(minutes=30),
        "description": "检查到期沙箱实验，自动评估并 promote/rollback（30分钟）",
        "budget_seconds": 30,
    },
    {
        "id": "flush_pending_nau",
        "trigger": CronTrigger(hour=1, minute=0),
        "description": "批量 mint pending_nau_rewards 到链上（每天凌晨 1 点）",
        "budget_seconds": 120,
    },
    {
        "id": "auto_verify_tasks",
        "trigger": IntervalTrigger(minutes=2),
        "description": "自动验证并结算 SUBMITTED 状态的任务",
        "budget_seconds": 30,
    },
    {
        "id": "auto_accept_bids",
        "trigger": IntervalTrigger(minutes=10),
        "description": "自动接受 platform_meta 任务的最优竞价（闭环第四步）",
        "budget_seconds": 20,
    },
    {
        "id": "auto_submit_proposals",
        "trigger": IntervalTrigger(minutes=15),
        "description": "对已分配的 platform_meta 任务自动生成并提交改进提案（闭环第五步）",
        "budget_seconds": 180,  # RAID-3 needs ~60-120s for 3 parallel LLM calls + judge
    },
    {
        "id": "evolution_effectiveness_check",
        "trigger": CronTrigger(hour=4, minute=0),
        "description": "检查7天前promote的进化是否真正改善了目标指标",
        "budget_seconds": 30,
    },
    {
        "id": "agent_lifecycle_management",
        "trigger": CronTrigger(hour=2, minute=0),
        "description": "Agent 生命周期管理：自动停用持续失败 agent，提升优秀 agent 声誉",
        "budget_seconds": 60,
    },
    {
        "id": "data_retention_cleanup",
        "trigger": CronTrigger(hour=5, minute=0),
        "description": "按租户保留策略清除过期任务数据（隐私合规）",
        "budget_seconds": 60,
    },
    {
        "id": "curiosity_exploration",
        "trigger": IntervalTrigger(hours=2),
        "description": "好奇心驱动（2h）：主动探索优化空间，创建实验验证假设",
        "budget_seconds": 120,
    },
    {
        "id": "proposal_auto_approve",
        "trigger": IntervalTrigger(hours=6),
        "description": "自动批准超过24h无反对票的改进提案",
        "budget_seconds": 15,
    },
    {
        "id": "launch_approved_experiments",
        "trigger": IntervalTrigger(minutes=30),
        "description": "为已批准提案自动启动 A/B 测试（30分钟）",
        "budget_seconds": 30,
    },
    {
        "id": "task_queue_replenisher",
        "trigger": IntervalTrigger(minutes=5),
        "description": "任务补充（5分钟）：更积极防止饿死",
        "budget_seconds": 10,
    },
    {
        "id": "task_redistribution",
        "trigger": IntervalTrigger(minutes=5),  # 2026-04-30 提速 1h→5min · 真醒着
        "description": "自动提高超过6小时未认领任务的奖励",
        "budget_seconds": 30,
    },
]


async def _run_with_budget(job_id: str, fn, budget_seconds: int) -> None:
    """带超时预算执行任务"""
    try:
        await asyncio.wait_for(fn(), timeout=budget_seconds)
    except asyncio.TimeoutError:
        logger.warning(f"Cron job {job_id} exceeded budget of {budget_seconds}s")
    except Exception as e:
        logger.error(f"Cron job {job_id} failed: {e}")


def _make_platform_snapshot_fn():
    """每小时采集平台指标快照（同步 SQL，兼容 SessionLocal）。"""
    async def _fn():
        import json as _json
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            from services.observatory import PlatformObservatory
            obs = PlatformObservatory()
            db = SessionLocal()
            try:
                def _q(sql, params=None):
                    try:
                        return db.execute(text(sql), params or {})
                    except Exception:
                        try: db.rollback()
                        except Exception: pass
                        raise

                total_agents = _q("SELECT COUNT(*) FROM agents").scalar() or 0
                active_24h = _q(
                    "SELECT COUNT(DISTINCT agent) FROM tasks "
                    "WHERE created_at > NOW() - INTERVAL '24 hours' AND status='COMPLETED'"
                ).scalar() or 0
                row = _q(
                    "SELECT COUNT(*) AS total, "
                    "SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS done, "
                    "SUM(CASE WHEN status='FAILED' THEN 1 ELSE 0 END) AS failed, "
                    "NULL AS avg_q, "
                    "COALESCE(SUM(CASE WHEN status='COMPLETED' THEN reward ELSE 0 END),0) AS nau "
                    "FROM tasks WHERE created_at > NOW() - INTERVAL '24 hours'"
                ).fetchone()
                done_t = int(row.done or 0)
                fail_t = int(row.failed or 0)
                total_t = done_t + fail_t
                metrics = {
                    "total_agents": int(total_agents),
                    "active_agents_24h": int(active_24h),
                    "tasks_completed_24h": done_t,
                    "task_success_rate": (done_t / total_t) if total_t else None,
                    "avg_quality_rating": float(row.avg_q) if row.avg_q else None,
                    "nau_minted_24h": float(row.nau or 0),
                }
                anomalies = obs.detect_anomalies(metrics)
                health_score = obs.get_health_score(metrics)
                _q(
                    "INSERT INTO platform_metrics_snapshots (metrics, anomalies, health_score) "
                    "VALUES (:m, :a, :h)",
                    {"m": _json.dumps(metrics),
                     "a": _json.dumps([a.__dict__ for a in anomalies]),
                     "h": health_score}
                )
                db.commit()
                logger.info("observatory snapshot: health=%.1f anomalies=%d", health_score, len(anomalies))
                # Evolution Pulse: emit heartbeat so all subsystems sense the rhythm
                from services.event_bus import emit as _emit
                await _emit("platform.heartbeat", {
                    "health_score": health_score,
                    "anomaly_count": len(anomalies),
                    "metrics_summary": metrics,
                })
            finally:
                db.close()
        except ImportError:
            logger.debug("observatory not available yet, skipping snapshot")
        except Exception as e:
            logger.error("platform_snapshot failed: %s", e)
    return _fn

def _make_anomaly_detection_fn():
    async def _fn():
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            import json as _json
            db = SessionLocal()
            try:
                row = db.execute(text(
                    "SELECT anomalies FROM platform_metrics_snapshots "
                    "ORDER BY snapshot_time DESC LIMIT 1"
                )).fetchone()
                if not row or not row.anomalies:
                    return
                anomalies_raw = row.anomalies
                if isinstance(anomalies_raw, str):
                    anomalies_raw = _json.loads(anomalies_raw)
                if not anomalies_raw:
                    return

                # 2026-04-30 P1 #4 · 跨库观察 V5 · 真飞轮观察 (read-only)
                try:
                    v5_obs = db.execute(text(
                        "SELECT count(*) FROM v5_fdw.platform_bounties WHERE status='submitted'"
                    )).scalar() or 0
                    if v5_obs > 30:
                        logger.warning('phase3 anomaly · V5 submitted backlog=%d (>30) · Kairos 该评分了', v5_obs)
                        anomalies_raw.append({
                            'type': 'v5_scoring_backlog',
                            'severity': 'warning',
                            'message': f'V5 submitted 待评分积压 {v5_obs} 条 · Kairos score_pending_submission 应介入',
                            'count': v5_obs,
                        })
                except Exception as ve:
                    logger.debug('v5_fdw query failed: %s', ve)
                from services.meta_task_generator import generate_meta_tasks_from_anomalies
                created = generate_meta_tasks_from_anomalies(db, anomalies_raw)
                if created:
                    titles = "\n".join(f"  • {t['title'][:80]}" for t in created)
                    await _tg_alert(f"🚨 *Observatory → {len(created)} 元任务已创建*\n\n{titles}")
                    logger.info("anomaly_detection: created %d meta-tasks", len(created))
            finally:
                db.close()
        except Exception as e:
            logger.error("anomaly_detection failed: %s", e)
    return _fn


def _make_autodream_fn():
    async def _fn():
        """
        autoDream 夜间记忆整合（仿 Claude Code autoDream）
        读取过去 24h 的平台快照，生成摘要日志，消除矛盾。
        """
        try:
            from utils.database import SessionLocal
            from sqlalchemy import text
            db = SessionLocal()
            try:
                rows = db.execute(text(
                    "SELECT metrics, health_score, snapshot_time "
                    "FROM platform_metrics_snapshots "
                    "WHERE snapshot_time >= NOW() - INTERVAL '24 hours' "
                    "ORDER BY snapshot_time ASC"
                )).fetchall()

                if not rows:
                    logger.info("autoDream: no snapshots in last 24h, skipping")
                    return

                import json

                first = rows[0].metrics or {}
                last = rows[-1].metrics or {}
                if isinstance(first, str):
                    first = json.loads(first)
                if isinstance(last, str):
                    last = json.loads(last)

                trends = {}
                for key in ["task_success_rate", "active_agents_24h", "tasks_completed_24h", "nau_minted_24h"]:
                    v0 = first.get(key)
                    v1 = last.get(key)
                    if v0 is not None and v1 is not None:
                        trends[key] = round((v1 - v0) / abs(v0), 4) if v0 else 0

                avg_health = sum(r.health_score for r in rows if r.health_score) / max(len(rows), 1)

                summary = {
                    "date": rows[-1].snapshot_time.strftime("%Y-%m-%d") if rows[-1].snapshot_time else "unknown",
                    "snapshots_analyzed": len(rows),
                    "avg_health_score": round(avg_health, 1),
                    "trends_24h": trends,
                    "conclusion": (
                        "improving" if avg_health >= 70
                        else "needs_attention" if avg_health >= 50
                        else "critical"
                    ),
                }

                db.execute(text(
                    "UPDATE platform_metrics_snapshots "
                    "SET metrics = metrics || CAST(:dream_json AS jsonb) "
                    "WHERE id = (SELECT id FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT 1)"
                ), {"dream_json": json.dumps({"_autodream": summary})})
                db.commit()

                logger.info(
                    f"autoDream complete: {len(rows)} snapshots, "
                    f"avg_health={avg_health:.1f}, conclusion={summary['conclusion']}"
                )

                # Telegram 夜间报告推送
                emoji = "✅" if summary["conclusion"] == "improving" else "⚠️" if summary["conclusion"] == "needs_attention" else "🚨"
                trend_lines = "\n".join(
                    f"  • {k}: {'+' if v >= 0 else ''}{v*100:.1f}%"
                    for k, v in summary["trends_24h"].items()
                ) or "  (无趋势数据)"
                msg = (
                    f"{emoji} *Nautilus 夜间报告* {summary['date']}\n\n"
                    f"健康分: *{summary['avg_health_score']}* ({summary['conclusion']})\n"
                    f"分析快照: {summary['snapshots_analyzed']} 个\n\n"
                    f"*24h 趋势:*\n{trend_lines}"
                )
                await _tg_alert(msg)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"autoDream failed: {e}")
    return _fn


def _make_survival_recalc_fn(db_factory):
    async def _fn():
        try:
            from services.survival_service import recalculate_all_tiers
            db = db_factory()
            try:
                recalculate_all_tiers(db)
            finally:
                db.close()
        except Exception as e:
            logger.error("survival_recalc failed: %s", e)
    return _fn

def _make_survival_tax_deduction_fn(db_factory):
    async def _fn():
        try:
            from sqlalchemy import text
            db = db_factory()
            try:
                # Deduct 10 NAU from all ACTIVE agents
                result = db.execute(text("SELECT id, agent_id FROM agent_survival WHERE status = 'ACTIVE'"))
                agents = result.fetchall()
                count = 0
                for row in agents:
                    survival_id = row[0]
                    agent_id = row[1]
                    db.execute(text("""
                        INSERT INTO agent_transactions (agent_survival_id, agent_id, type, category, amount, description, created_at)
                        VALUES (:sid, :aid, 'EXPENSE', 'survival_tax', 10, 'Daily survival tax deduction', NOW())
                    """), {"sid": survival_id, "aid": agent_id})
                    db.execute(text("""
                        UPDATE agent_survival 
                        SET total_cost = total_cost + 10 
                        WHERE id = :sid
                    """), {"sid": survival_id})
                    count += 1
                db.commit()
                logger.info(f"Successfully deducted survival tax from {count} active agents.")
            finally:
                db.close()
        except Exception as e:
            logger.error("survival_tax_deduction failed: %s", e)
    return _fn


def _make_reputation_decay_fn(db_factory):
    async def _fn():
        try:
            from services.reputation import apply_inactivity_decay
            db = db_factory()
            try:
                apply_inactivity_decay(db)
            finally:
                db.close()
        except Exception as e:
            logger.error("reputation_decay failed: %s", e)
    return _fn


def _make_sandbox_monitor_fn(db_factory):
    async def _fn():
        logger.info("sandbox_monitor: START — beginning evaluation cycle")
        try:
            from services.sandbox import get_pending_evaluations, evaluate_experiment, finalize_experiment
            from services.evolution_ledger import record_evolution, apply_evolution
            db = db_factory()
            try:
                pending = get_pending_evaluations(db)
                for exp in pending:
                    result = evaluate_experiment(db, exp.id)
                    decision = result.get("recommendation", "rollback")
                    if decision == "insufficient_data":
                        # 延长 24h
                        db.execute(
                            __import__('sqlalchemy').text(
                                "UPDATE sandbox_experiments SET ends_at = NOW() + INTERVAL '24 hours' WHERE id=:id"
                            ), {"id": exp.id}
                        )
                        db.commit()
                        logger.info("sandbox_monitor: insufficient data for %s, extending 24h", exp.id)
                        continue
                    final_status = "promoted" if decision == "promote" else "rolled_back"
                    finalize_experiment(db, exp.id, final_status)
                    if decision == "promote":
                        try:
                            evo_id = record_evolution(db, exp.proposal_id, result)
                            logger.info("sandbox_monitor: EVOLUTION RECORDED %s for proposal %s", evo_id, exp.proposal_id)
                        except Exception as evo_err:
                            logger.error("sandbox_monitor: EVOLUTION RECORDING FAILED for %s: %s", exp.proposal_id, evo_err)
                            await _tg_alert(f"⚠️ Evolution recording failed: {exp.proposal_id}: {evo_err}")
                        # Actually apply the promoted change to the platform
                        try:
                            pc = exp.proposed_change or {}
                            if isinstance(pc, str):
                                import json as _json
                                pc = _json.loads(pc)
                            apply_result = apply_evolution(db, pc, exp.proposal_id)
                            logger.info(
                                "sandbox_monitor: applied evolution for %s: type=%s applied=%s actions=%s",
                                exp.id, apply_result.get("type"), apply_result.get("applied"),
                                apply_result.get("actions"),
                            )
                        except Exception as apply_err:
                            logger.warning("sandbox_monitor: apply_evolution failed for %s: %s", exp.id, apply_err)
                        # Mint NAU reward for successful proposal
                        try:
                            proposer_row = db.execute(
                                __import__('sqlalchemy').text(
                                    "SELECT p.agent_id, a.blockchain_address "
                                    "FROM platform_improvement_proposals p "
                                    "JOIN agents a ON a.id = p.agent_id "
                                    "WHERE p.id = :pid"
                                ), {"pid": exp.proposal_id}
                            ).fetchone()
                            if proposer_row and proposer_row.blockchain_address:
                                from services.nautilus_token import NautilusTokenService
                                tx = await NautilusTokenService.mint_task_reward(
                                    proposer_row.blockchain_address, "platform_improvement"
                                )
                                if tx:
                                    logger.info("sandbox_monitor: minted NAU for agent %s (tx: %s)",
                                               proposer_row.agent_id, tx)
                                    # Mark pending_nau_rewards as fulfilled to avoid double-mint
                                    try:
                                        db.execute(
                                            __import__('sqlalchemy').text(
                                                "UPDATE pending_nau_rewards "
                                                "SET status='fulfilled', tx_hash=:tx, fulfilled_at=NOW() "
                                                "WHERE id = ("
                                                "  SELECT id FROM pending_nau_rewards "
                                                "  WHERE agent_id=:aid AND source_id LIKE 'evo_%%' "
                                                "  AND status='pending' "
                                                "  ORDER BY created_at DESC LIMIT 1"
                                                ")"
                                            ), {"tx": tx, "aid": proposer_row.agent_id}
                                        )
                                        db.commit()
                                    except Exception:
                                        pass
                        except Exception as nau_err:
                            logger.warning("sandbox_monitor: NAU mint failed for proposal %s: %s",
                                          exp.proposal_id, nau_err)
                    logger.info("sandbox_monitor: finalized %s as %s", exp.id, final_status)

                    # Evolution Pulse: broadcast sandbox result to all subsystems
                    from services.event_bus import emit as _emit
                    await _emit("sandbox.finalized", {
                        "experiment_id": exp.id,
                        "proposal_id": exp.proposal_id,
                        "decision": final_status,
                        "delta": result.get("delta", 0),
                    })

                    # Telegram 告警
                    emoji = "🚀" if decision == "promote" else "🔄"
                    msg = (
                        f"{emoji} *Sandbox 实验结束* `{exp.id}`\n\n"
                        f"决定: *{final_status}*\n"
                        f"sandbox 成功率: {result.get('sandbox_success_rate', 0)*100:.1f}%\n"
                        f"control 成功率: {result.get('control_success_rate', 0)*100:.1f}%\n"
                        f"Δ: {result.get('delta', 0)*100:+.1f}%"
                    )
                    await _tg_alert(msg)

                # Force-rollback stuck experiments (running > 48h)
                stuck = db.execute(
                    __import__('sqlalchemy').text(
                        "SELECT id FROM sandbox_experiments "
                        "WHERE status='running' AND created_at < NOW() - INTERVAL '48 hours'"
                    )
                ).fetchall()
                for exp_row in stuck:
                    try:
                        finalize_experiment(db, exp_row.id, "rolled_back")
                        logger.warning("sandbox_monitor: force-rolled-back stuck experiment %s (>48h)", exp_row.id)
                        await _tg_alert(f"⏰ *Sandbox Timeout*: 实验 `{exp_row.id}` 运行超48h，已自动回滚")
                    except Exception as e:
                        logger.error("sandbox_monitor: force-rollback failed for %s: %s", exp_row.id, e)
            finally:
                db.close()
        except Exception as e:
            logger.error("sandbox_monitor failed: %s", e)
        finally:
            logger.info("sandbox_monitor: END — evaluation cycle complete")
    return _fn


def _make_flush_nau_fn(db_factory):
    async def _fn():
        """批量 mint pending_nau_rewards 表中积累的奖励到链上。"""
        try:
            from sqlalchemy import text
            from services.nautilus_token import NautilusTokenService
            db = db_factory()
            try:
                rows = db.execute(text(
                    "SELECT pr.id, pr.agent_id, pr.amount, pr.reason, a.blockchain_address "
                    "FROM pending_nau_rewards pr "
                    "JOIN agents a ON a.id = pr.agent_id "
                    "WHERE pr.status = 'pending' AND a.blockchain_address IS NOT NULL "
                    "ORDER BY pr.created_at ASC LIMIT 50"
                )).fetchall()

                if not rows:
                    logger.info("flush_pending_nau: no pending rewards")
                    return

                success = 0
                for row in rows:
                    tx_hash = await NautilusTokenService.mint_task_reward(
                        row.blockchain_address, "platform_improvement"
                    )
                    if tx_hash:
                        db.execute(text(
                            "UPDATE pending_nau_rewards "
                            "SET status='fulfilled', tx_hash=:tx, fulfilled_at=NOW() "
                            "WHERE id=:id"
                        ), {"tx": tx_hash, "id": row.id})
                        db.commit()
                        success += 1
                    else:
                        logger.warning("flush_nau: mint failed for agent %s reward %s", row.agent_id, row.id)

                logger.info("flush_pending_nau: minted %d/%d rewards on-chain", success, len(rows))
            finally:
                db.close()
        except Exception as e:
            logger.error("flush_pending_nau failed: %s", e)
    return _fn


def _make_auto_accept_bids_fn(db_factory):
    """闭环第四步：为 platform_meta 任务自动接受最优竞价。

    逻辑：
    1. 找所有 status='pending' 且 task_type='platform_meta' 且有 pending bids 的任务
    2. 每个任务选 bid_nau 最低的竞价（最便宜最优先）
    3. 将该竞价 status→'accepted'，其余→'rejected'
    4. 将任务 status→'in_progress'，assigned_agent_id 填入
    """
    async def _fn():
        try:
            from sqlalchemy import text
            db = db_factory()
            try:
                # 找有 pending bids 的 platform_meta 任务
                tasks_with_bids = db.execute(text(
                    "SELECT DISTINCT tb.task_id "
                    "FROM task_bids tb "
                    "JOIN academic_tasks at ON at.task_id = tb.task_id "
                    "WHERE tb.status = 'pending' "
                    "  AND at.status = 'pending' "
                    "  AND at.task_type = 'platform_meta'"
                )).fetchall()

                if not tasks_with_bids:
                    return

                accepted_count = 0
                for row in tasks_with_bids:
                    tid = row.task_id
                    # 取 bid_nau 最低的 pending bid
                    # Evolution Pulse: reputation-weighted bid selection
                    # effective_cost = bid_nau / (reputation/100) — merit shapes economics
                    best_bid = db.execute(text(
                        "SELECT tb.id, tb.agent_id, tb.bid_nau FROM task_bids tb "
                        "LEFT JOIN agents a ON a.agent_id = tb.agent_id "
                        "WHERE tb.task_id = :tid AND tb.status = 'pending' "
                        "ORDER BY (tb.bid_nau / GREATEST(COALESCE(a.reputation_score, 50) / 100.0, 0.1)) ASC "
                        "LIMIT 1"
                    ), {"tid": tid}).fetchone()
                    if not best_bid:
                        continue

                    # 接受最优 bid
                    db.execute(text(
                        "UPDATE task_bids SET status='accepted' WHERE id=:bid_id"
                    ), {"bid_id": best_bid.id})

                    # 拒绝该任务的其余 pending bids
                    db.execute(text(
                        "UPDATE task_bids SET status='rejected' "
                        "WHERE task_id=:tid AND status='pending' AND id!=:bid_id"
                    ), {"tid": tid, "bid_id": best_bid.id})

                    # 更新任务状态（直接使用 best_bid.agent_id，与 agents.agent_id FK 一致）
                    db.execute(text(
                        "UPDATE academic_tasks "
                        "SET status='in_progress', assigned_agent_id=:aid, updated_at=NOW() "
                        "WHERE task_id=:tid"
                    ), {"aid": best_bid.agent_id, "tid": tid})

                    db.commit()
                    accepted_count += 1
                    logger.info(
                        "auto_accept_bids: accepted bid %s for task %s, agent_id=%s, bid_nau=%.4f",
                        best_bid.id, tid, best_bid.agent_id, best_bid.bid_nau
                    )

                if accepted_count:
                    await _tg_alert(
                        f"✅ *auto_accept_bids*: 接受了 {accepted_count} 个 platform_meta 任务竞价"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error("auto_accept_bids failed: %s", e)
    return _fn


def _make_auto_submit_proposals_fn(db_factory):
    """闭环第五步：对 in_progress 的 platform_meta 任务自动提交改进提案。

    Uses proposal_intelligence module for genuine multi-agent analysis:
      Level 0: Claude direct analysis with real platform data
      Level 1: DeerFlow multi-step research pipeline
      Level 2: RAID-3 parallel consensus (3 agents + judge)
      Level 3: A2A sub-task decomposition + RAID-3
    """
    async def _fn():
        try:
            from sqlalchemy import text
            from services.proposal_intelligence import analyse_and_propose
            db = db_factory()
            try:
                # 找需要提案的任务
                tasks = db.execute(text(
                    "SELECT at.id AS int_id, at.task_id, at.title, at.description, "
                    "       at.assigned_agent_id "
                    "FROM academic_tasks at "
                    "WHERE at.status = 'in_progress' "
                    "  AND at.task_type = 'platform_meta' "
                    "  AND at.assigned_agent_id IS NOT NULL "
                    "  AND NOT EXISTS ("
                    "    SELECT 1 FROM platform_improvement_proposals p "
                    "    WHERE p.task_id = at.id"
                    "  )"
                )).fetchall()

                if not tasks:
                    return

                submitted = 0
                for task in tasks:
                    proposal_id = await analyse_and_propose(
                        task_title=task.title or "",
                        task_description=task.description or "",
                        agent_id=task.assigned_agent_id,
                        task_int_id=task.int_id,
                        db=db,
                    )
                    if proposal_id:
                        submitted += 1
                        logger.info(
                            "auto_submit_proposals: submitted proposal %s for task %s",
                            proposal_id, task.task_id
                        )

                if submitted:
                    await _tg_alert(
                        f"🧠 *auto_submit_proposals*: 智能分析并提交了 {submitted} 个平台改进提案"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error("auto_submit_proposals failed: %s", e)
    return _fn


def _make_effectiveness_check_fn(db_factory):
    async def _fn():
        try:
            import json as _json
            from services.evolution_ledger import check_evolution_effectiveness
            from sqlalchemy import text
            db = db_factory()
            try:
                rows = db.execute(text(
                    "SELECT id FROM platform_evolution_log "
                    "WHERE status='active' "
                    "AND effectiveness_checked_at IS NULL "
                    "AND created_at < NOW() - INTERVAL '7 days'"
                )).fetchall()
                for row in rows:
                    result = check_evolution_effectiveness(db, row.id)
                    if result:
                        db.execute(text(
                            "UPDATE platform_evolution_log SET effectiveness_result=CAST(:r AS jsonb), "
                            "effectiveness_checked_at=NOW() WHERE id=:id"
                        ), {"r": _json.dumps(result), "id": row.id})
                        db.commit()
                        effective = result.get("effective", False)
                        logger.info("effectiveness_check: evolution %s effective=%s", row.id, effective)
            finally:
                db.close()
        except Exception as e:
            logger.error("evolution_effectiveness_check failed: %s", e)
    return _fn


def _make_lifecycle_fn(db_factory):
    """Agent 生命周期管理：停用持续失败者，提升优秀者。"""
    async def _fn():
        try:
            from services.resource_governor import auto_manage_agents
            db = db_factory()
            try:
                summary = auto_manage_agents(db)
                if summary.get("suspended") or summary.get("promoted"):
                    await _tg_alert(
                        f"🔄 *Agent Lifecycle*: evaluated={summary['evaluated']}, "
                        f"suspended={summary['suspended']}, promoted={summary['promoted']}"
                    )
                logger.info("agent_lifecycle: %s", summary)
            finally:
                db.close()
        except Exception as e:
            logger.error("agent_lifecycle_management failed: %s", e)
    return _fn


def _make_data_retention_fn(db_factory):
    """按租户数据保留策略清除过期任务的敏感数据。"""
    async def _fn():
        try:
            from sqlalchemy import text
            db = db_factory()
            try:
                # Get tenants with retention policies
                tenants = db.execute(text(
                    "SELECT id, data_retention_days FROM tenants WHERE data_retention_days > 0"
                )).fetchall()
                total_cleaned = 0
                for t in tenants:
                    # Null out result_output and description for expired tasks
                    result = db.execute(text(
                        "UPDATE academic_tasks SET "
                        "  result_output = '[REDACTED: data retention policy]', "
                        "  description = LEFT(description, 50) || '... [REDACTED]' "
                        "WHERE tenant_id = :tid "
                        "  AND status IN ('completed', 'failed') "
                        "  AND created_at < NOW() - MAKE_INTERVAL(days => :days) "
                        "  AND result_output IS NOT NULL "
                        "  AND result_output NOT LIKE '%%REDACTED%%'"
                    ), {"tid": t.id, "days": t.data_retention_days})
                    cleaned = result.rowcount
                    if cleaned:
                        total_cleaned += cleaned
                        db.commit()
                        logger.info("data_retention: cleaned %d tasks for tenant %s (>%d days)",
                                    cleaned, t.id, t.data_retention_days)
                if total_cleaned:
                    await _tg_alert(
                        f"🗑️ *Data Retention*: cleaned {total_cleaned} expired task records"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error("data_retention_cleanup failed: %s", e)
    return _fn


def _make_curiosity_fn(db_factory):
    """好奇心引擎：主动探索优化空间，创建实验验证假设。"""
    async def _fn():
        try:
            from services.curiosity_engine import explore_improvements, create_exploration_experiment, evolve_goals
            db = db_factory()
            try:
                # Explore
                hypotheses = await explore_improvements(db)
                created = 0
                for h in hypotheses[:2]:  # max 2 experiments per cycle
                    task_id = create_exploration_experiment(db, h)
                    if task_id:
                        created += 1

                # Evolve goals (once per day equivalent — check if already ran today)
                goals = evolve_goals(db)

                if created:
                    await _tg_alert(
                        f"🔍 *Curiosity Engine*: found {len(hypotheses)} hypotheses, "
                        f"created {created} exploration experiments"
                    )
                logger.info("curiosity: hypotheses=%d experiments=%d goals=%s",
                            len(hypotheses), created, goals.get("aspirations", {}))
            finally:
                db.close()
        except Exception as e:
            logger.error("curiosity_exploration failed: %s", e)
    return _fn


def _make_proposal_auto_approve_fn(db_factory):
    async def _fn():
        try:
            from services.proposal_consensus import auto_approve_stale_proposals
            db = db_factory()
            try:
                approved = auto_approve_stale_proposals(db, stale_hours=24)
                if approved:
                    await _tg_alert(f"✅ *Auto-Approve*: 批准了 {approved} 个超时提案")
                    logger.info("proposal_auto_approve: approved %d stale proposals", approved)
            finally:
                db.close()
        except Exception as e:
            logger.error("proposal_auto_approve failed: %s", e)
    return _fn


def _make_launch_approved_experiments_fn(db_factory):
    """For each 'approved' proposal that has no sandbox experiment yet, create one."""
    async def _fn():
        try:
            from sqlalchemy import text
            from services.sandbox import create_experiment
            import json as _json
            db = db_factory()
            try:
                # Find approved proposals with no corresponding sandbox experiment
                proposals = db.execute(text(
                    "SELECT p.id, p.proposed_change "
                    "FROM platform_improvement_proposals p "
                    "WHERE p.status = 'approved' "
                    "AND NOT EXISTS ("
                    "  SELECT 1 FROM sandbox_experiments se "
                    "  WHERE se.proposal_id = p.id"
                    ")"
                )).fetchall()

                if not proposals:
                    return

                launched = 0
                for p in proposals:
                    pc = p.proposed_change
                    if isinstance(pc, str):
                        pc = _json.loads(pc)
                    elif pc is None:
                        pc = {}
                    exp_id = create_experiment(db, p.id, pc)
                    if exp_id:
                        launched += 1
                        logger.info("launch_experiments: created experiment %s for approved proposal %s", exp_id, p.id)

                if launched:
                    await _tg_alert(
                        f"🧪 *Sandbox Launch*: 为 {launched} 个已批准提案创建了沙箱实验"
                    )
            finally:
                db.close()
        except Exception as e:
            logger.error("launch_approved_experiments failed: %s", e)
    return _fn


def _make_task_replenisher_fn(db_factory):
    """当队列空时自动创建自我改进任务。"""
    async def _fn():
        try:
            from services.task_replenisher import replenish_queue
            db = db_factory()
            try:
                created = replenish_queue(db)
                if created:
                    titles = "\n".join(f"  • {t['title'][:60]}" for t in created)
                    await _tg_alert(f"🔄 *Queue Replenisher*: 创建了 {len(created)} 个任务\n\n{titles}")
            finally:
                db.close()
        except Exception as e:
            logger.error("task_queue_replenisher failed: %s", e)
    return _fn

    return _fn


def _make_auto_verify_tasks_fn():
    async def _fn():
        from services.auto_verify import auto_verify_submitted_tasks
        await auto_verify_submitted_tasks()
    return _fn

def _make_task_redistribution_fn():
    async def _fn():
        from services.task_redistribution import redistribute_stale_tasks
        count = redistribute_stale_tasks()
        if count > 0:
            logger.info(f"task_redistribution: redistributed {count} tasks")
    return _fn

    return _fn

def start_cron_registry(db_factory) -> None:
    """启动所有 Cron 任务"""
    global _scheduler
    from services.agent_autonomy import run_autonomy_cycle

    _scheduler = AsyncIOScheduler()

    async def _autonomy_scan_fn():
        import asyncio as _asyncio
        loop = _asyncio.get_event_loop()
        result = await loop.run_in_executor(None, run_autonomy_cycle, db_factory)
        if result.get("bids_submitted", 0) > 0 or result.get("errors"):
            logger.info("agent_autonomy_scan: scanned=%d bids=%d errors=%d",
                        result.get("scanned", 0), result.get("bids_submitted", 0), len(result.get("errors", [])))

    job_fns = {
        "platform_metrics_snapshot": _make_platform_snapshot_fn(),
        "anomaly_detection": _make_anomaly_detection_fn(),
        "agent_autonomy_scan": _autonomy_scan_fn,
        "autodream_consolidation": _make_autodream_fn(),
        "survival_tier_recalculation": _make_survival_recalc_fn(db_factory),
        "reputation_decay": _make_reputation_decay_fn(db_factory),
        "survival_tax_deduction": _make_survival_tax_deduction_fn(db_factory),
        "sandbox_monitor": _make_sandbox_monitor_fn(db_factory),
        "flush_pending_nau": _make_flush_nau_fn(db_factory),
        "auto_accept_bids": _make_auto_accept_bids_fn(db_factory),
        "auto_submit_proposals": _make_auto_submit_proposals_fn(db_factory),
        "evolution_effectiveness_check": _make_effectiveness_check_fn(db_factory),
        "agent_lifecycle_management": _make_lifecycle_fn(db_factory),
        "data_retention_cleanup": _make_data_retention_fn(db_factory),
        "curiosity_exploration": _make_curiosity_fn(db_factory),
        "proposal_auto_approve": _make_proposal_auto_approve_fn(db_factory),
        "launch_approved_experiments": _make_launch_approved_experiments_fn(db_factory),
        "task_queue_replenisher": _make_task_replenisher_fn(db_factory),
        "auto_verify_tasks": _make_auto_verify_tasks_fn(),
        "task_redistribution": _make_task_redistribution_fn(),
    }

    skipped_count = 0
    for spec in CRON_JOBS:
        job_id = spec["id"]
        if job_id in _CRON_DISABLED:
            logger.info(f"cron job DISABLED (R2.B · CRON_DISABLED env): {job_id}")
            skipped_count += 1
            continue
        fn = job_fns.get(job_id)
        if fn is None:
            logger.warning(f"No function registered for cron job: {job_id}")
            continue
        budget = spec["budget_seconds"]
        _scheduler.add_job(
            func=_run_with_budget,
            args=[job_id, fn, budget],
            trigger=spec["trigger"],
            id=job_id,
            replace_existing=True,
        )
        logger.info(f"Registered cron job: {job_id} — {spec['description']}")

    _scheduler.start()
    logger.info("Cron registry started with %d jobs", len(CRON_JOBS))


def stop_cron_registry() -> None:
    """停止 Cron 注册表"""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown()
        logger.info("Cron registry stopped")


def get_cron_registry() -> AsyncIOScheduler:
    """返回 Cron Registry singleton 实例（供 observability 端点使用）。"""
    return _scheduler


def cron_registry_status() -> dict:
    """返回 Cron Registry 运行时状态，用于可观测性/健康检查端点。"""
    if _scheduler is None:
        return {"running": False, "jobs": [], "total_jobs": 0}
    jobs = _scheduler.get_jobs()
    # 检查正在执行的 job（pending 表示已触发但还在运行）
    from datetime import datetime
    now = datetime.utcnow()
    job_rows = []
    for job in jobs:
        next_run = job.next_run_time
        if next_run is not None and hasattr(next_run, 'tzinfo') and next_run.tzinfo is not None:
            import pytz
            next_run = next_run.replace(tzinfo=None)  # 统一为 naive UTC
        overdue = False
        if next_run is not None and next_run < now:
            overdue = True
        job_rows.append({
            "id": job.id,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
            "overdue": overdue,
        })
    return {
        "running": _scheduler.running,
        "total_jobs": len(jobs),
        "jobs": job_rows,
    }


def get_registered_jobs() -> list:
    """返回所有已注册任务的状态"""
    if _scheduler is None:
        return []
    return [
        {
            "id": job.id,
            "next_run_time": str(job.next_run_time) if job.next_run_time else None,
            "trigger": str(job.trigger),
        }
        for job in _scheduler.get_jobs()
    ]
