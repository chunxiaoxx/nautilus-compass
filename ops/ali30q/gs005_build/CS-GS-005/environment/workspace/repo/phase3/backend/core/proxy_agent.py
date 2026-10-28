"""
Proxy Agent (PA) — Open-source core orchestrator for Nautilus.

Implements the PA role from DMAS (arXiv:2512.02410):
  - Stateful task orchestration
  - Multi-agent coordination (A2A decomposition, RAID consensus)
  - Service Agent discovery and routing
  - Task lifecycle management

This is the minimal, open-source PA. The commercial version (agent_executor.py)
adds customer-facing personas, billing, and chat integration.

Usage:
    pa = ProxyAgent()
    result = await pa.execute_task(task_description, task_type="research_synthesis")
    result = await pa.coordinate_multi_agent(task_description, num_agents=3)
"""
import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

LLM_MODEL = os.getenv("PA_LLM_MODEL", "claude-sonnet-4-6-20250514")


# ─────────────────────────────────────────────────────────────────────────────
# Data types
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """Result from a single agent execution."""
    task_id: str
    status: str  # completed | failed
    output: str
    agent_id: Optional[int] = None
    duration_seconds: float = 0.0
    quality_score: Optional[float] = None


@dataclass
class CoordinationResult:
    """Result from multi-agent coordination."""
    task_id: str
    strategy: str  # "single" | "a2a" | "raid" | "deerflow"
    final_output: str
    sub_results: List[TaskResult] = field(default_factory=list)
    consensus_score: float = 0.0
    duration_seconds: float = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# LLM interface
# ─────────────────────────────────────────────────────────────────────────────

async def _llm_call(system: str, user: str, max_tokens: int = 2048) -> str:
    """Make an LLM call. Uses Anthropic by default, falls back to LLMClient."""
    try:
        import anthropic
        client = anthropic.Anthropic()
        response = await asyncio.to_thread(
            lambda: client.messages.create(
                model=LLM_MODEL,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        )
        return response.content[0].text
    except Exception:
        # Fallback to unified LLM client
        from agent_engine.llm.client import get_llm_client
        client = get_llm_client()
        return await asyncio.to_thread(client.chat, user, system, max_tokens)


# ─────────────────────────────────────────────────────────────────────────────
# Task Classification
# ─────────────────────────────────────────────────────────────────────────────

COMPLEXITY_THRESHOLDS = {
    "simple": 1,    # single agent, direct execution
    "moderate": 2,  # RAID-2 (execute + review + improve)
    "complex": 3,   # RAID-3 (3 parallel + judge) or A2A decomposition
}


async def classify_task(description: str) -> Dict[str, str]:
    """Classify task type and complexity for routing."""
    try:
        from services.task_router import classify
        return classify(description)
    except Exception:
        # Minimal fallback classification
        desc_lower = description.lower()
        if any(k in desc_lower for k in ["research", "survey", "review", "analyse"]):
            return {"type": "research_synthesis", "complexity": "complex"}
        elif any(k in desc_lower for k in ["simulate", "monte carlo", "physics"]):
            return {"type": "physics_simulation", "complexity": "moderate"}
        elif any(k in desc_lower for k in ["code", "implement", "function", "script"]):
            return {"type": "code_generation", "complexity": "moderate"}
        return {"type": "general_computation", "complexity": "simple"}


# ─────────────────────────────────────────────────────────────────────────────
# Proxy Agent
# ─────────────────────────────────────────────────────────────────────────────

class ProxyAgent:
    """
    Stateful Proxy Agent implementing DMAS PA role.

    Responsibilities:
    1. Classify incoming tasks
    2. Route to appropriate execution strategy
    3. Coordinate multi-agent execution when needed
    4. Aggregate results and manage lifecycle
    """

    def __init__(self, db_session=None):
        self._db = db_session
        self._execution_history: List[CoordinationResult] = []

    async def execute_task(
        self,
        description: str,
        task_type: Optional[str] = None,
        strategy: Optional[str] = None,
    ) -> CoordinationResult:
        """Execute a task with automatic strategy selection.

        Strategy selection (if not specified):
          - simple tasks → single agent execution
          - moderate tasks → RAID-2 (execute + review + improve)
          - complex tasks → RAID-3 (3 parallel + judge)
          - research tasks → DeerFlow pipeline
        """
        import time
        start = time.time()
        task_id = f"pa_{uuid.uuid4().hex[:12]}"

        # 1. Classify
        if task_type is None:
            classification = await classify_task(description)
            task_type = classification.get("type", "general_computation")
            complexity = classification.get("complexity", "simple")
        else:
            complexity = "moderate"

        # 2. Select strategy
        if strategy is None:
            if task_type == "research_synthesis":
                strategy = "deerflow"
            elif complexity == "complex":
                strategy = "raid3"
            elif complexity == "moderate":
                strategy = "raid2"
            else:
                strategy = "single"

        logger.info("PA: task=%s type=%s strategy=%s", task_id, task_type, strategy)

        # 3. Execute
        try:
            if strategy == "deerflow":
                result = await self._execute_deerflow(task_id, description)
            elif strategy == "raid3":
                result = await self._execute_raid(task_id, description, level=3)
            elif strategy == "raid2":
                result = await self._execute_raid(task_id, description, level=2)
            elif strategy == "a2a":
                result = await self._execute_a2a(task_id, description)
            else:
                result = await self._execute_single(task_id, description, task_type)
        except Exception as e:
            logger.error("PA execution failed: %s", e)
            result = CoordinationResult(
                task_id=task_id, strategy=strategy,
                final_output=f"Execution failed: {e}",
            )

        result.duration_seconds = round(time.time() - start, 2)
        self._execution_history.append(result)
        return result

    async def coordinate_multi_agent(
        self,
        description: str,
        num_agents: int = 3,
    ) -> CoordinationResult:
        """Explicitly coordinate multiple agents on a task."""
        if num_agents >= 3:
            return await self.execute_task(description, strategy="raid3")
        return await self.execute_task(description, strategy="raid2")

    # ── Execution strategies ─────────────────────────────────────────────────

    async def _execute_single(
        self, task_id: str, description: str, task_type: str
    ) -> CoordinationResult:
        """Single agent execution via LLM."""
        output = await _llm_call(
            system="You are a capable AI agent. Complete the task and return results.",
            user=description,
        )
        return CoordinationResult(
            task_id=task_id, strategy="single", final_output=output,
            sub_results=[TaskResult(task_id=task_id, status="completed", output=output)],
            consensus_score=1.0,
        )

    async def _execute_raid(
        self, task_id: str, description: str, level: int = 3
    ) -> CoordinationResult:
        """Multi-agent consensus via RAID engine."""
        try:
            from services.raid_engine import RaidEngine, RaidLevel
            db = self._get_db()
            engine = RaidEngine(db)
            raid_level = {1: RaidLevel.RAID_1, 2: RaidLevel.RAID_2,
                          3: RaidLevel.RAID_3, 5: RaidLevel.RAID_5}.get(level, RaidLevel.RAID_3)
            result = await engine.execute(description, level=raid_level)
            return CoordinationResult(
                task_id=task_id, strategy=f"raid{level}",
                final_output=result.output,
                consensus_score=result.consensus_score,
            )
        except Exception as e:
            logger.warning("RAID-%d failed, falling back to single: %s", level, e)
            return await self._execute_single(task_id, description, "general_computation")

    async def _execute_deerflow(
        self, task_id: str, description: str
    ) -> CoordinationResult:
        """Multi-step research via DeerFlow pipeline."""
        try:
            from services.deep_research import DeepResearchPipeline
            pipeline = DeepResearchPipeline()
            result = await pipeline.run(topic=description, depth="standard")
            return CoordinationResult(
                task_id=task_id, strategy="deerflow",
                final_output=result.get("report", ""),
                consensus_score=1.0,
            )
        except Exception as e:
            logger.warning("DeerFlow failed, falling back to RAID-3: %s", e)
            return await self._execute_raid(task_id, description, level=3)

    async def _execute_a2a(
        self, task_id: str, description: str
    ) -> CoordinationResult:
        """Task decomposition via A2A protocol."""
        try:
            from services.a2a_protocol import A2ACoordinator
            db = self._get_db()
            coordinator = A2ACoordinator()
            subtask_ids = await coordinator.decompose(
                parent_task_id=task_id, num_workers=3, db=db,
            )
            # A2A creates async subtasks — for immediate results, fall back to RAID
            return await self._execute_raid(task_id, description, level=3)
        except Exception as e:
            logger.warning("A2A failed, falling back to single: %s", e)
            return await self._execute_single(task_id, description, "general_computation")

    def _get_db(self):
        """Get or create a database session."""
        if self._db:
            return self._db
        from utils.database import get_db_context
        return get_db_context().__enter__()

    @property
    def history(self) -> List[CoordinationResult]:
        return list(self._execution_history)


# ─────────────────────────────────────────────────────────────────────────────
# Convenience
# ─────────────────────────────────────────────────────────────────────────────

_default_pa: Optional[ProxyAgent] = None


def get_proxy_agent(db=None) -> ProxyAgent:
    """Get the default ProxyAgent singleton."""
    global _default_pa
    if _default_pa is None:
        _default_pa = ProxyAgent(db_session=db)
    return _default_pa
