"""
Intelligent task routing - classify, match, and route tasks to best agents.

Dual-path classification (keyword fast-match + LLM fallback),
agent matching by capability/reputation/load, and raid level suggestion.
"""
import asyncio
import json
import logging
import os
import re
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from models.database import Agent, Task

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Keyword classification tables (fast path, <1ms)
# ---------------------------------------------------------------------------
KEYWORDS: dict[str, list[str]] = {
    "code": [
        "代码", "编程", "函数", "bug", "修复", "debug", "重构", "优化",
        "python", "javascript", "typescript", "rust", "golang", "api",
    ],
    "data_labeling": [
        "标注", "分类", "情感", "实体", "标签", "label", "annotate",
        "sentiment", "ner", "tagging",
    ],
    "scientific": [
        "仿真", "拟合", "模拟", "方程", "物理", "本构", "ode", "pde",
        "scipy", "matplotlib", "数值", "计算",
    ],
    "research": [
        "调研", "分析", "报告", "论文", "综述", "review", "survey",
        "research", "literature", "meta-analysis",
    ],
    "simulation": [
        "动力学", "碰撞", "传感器", "场景", "运动规划", "机器人",
        "robotics", "planning", "trajectory",
    ],
}

# Complexity heuristics
_LONG_DESC_THRESHOLD = int(os.getenv("ROUTER_LONG_DESC_LEN", "500"))
_HIGH_KEYWORD_DENSITY = float(os.getenv("ROUTER_HIGH_DENSITY", "0.08"))
_KEYWORD_CONFIDENCE_THRESHOLD = float(os.getenv("ROUTER_KW_CONFIDENCE", "0.7"))
_MAX_MATCHED_AGENTS = int(os.getenv("ROUTER_MAX_AGENTS", "5"))


# ---------------------------------------------------------------------------
# Enums & models
# ---------------------------------------------------------------------------
class TaskComplexity(str, Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    CRITICAL = "critical"


class TaskClassification(BaseModel):
    task_type: str
    complexity: TaskComplexity
    confidence: float
    required_capabilities: List[str]
    suggested_raid_level: int
    classification_method: str  # "keyword" or "llm"


class RoutingDecision(BaseModel):
    task_type: str
    matched_agents: List[dict]
    suggested_raid_level: int
    use_team: bool
    reason: str


# ---------------------------------------------------------------------------
# Raid-level mapping (loaded from config/raid_harness.yaml)
# ---------------------------------------------------------------------------
from services.raid_config import get_complexity_raid_mapping as _get_crm

def _build_raid_map() -> dict["TaskComplexity", int]:
    raw = _get_crm()
    return {TaskComplexity(k): v for k, v in raw.items()}

_RAID_MAP: dict[TaskComplexity, int] = _build_raid_map()


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
class TaskRouter:
    """Classify tasks and route them to the best-fit agents."""

    def __init__(self, db: Session, llm=None):
        self._db = db
        self._llm = llm

    # -- lazy LLM accessor --------------------------------------------------
    @property
    def llm(self):
        if self._llm is None:
            from agent_engine.llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    # -- public API ----------------------------------------------------------
    def classify(self, description: str) -> TaskClassification:
        """Dual-path: keyword fast match, fallback to LLM if low confidence."""
        result = self._classify_by_keywords(description)
        if result.confidence >= _KEYWORD_CONFIDENCE_THRESHOLD:
            logger.info("Keyword classification accepted (confidence=%.2f)", result.confidence)
            return result
        logger.info("Keyword confidence %.2f < threshold, falling back to LLM", result.confidence)
        return self._classify_by_llm(description, keyword_hint=result.task_type)

    async def route(self, task_id: str, description: str) -> RoutingDecision:
        """Full routing: classify -> match agents -> decide execution mode."""
        classification = await asyncio.to_thread(self.classify, description)
        agents = await self.match_agents(
            classification.required_capabilities,
            limit=_MAX_MATCHED_AGENTS,
        )
        use_team = classification.complexity in (TaskComplexity.COMPLEX, TaskComplexity.CRITICAL)
        reason = self._build_reason(classification, len(agents))
        logger.info(
            "Routed task %s: type=%s raid=%d agents=%d team=%s",
            task_id, classification.task_type,
            classification.suggested_raid_level, len(agents), use_team,
        )
        return RoutingDecision(
            task_type=classification.task_type,
            matched_agents=agents,
            suggested_raid_level=classification.suggested_raid_level,
            use_team=use_team,
            reason=reason,
        )

    async def match_agents(
        self, required_capabilities: List[str], limit: int = 5
    ) -> List[dict]:
        """Find best agents by capability + reputation + current load."""
        agents = await asyncio.to_thread(self._query_agents, required_capabilities, limit)
        return agents

    # -- keyword classification (fast path) ----------------------------------
    def _classify_by_keywords(self, description: str) -> TaskClassification:
        text = description.lower()
        tokens = re.findall(r"[\w\u4e00-\u9fff]+", text)
        token_count = max(len(tokens), 1)

        scores: dict[str, int] = {}
        for category, kws in KEYWORDS.items():
            hits = sum(1 for kw in kws if kw in text)
            scores[category] = hits

        best_cat = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_hits = scores[best_cat]

        if best_hits == 0:
            confidence = 0.0
            task_type = "other"
        else:
            density = best_hits / token_count
            confidence = min(0.5 + density / _HIGH_KEYWORD_DENSITY * 0.5, 1.0)
            task_type = best_cat

        complexity = self._estimate_complexity(description, best_hits)
        raid_level = _RAID_MAP[complexity]
        capabilities = self._capabilities_for(task_type)

        return TaskClassification(
            task_type=task_type,
            complexity=complexity,
            confidence=round(confidence, 3),
            required_capabilities=capabilities,
            suggested_raid_level=raid_level,
            classification_method="keyword",
        )

    # -- LLM classification (precise path) -----------------------------------
    def _classify_by_llm(
        self, description: str, keyword_hint: str = ""
    ) -> TaskClassification:
        system = (
            "You are a task classifier for an AI-agent platform. "
            "Return ONLY valid JSON with keys: task_type, complexity, "
            "required_capabilities. task_type is one of: code, data_labeling, "
            "scientific, research, simulation, other. complexity is one of: "
            "simple, moderate, complex, critical. required_capabilities is a "
            "list of strings."
        )
        prompt = (
            f"Classify this task. Keyword hint: '{keyword_hint}'.\n\n"
            f"Task description:\n{description[:2000]}"
        )
        try:
            raw = self.llm.chat(prompt, system=system, max_tokens=512, temperature=0.1)
            parsed = self._parse_llm_response(raw)
            complexity = TaskComplexity(parsed.get("complexity", "moderate"))
            task_type = parsed.get("task_type", keyword_hint or "other")
            capabilities = parsed.get("required_capabilities", self._capabilities_for(task_type))
            return TaskClassification(
                task_type=task_type,
                complexity=complexity,
                confidence=0.85,
                required_capabilities=capabilities,
                suggested_raid_level=_RAID_MAP[complexity],
                classification_method="llm",
            )
        except Exception:
            logger.exception("LLM classification failed, using keyword fallback")
            return self._classify_by_keywords(description)

    # -- agent query ---------------------------------------------------------
    def _query_agents(
        self, required_capabilities: List[str], limit: int, task_type: str = ""
    ) -> List[dict]:
        query = self._db.query(Agent).filter(Agent.reputation > 0)

        if required_capabilities:
            cap_filters = [
                Agent.specialties.ilike(f"%{cap}%") for cap in required_capabilities
            ]
            from sqlalchemy import or_
            query = query.filter(or_(*cap_filters))

        agents = (
            query
            .order_by(desc(Agent.reputation), Agent.current_tasks)
            .limit(limit * 2)  # fetch more, then sort by capability score
            .all()
        )

        results: List[dict] = []
        for agent in agents:
            score = self._agent_match_score(agent, required_capabilities, task_type)
            results.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "reputation": agent.reputation,
                "current_tasks": agent.current_tasks,
                "score": round(score, 3),
            })

        results.sort(key=lambda a: a["score"], reverse=True)
        return results[:limit]

    # -- helpers -------------------------------------------------------------
    @staticmethod
    def _estimate_complexity(description: str, keyword_hits: int) -> TaskComplexity:
        length = len(description)
        if length > _LONG_DESC_THRESHOLD and keyword_hits >= 4:
            return TaskComplexity.CRITICAL
        if length > _LONG_DESC_THRESHOLD or keyword_hits >= 3:
            return TaskComplexity.COMPLEX
        if keyword_hits >= 2 or length > 200:
            return TaskComplexity.MODERATE
        return TaskComplexity.SIMPLE

    @staticmethod
    def _capabilities_for(task_type: str) -> List[str]:
        mapping: dict[str, list[str]] = {
            "code": ["programming", "debugging", "code_review"],
            "data_labeling": ["annotation", "classification", "nlp"],
            "scientific": ["numerical_computing", "modeling", "visualization"],
            "research": ["literature_review", "analysis", "writing"],
            "simulation": ["robotics", "physics_sim", "motion_planning"],
        }
        return mapping.get(task_type, ["general"])

    def _agent_match_score(self, agent: Agent, capabilities: List[str], task_type: str = "") -> float:
        """Score agent fitness: reputation (30%) + load (20%) + specialty (20%) + proven capability (30%)."""
        reputation_score = min(agent.reputation / 100.0, 1.0) * 0.3
        load_score = max(1.0 - (agent.current_tasks or 0) / 5.0, 0.0) * 0.2
        specialty_score = 0.0
        specialties_text = (agent.specialties or "").lower()
        if capabilities and specialties_text:
            matched = sum(1 for c in capabilities if c in specialties_text)
            specialty_score = (matched / len(capabilities)) * 0.2
        else:
            specialty_score = 0.1

        # Proven capability bonus: check agent_capability_stats for this task_type
        capability_score = 0.0
        if task_type:
            try:
                from sqlalchemy import text as sql_text
                row = self._db.execute(sql_text(
                    "SELECT total_attempts, success_count FROM agent_capability_stats "
                    "WHERE agent_id = :aid AND task_type = :tt"
                ), {"aid": agent.agent_id, "tt": task_type}).fetchone()
                if row and row.total_attempts >= 3:
                    success_rate = row.success_count / row.total_attempts
                    capability_score = success_rate * 0.3
                else:
                    capability_score = 0.1  # unknown capability, neutral
            except Exception:
                capability_score = 0.1

        total = reputation_score + load_score + specialty_score + capability_score

        # Apply routing weight overrides from platform_config
        try:
            from services.platform_config import get_config_sync
            overrides = get_config_sync(self._db, "routing_weights") or {}
            boost = overrides.get("task_type_boost", {}).get(task_type, 1.0)
            total *= boost
        except Exception:
            pass

        return total

    @staticmethod
    def _build_reason(classification: TaskClassification, agent_count: int) -> str:
        parts = [
            f"Task classified as '{classification.task_type}' "
            f"({classification.complexity.value}) via {classification.classification_method}.",
        ]
        if agent_count == 0:
            parts.append("No matching agents found; manual assignment recommended.")
        elif classification.complexity in (TaskComplexity.COMPLEX, TaskComplexity.CRITICAL):
            parts.append(
                f"Team execution recommended (Raid {classification.suggested_raid_level}) "
                f"with {agent_count} candidate agent(s)."
            )
        else:
            parts.append(
                f"Single-agent execution (Raid {classification.suggested_raid_level}) "
                f"with top candidate from {agent_count} match(es)."
            )
        return " ".join(parts)

    @staticmethod
    def _parse_llm_response(raw: str) -> dict:
        # Try to extract JSON from LLM response (may contain markdown fences)
        match = re.search(r"\{[^}]+\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group())
        return json.loads(raw)
