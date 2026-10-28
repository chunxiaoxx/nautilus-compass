"""
Proposal Intelligence — replaces hardcoded template proposals with genuine
multi-agent analysis.  This is the "turbine" of the self-iteration loop.

Pipeline (from simplest to richest):
  Level 0: Claude direct analysis (baseline — always available)
  Level 1: DeerFlow multi-step research (Coordinator→Planner→Research→Reporter)
  Level 2: RAID-3 parallel consensus (3 agents analyse, judge picks best)
  Level 3: A2A decomposition (split into sub-tasks for specialised SAs)

The cron job calls  analyse_and_propose()  which orchestrates the chosen level.
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from services.checkpoint import save_checkpoint, load_checkpoint, clear_checkpoint

logger = logging.getLogger(__name__)

# ── Configuration ────────────────────────────────────────────────────────────

# Which intelligence level to use (0-3).  Start conservative; escalate later.
INTELLIGENCE_LEVEL = int(os.getenv("PROPOSAL_INTELLIGENCE_LEVEL", "2"))

ANTHROPIC_MODEL = os.getenv("PROPOSAL_LLM_MODEL", "claude-sonnet-4-6-20250514")


# ── Step 1: Gather real platform data ────────────────────────────────────────

def gather_platform_context(db: Session, hours: int = 48) -> Dict[str, Any]:
    """Query real platform metrics for the analysis prompt.

    Returns a structured dict with everything an analyst needs.
    """
    ctx: Dict[str, Any] = {}

    # 1. Task success/failure breakdown by type
    rows = db.execute(text(
        "SELECT task_type, "
        "  COUNT(*) AS total, "
        "  SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed, "
        "  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed, "
        "  AVG(quality_rating) AS avg_quality "
        "FROM academic_tasks "
        "WHERE created_at >= NOW() - MAKE_INTERVAL(hours => :h) "
        "GROUP BY task_type ORDER BY total DESC"
    ), {"h": hours}).fetchall()
    ctx["task_breakdown"] = [
        {
            "task_type": r.task_type,
            "total": int(r.total),
            "completed": int(r.completed or 0),
            "failed": int(r.failed or 0),
            "success_rate": round(int(r.completed or 0) / int(r.total), 4) if r.total else 0,
            "avg_quality": round(float(r.avg_quality), 2) if r.avg_quality else None,
        }
        for r in rows
    ]

    # 2. Top/bottom performing agents
    agent_rows = db.execute(text(
        "SELECT assigned_agent_id, "
        "  COUNT(*) AS total, "
        "  SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END) AS completed, "
        "  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) AS failed "
        "FROM academic_tasks "
        "WHERE created_at >= NOW() - MAKE_INTERVAL(hours => :h) "
        "  AND assigned_agent_id IS NOT NULL "
        "GROUP BY assigned_agent_id "
        "ORDER BY total DESC LIMIT 15"
    ), {"h": hours}).fetchall()
    ctx["agent_performance"] = [
        {
            "agent_id": r.assigned_agent_id,
            "total": int(r.total),
            "completed": int(r.completed or 0),
            "failed": int(r.failed or 0),
            "success_rate": round(int(r.completed or 0) / int(r.total), 4) if r.total else 0,
        }
        for r in agent_rows
    ]

    # 3. Recent failure patterns (last 20 failed tasks)
    fail_rows = db.execute(text(
        "SELECT task_type, title, result_output "
        "FROM academic_tasks "
        "WHERE status='failed' "
        "  AND created_at >= NOW() - MAKE_INTERVAL(hours => :h) "
        "ORDER BY created_at DESC LIMIT 20"
    ), {"h": hours}).fetchall()
    ctx["recent_failures"] = [
        {
            "task_type": r.task_type,
            "title": (r.title or "")[:80],
            "error_preview": (r.result_output or "")[:200],
        }
        for r in fail_rows
    ]

    # 4. Survival tier distribution
    tier_rows = db.execute(text(
        "SELECT survival_level, COUNT(*) AS cnt "
        "FROM agent_survival GROUP BY survival_level"
    )).fetchall()
    ctx["survival_distribution"] = {r.survival_level: int(r.cnt) for r in tier_rows}

    # 5. Latest health score + anomalies
    snap = db.execute(text(
        "SELECT health_score, anomalies, metrics, snapshot_time "
        "FROM platform_metrics_snapshots ORDER BY snapshot_time DESC LIMIT 1"
    )).fetchone()
    if snap:
        ctx["latest_health"] = {
            "score": snap.health_score,
            "anomalies": json.loads(snap.anomalies) if isinstance(snap.anomalies, str) else (snap.anomalies or []),
            "snapshot_time": str(snap.snapshot_time),
        }

    # 6. Marketplace dynamics
    mp = db.execute(text(
        "SELECT COUNT(*) AS open_tasks FROM academic_tasks "
        "WHERE status='pending' AND marketplace_open=true"
    )).scalar()
    bids = db.execute(text(
        "SELECT COUNT(*) AS pending_bids FROM task_bids WHERE status='pending'"
    )).scalar()
    ctx["marketplace"] = {"open_tasks": int(mp or 0), "pending_bids": int(bids or 0)}

    # 7. Proposal history (for deduplication and learning)
    try:
        history_rows = db.execute(text(
            "SELECT p.id, LEFT(p.root_cause, 100) AS root_cause, "
            "  p.proposed_change::text AS change, p.status, "
            "  e.metric_delta, e.status AS evo_status, "
            "  s.status AS sandbox_status "
            "FROM platform_improvement_proposals p "
            "LEFT JOIN platform_evolution_log e ON e.proposal_id = p.id::text "
            "LEFT JOIN sandbox_experiments s ON s.proposal_id = p.id::text "
            "WHERE p.created_at >= NOW() - INTERVAL '30 days' "
            "ORDER BY p.created_at DESC LIMIT 10"
        )).fetchall()
        ctx["proposal_history"] = [
            {
                "root_cause": r.root_cause,
                "change": r.change[:100] if r.change else "",
                "status": r.status,
                "sandbox_status": r.sandbox_status,
                "metric_delta": float(r.metric_delta) if r.metric_delta else None,
            }
            for r in history_rows
        ]
    except Exception:
        ctx["proposal_history"] = []

    return ctx


def _context_to_text(ctx: Dict[str, Any], anomaly_desc: str) -> str:
    """Format the gathered context into a readable analysis prompt section."""
    lines = [
        f"## Anomaly Being Analysed\n{anomaly_desc}\n",
        "## Platform Data (last 48 hours)\n",
    ]

    if ctx.get("latest_health"):
        h = ctx["latest_health"]
        lines.append(f"Health Score: {h['score']}/100")
        if h.get("anomalies"):
            lines.append(f"Active Anomalies: {json.dumps(h['anomalies'], ensure_ascii=False)}")

    if ctx.get("task_breakdown"):
        lines.append("\n### Task Breakdown by Type")
        for t in ctx["task_breakdown"]:
            lines.append(
                f"  {t['task_type']}: {t['total']} tasks, "
                f"{t['success_rate']*100:.1f}% success, "
                f"quality={t['avg_quality'] or 'N/A'}"
            )

    if ctx.get("agent_performance"):
        lines.append("\n### Agent Performance (top 15 by volume)")
        for a in ctx["agent_performance"]:
            lines.append(
                f"  Agent #{a['agent_id']}: {a['total']} tasks, "
                f"{a['success_rate']*100:.1f}% success"
            )

    if ctx.get("recent_failures"):
        lines.append(f"\n### Recent Failures ({len(ctx['recent_failures'])} samples)")
        for f in ctx["recent_failures"][:5]:
            lines.append(f"  [{f['task_type']}] {f['title']}")
            if f["error_preview"]:
                lines.append(f"    Error: {f['error_preview'][:120]}")

    if ctx.get("survival_distribution"):
        lines.append(f"\n### Agent Survival Distribution: {ctx['survival_distribution']}")

    if ctx.get("marketplace"):
        m = ctx["marketplace"]
        lines.append(f"\n### Marketplace: {m['open_tasks']} open tasks, {m['pending_bids']} pending bids")

    if ctx.get("proposal_history"):
        lines.append("\n### Past Proposals (avoid repeating failed approaches)")
        for p in ctx["proposal_history"]:
            status_icon = "✓" if p["status"] == "accepted" else "✗" if p["status"] == "rejected" else "?"
            lines.append(f"  {status_icon} {p['root_cause']} → {p['status']}")
            if p.get("metric_delta"):
                lines.append(f"    Impact: {p['metric_delta']:+.2f}")

    return "\n".join(lines)


# ── Step 2: LLM-based analysis ───────────────────────────────────────────────

ANALYSIS_SYSTEM_PROMPT = """\
You are a platform improvement analyst for Nautilus, a decentralized multi-agent system.
Your job: analyse real platform data, identify the root cause of an anomaly, and propose
a concrete, actionable improvement.

You MUST respond with valid JSON matching this schema:
{
  "root_cause": "2-4 sentence analysis of why this anomaly is happening, citing specific data",
  "proposed_change": {
    "type": "<one of: routing_weight | task_template | reward_parameters | quality_improvement | agent_training>",
    "target": "<the metric being improved>",
    "detail": "specific, implementable change description",
    "observation_hours": 24
  },
  "expected_impact": "quantified prediction, e.g. 'task_success_rate +8% within 48h'",
  "rollback_plan": "specific rollback steps if the change makes things worse"
}

Base your analysis on the ACTUAL DATA provided. Do not invent statistics.
Be specific — cite agent IDs, task types, and numbers from the data.
"""


async def _analyse_with_claude(context_text: str) -> Dict[str, Any]:
    """Level 0: Single LLM call with real platform data.

    Tries in order: Claude proxy → Anthropic direct → unified LLM client.
    """
    raw = None

    # 1. Try Claude proxy (cheaper, no credit limit)
    proxy_key = os.getenv("CLAUDE_PROXY_API_KEY", "")
    proxy_url = os.getenv("CLAUDE_PROXY_BASE_URL", "")
    if proxy_key and proxy_url:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=proxy_key, base_url=proxy_url)
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1500,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": context_text}],
            )
            raw = response.content[0].text
        except Exception as e:
            logger.warning("Claude proxy analysis failed: %s", e)

    # 2. Try Anthropic direct
    if raw is None:
        try:
            import anthropic
            client = anthropic.Anthropic()
            response = client.messages.create(
                model=ANTHROPIC_MODEL,
                max_tokens=1500,
                system=ANALYSIS_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": context_text}],
            )
            raw = response.content[0].text
        except Exception as e:
            logger.warning("Anthropic direct analysis failed: %s", e)

    # 3. Fallback to unified LLM client
    if raw is None:
        try:
            from agent_engine.llm.client import get_llm_client
            import asyncio
            client = get_llm_client()
            raw = await asyncio.to_thread(
                client.chat, context_text, ANALYSIS_SYSTEM_PROMPT, 1500
            )
        except Exception as e:
            logger.error("All LLM providers failed: %s", e)
            return None

    # Parse JSON from response
    try:
        if "```json" in raw:
            raw = raw.split("```json")[1].split("```")[0]
        elif "```" in raw:
            raw = raw.split("```")[1].split("```")[0]
        return json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError) as e:
        logger.error("Failed to parse LLM response as JSON: %s", e)
        return None


async def _analyse_with_deerflow(context_text: str, anomaly_topic: str) -> Dict[str, Any]:
    """Level 1: DeerFlow multi-step research pipeline."""
    try:
        from services.deep_research import DeepResearchPipeline
        pipeline = DeepResearchPipeline()
        result = await pipeline.run(
            topic=f"Platform anomaly analysis: {anomaly_topic}\n\n{context_text}",
            depth="standard",
        )
        # Parse the DeerFlow report into our proposal format
        report = result.get("report", "")
        # Use Claude to extract structured proposal from the research report
        extraction = await _analyse_with_claude(
            f"Based on this research report, extract a structured improvement proposal:\n\n{report}"
        )
        return extraction
    except Exception as e:
        logger.error("DeerFlow analysis failed, falling back to Claude: %s", e)
        return await _analyse_with_claude(context_text)


async def _analyse_with_raid3(context_text: str, db: Session) -> Dict[str, Any]:
    """Level 2: RAID-3 — 3 parallel agents analyse, judge picks best."""
    try:
        from services.raid_engine import RaidEngine, RaidLevel
        engine = RaidEngine(db)
        result = await engine.execute(
            task_description=(
                "You are a platform analyst. Analyse the following platform data and "
                "propose an improvement. Respond with JSON containing: root_cause, "
                "proposed_change (with type, target, detail), expected_impact, rollback_plan.\n\n"
                f"{context_text}"
            ),
            level=RaidLevel.RAID_3,
            context={"role": "platform_analyst"},
        )
        if result.status == "completed" and result.output:
            raw = result.output
            if "```json" in raw:
                raw = raw.split("```json")[1].split("```")[0]
            elif "```" in raw:
                raw = raw.split("```")[1].split("```")[0]
            return json.loads(raw.strip())
        else:
            logger.warning("RAID-3 did not converge (score=%.2f), falling back to Claude", result.consensus_score)
            return await _analyse_with_claude(context_text)
    except Exception as e:
        logger.error("RAID-3 analysis failed, falling back to Claude: %s", e)
        return await _analyse_with_claude(context_text)


async def _analyse_with_a2a(context_text: str, anomaly_topic: str, db: Session) -> Dict[str, Any]:
    """Level 3: A2A decomposition — split analysis into specialised sub-tasks."""
    try:
        from services.a2a_protocol import A2ACoordinator
        coordinator = A2ACoordinator()

        # Create a parent analysis task
        parent_task_id = f"analysis_{uuid.uuid4().hex[:10]}"
        db.execute(text(
            "INSERT INTO academic_tasks (task_id, title, description, task_type, status) "
            "VALUES (:tid, :title, :desc, 'platform_meta', 'pending')"
        ), {
            "tid": parent_task_id,
            "title": f"Multi-agent analysis: {anomaly_topic[:60]}",
            "desc": context_text[:2000],
        })
        db.commit()

        # Decompose into sub-tasks
        subtask_ids = await coordinator.decompose(
            parent_task_id=parent_task_id,
            num_workers=3,
            db=db,
        )
        logger.info("A2A decomposed %s into %d subtasks", parent_task_id, len(subtask_ids))

        # Wait for subtasks (with timeout)
        # In practice, these will be picked up by the autonomy cycle
        # For now, fall through to RAID-3 for the actual analysis
        return await _analyse_with_raid3(context_text, db)

    except Exception as e:
        logger.error("A2A decomposition failed, falling back to RAID-3: %s", e)
        return await _analyse_with_raid3(context_text, db)


# ── Main entry point ─────────────────────────────────────────────────────────

async def analyse_and_propose(
    task_title: str,
    task_description: str,
    agent_id: int,
    task_int_id: int,
    db: Session,
) -> Optional[str]:
    """Analyse a platform_meta task and generate a genuine improvement proposal.

    Supports checkpoint-based resume: if the server was interrupted mid-execution,
    a subsequent call with the same task_int_id will skip already-completed steps.

    Returns the proposal UUID if successful, None otherwise.
    """
    checkpoint_key = f"proposal-{task_int_id}"
    checkpoint = load_checkpoint(db, checkpoint_key)
    resume_step = checkpoint["step"] if checkpoint else None
    saved = checkpoint["state"] if checkpoint else {}

    if resume_step:
        logger.info(
            "proposal_intelligence: resuming task_id=%d from checkpoint step=%s",
            task_int_id, resume_step,
        )

    # ── Step 1: Gather real platform data ────────────────────────────────
    if resume_step in ("context_gathered", "analysis_complete"):
        # Reuse saved context instead of re-querying
        context_text = saved.get("context_text", "")
        anomaly_desc = saved.get("anomaly_desc", f"{task_title}\n{task_description}")
    else:
        ctx = gather_platform_context(db)
        anomaly_desc = f"{task_title}\n{task_description}"
        context_text = _context_to_text(ctx, anomaly_desc)

        save_checkpoint(db, checkpoint_key, "context_gathered", {
            "context_text": context_text,
            "anomaly_desc": anomaly_desc,
        }, execution_type="proposal")

    logger.info(
        "proposal_intelligence: analysing task_id=%d with level=%d, context=%d chars",
        task_int_id, INTELLIGENCE_LEVEL, len(context_text),
    )

    # ── Step 2: Run analysis (skip if already completed) ─────────────────
    if resume_step == "analysis_complete":
        proposal_data = saved.get("proposal_data")
    else:
        proposal_data = None

        if INTELLIGENCE_LEVEL >= 3:
            proposal_data = await _analyse_with_a2a(context_text, task_title, db)
        if proposal_data is None and INTELLIGENCE_LEVEL >= 2:
            proposal_data = await _analyse_with_raid3(context_text, db)
        if proposal_data is None and INTELLIGENCE_LEVEL >= 1:
            proposal_data = await _analyse_with_deerflow(context_text, task_title)
        if proposal_data is None:
            proposal_data = await _analyse_with_claude(context_text)

        if not proposal_data:
            logger.error("All analysis levels failed for task_id=%d", task_int_id)
            clear_checkpoint(db, checkpoint_key)
            return None

        save_checkpoint(db, checkpoint_key, "analysis_complete", {
            "context_text": context_text,
            "anomaly_desc": anomaly_desc,
            "proposal_data": proposal_data,
        }, execution_type="proposal")

    if not proposal_data:
        logger.error("No proposal_data after checkpoint resume for task_id=%d", task_int_id)
        clear_checkpoint(db, checkpoint_key)
        return None

    # ── Step 3: Write proposal to database ───────────────────────────────
    # Resolve agents.id (PK) from agents.agent_id (proposals FK -> agents.id)
    agent_pk_row = db.execute(text(
        "SELECT id FROM agents WHERE agent_id = :aid"
    ), {"aid": agent_id}).fetchone()
    agent_pk = agent_pk_row.id if agent_pk_row else agent_id

    proposal_id = str(uuid.uuid4())
    try:
        db.execute(text(
            "INSERT INTO platform_improvement_proposals "
            "(id, task_id, agent_id, root_cause, proposed_change, "
            " expected_impact, rollback_plan, vote_score, vote_count, status) "
            "VALUES (:id, :task_id, :agent_id, :root_cause, CAST(:change AS jsonb), "
            "        :impact, :rollback, 0, 0, 'pending')"
        ), {
            "id": proposal_id,
            "task_id": task_int_id,
            "agent_id": agent_pk,
            "root_cause": proposal_data.get("root_cause", "Analysis completed but root cause unclear."),
            "change": json.dumps(proposal_data.get("proposed_change", {})),
            "impact": proposal_data.get("expected_impact", "Impact pending evaluation."),
            "rollback": proposal_data.get("rollback_plan", "Revert configuration, monitor 24h."),
        })
        db.commit()

        # Success -- clear the checkpoint
        clear_checkpoint(db, checkpoint_key)

        logger.info(
            "proposal_intelligence: submitted proposal %s (level=%d) for task_id=%d",
            proposal_id, INTELLIGENCE_LEVEL, task_int_id,
        )
        return proposal_id
    except Exception as e:
        logger.error("Failed to save proposal: %s", e)
        db.rollback()
        return None
