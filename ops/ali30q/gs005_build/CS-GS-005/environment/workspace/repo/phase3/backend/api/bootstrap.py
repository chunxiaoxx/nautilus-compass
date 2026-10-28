"""
Bootstrap API - Agent self-improvement endpoints.

Provides REST API for:
- Running AutoResearch prompt optimization loops
- Viewing experiment history and prompt versions
- Strategy optimization based on failure analysis
- Bootstrap status and metrics
"""
import asyncio
import logging
import os
import sys
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from utils.database import get_db
from slowapi import Limiter
from slowapi.util import get_remote_address

logger = logging.getLogger(__name__)
router = APIRouter()

TESTING = os.getenv("TESTING", "false").lower() == "true"
limiter = Limiter(key_func=get_remote_address, enabled=not TESTING)

# Add agent-engine to path
AGENT_ENGINE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "..", "agent-engine"
)
if AGENT_ENGINE_PATH not in sys.path:
    sys.path.insert(0, os.path.abspath(AGENT_ENGINE_PATH))


class BootstrapRunRequest(BaseModel):
    """Request to run AutoResearch loop."""
    eval_type: str = "sentiment"
    rounds: int = 5

    class Config:
        json_schema_extra = {
            "example": {
                "eval_type": "sentiment",
                "rounds": 5,
            }
        }


class StrategyOptimizeRequest(BaseModel):
    """Request to run strategy optimization."""
    failure_logs: List[Dict] = []


@router.get("/status")
@limiter.limit("30/minute")
async def bootstrap_status(request: Request):
    """
    Get bootstrap system status.

    Returns prompt registry stats, strategy stats, and recent experiments.
    """
    try:
        from bootstrap.prompt_registry import PromptRegistry
        from bootstrap.strategy_optimizer import StrategyRegistry

        registry = PromptRegistry()
        strategy_reg = StrategyRegistry()

        # Count prompts
        prompt_names = registry.list_all_names()
        total_versions = sum(len(registry.list_versions(n)) for n in prompt_names)

        # Count strategies
        strategy_names = list(strategy_reg.strategies.keys())
        total_strategies = sum(len(v) for v in strategy_reg.strategies.values())

        # Load recent experiments
        import json
        exp_path = os.path.join(AGENT_ENGINE_PATH, "bootstrap", "experiment_log.json")
        recent_experiments = []
        if os.path.exists(exp_path):
            with open(exp_path) as f:
                all_experiments = json.load(f)
            recent_experiments = all_experiments[-10:]  # Last 10

        return {
            "success": True,
            "data": {
                "prompts": {
                    "names": prompt_names,
                    "total_versions": total_versions,
                },
                "strategies": {
                    "names": strategy_names,
                    "total_versions": total_strategies,
                },
                "recent_experiments": recent_experiments,
                "available_eval_types": ["sentiment", "spam", "intent"],
            }
        }
    except Exception as e:
        logger.error(f"Bootstrap status error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/prompts")
@limiter.limit("30/minute")
async def list_prompts(request: Request, name: Optional[str] = None):
    """
    List prompt versions, optionally filtered by name.
    """
    try:
        from bootstrap.prompt_registry import PromptRegistry
        registry = PromptRegistry()

        if name:
            versions = registry.list_versions(name)
            return {
                "success": True,
                "data": [{
                    "name": v.name,
                    "version": v.version,
                    "active": v.active,
                    "created_by": v.created_by,
                    "created_at": v.created_at,
                    "metrics": v.metrics,
                    "template_preview": v.template[:200] + "..." if len(v.template) > 200 else v.template,
                } for v in versions]
            }

        # All prompts
        result = {}
        for pname in registry.list_all_names():
            versions = registry.list_versions(pname)
            active = registry.get_active(pname)
            result[pname] = {
                "total_versions": len(versions),
                "active_version": active.version if active else None,
                "active_accuracy": active.metrics.get("accuracy") if active else None,
                "latest_created_by": versions[-1].created_by if versions else None,
            }

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"List prompts error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies")
@limiter.limit("30/minute")
async def list_strategies(request: Request):
    """
    List active execution strategies.
    """
    try:
        from bootstrap.strategy_optimizer import StrategyOptimizer
        optimizer = StrategyOptimizer()
        strategies = optimizer.get_active_strategies()
        return {"success": True, "data": strategies}
    except Exception as e:
        logger.error(f"List strategies error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run")
@limiter.limit("5/minute")
async def run_bootstrap(request: Request, body: BootstrapRunRequest, db: Session = Depends(get_db)):
    """
    Run AutoResearch prompt optimization loop.

    This triggers N rounds of prompt evaluation and improvement.
    Each round: evaluate current → propose improvement → evaluate candidate → promote if better.

    **Rate Limit**: 5 requests per minute (expensive operation)
    """
    from api.org import _auth_check  # 2026-10-11 追补②(compass #10854/#10861):付费自改进循环口,限 platform
    denied = _auth_check(db, request, "platform")
    if denied:
        return denied
    if body.rounds < 1 or body.rounds > 20:
        raise HTTPException(status_code=400, detail="rounds must be 1-20")
    if body.eval_type not in ("sentiment", "spam", "intent"):
        raise HTTPException(status_code=400, detail="eval_type must be sentiment, spam, or intent")

    try:
        from bootstrap.autoresearch_loop import AutoResearchLoop

        loop = AutoResearchLoop(eval_type=body.eval_type)

        # Run in thread pool to avoid blocking
        summary = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: loop.run(rounds=body.rounds, verbose=False)
        )

        return {
            "success": True,
            "data": {
                "eval_type": summary["eval_type"],
                "rounds": summary["rounds"],
                "improvements": summary["improvements"],
                "baseline_score": round(summary["baseline_score"], 4),
                "final_score": round(summary["final_score"], 4),
                "total_improvement": round(summary["total_improvement"], 4),
                "baseline_accuracy": round(summary["baseline_accuracy"], 4),
                "final_accuracy": round(summary["final_accuracy"], 4),
                "experiments": summary["experiments"],
            }
        }
    except Exception as e:
        logger.error(f"Bootstrap run error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/optimize-strategy")
@limiter.limit("5/minute")
async def optimize_strategy(request: Request, body: StrategyOptimizeRequest):
    """
    Run strategy optimization based on failure logs.

    Analyzes failure patterns and proposes improved execution strategies.
    """
    try:
        from bootstrap.strategy_optimizer import StrategyOptimizer

        optimizer = StrategyOptimizer()
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: optimizer.optimize(body.failure_logs, verbose=False)
        )

        return {"success": True, "data": result}
    except Exception as e:
        logger.error(f"Strategy optimization error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/experiments")
@limiter.limit("30/minute")
async def list_experiments(
    request: Request,
    limit: int = Query(20, ge=1, le=100),
    eval_type: Optional[str] = None,
):
    """
    List experiment history from AutoResearch runs.
    """
    try:
        import json
        exp_path = os.path.join(AGENT_ENGINE_PATH, "bootstrap", "experiment_log.json")

        if not os.path.exists(exp_path):
            return {"success": True, "data": []}

        with open(exp_path) as f:
            experiments = json.load(f)

        if eval_type:
            experiments = [e for e in experiments if e.get("eval_type") == eval_type]

        return {
            "success": True,
            "data": experiments[-limit:],
            "meta": {"total": len(experiments)},
        }
    except Exception as e:
        logger.error(f"List experiments error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
