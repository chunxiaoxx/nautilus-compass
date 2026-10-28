"""Agent team coordination - dynamic assembly, role assignment, parallel execution."""
import asyncio
import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel
from sqlalchemy.orm import Session

from models.database import Agent
from models.team import Team, TeamMember

logger = logging.getLogger(__name__)


class AgentRole(str, Enum):
    LEADER = "leader"
    EXECUTOR = "executor"
    REVIEWER = "reviewer"
    SPECIALIST = "specialist"


class TeamResult(BaseModel):
    team_id: str
    status: str
    subtask_results: List[dict]
    final_output: str
    quality_score: float
    members: List[dict]


class AgentTeamService:
    """Coordinates dynamic team assembly, task decomposition, and parallel execution."""

    SYSTEM_PROMPT = (
        "You are Nautilus team coordinator. "
        "Respond ONLY with valid JSON, no markdown fences."
    )

    def __init__(self, db: Session):
        self._db = db
        self._llm = None

    @property
    def llm(self):
        if self._llm is None:
            from agent_engine.llm.client import get_llm_client
            self._llm = get_llm_client()
        return self._llm

    # -- Assembly --

    async def assemble(
        self,
        task_description: str,
        task_id: Optional[str] = None,
        min_agents: int = 3,
    ) -> dict:
        """Dynamically assemble a team based on task requirements."""
        capabilities = await self._extract_capabilities(task_description)
        agents = self._find_matching_agents(capabilities, min_agents)
        if len(agents) < min_agents:
            raise ValueError(
                f"Not enough agents: found {len(agents)}, need {min_agents}"
            )

        team_id = str(uuid.uuid4())
        sorted_agents = sorted(agents, key=lambda a: a.reputation or 0, reverse=True)
        role_map = self._assign_roles(sorted_agents)

        team = Team(
            team_id=team_id,
            name=f"Team-{team_id[:8]}",
            task_id=task_id,
            status="assembling",
            leader_agent_id=sorted_agents[0].agent_id,
        )
        self._db.add(team)

        members_info: List[dict] = []
        for agent, role in role_map:
            member = TeamMember(
                team_id=team_id,
                agent_id=agent.agent_id,
                role=role.value,
                status="assigned",
            )
            self._db.add(member)
            members_info.append({
                "agent_id": agent.agent_id,
                "name": agent.name,
                "role": role.value,
                "reputation": agent.reputation,
            })

        team.status = "active"
        self._db.commit()

        logger.info(
            "Team %s assembled: %d members for task %s",
            team_id, len(members_info), task_id,
        )
        return {"team_id": team_id, "members": members_info, "status": "active"}

    # -- Task decomposition --

    async def decompose_task(self, team_id: str, task_description: str) -> List[dict]:
        """Decompose a task into subtasks via LLM and assign to executors."""
        members = self._get_active_members(team_id)
        executors = [m for m in members if m.role in (AgentRole.EXECUTOR.value, AgentRole.SPECIALIST.value)]

        prompt = (f"Decompose the following task into {len(executors)} subtasks.\n"
                  f"Task: {task_description}\n"
                  f"Return JSON: {{\"subtasks\": [\"subtask1\", \"subtask2\", ...]}}")
        raw = await asyncio.to_thread(self.llm.chat, prompt, system=self.SYSTEM_PROMPT, max_tokens=1024)
        subtasks = self._parse_subtasks(raw, len(executors))

        for executor, subtask_text in zip(executors, subtasks):
            executor.subtask = subtask_text
            executor.status = "assigned"

        self._db.commit()
        logger.info("Team %s: decomposed into %d subtasks", team_id, len(subtasks))

        return [{"agent_id": e.agent_id, "subtask": e.subtask} for e in executors]

    # -- Parallel execution --

    async def execute_as_team(self, team_id: str) -> TeamResult:
        """Execute all subtasks in parallel, review, and merge results."""
        team = self._get_team(team_id)
        members = self._get_active_members(team_id)

        executors = [m for m in members if m.role in (AgentRole.EXECUTOR.value, AgentRole.SPECIALIST.value)]
        reviewer = next((m for m in members if m.role == AgentRole.REVIEWER.value), None)
        leader = next((m for m in members if m.role == AgentRole.LEADER.value), None)

        # 1. Parallel subtask execution
        execution_tasks = [
            self._execute_subtask(m) for m in executors if m.subtask
        ]
        results = await asyncio.gather(*execution_tasks, return_exceptions=True)
        subtask_results = self._collect_results(executors, results)

        # 2. Review
        quality_score = await self._review_results(subtask_results, reviewer)

        # 3. Merge
        final_output = await self._merge_results(subtask_results, leader)

        # 4. Persist
        team.status = "completed"
        team.completed_at = datetime.utcnow()
        team.quality_score = quality_score
        team.final_output = final_output
        self._db.commit()

        logger.info(
            "Team %s completed: quality=%.2f", team_id, quality_score,
        )
        return TeamResult(
            team_id=team_id,
            status="completed",
            subtask_results=subtask_results,
            final_output=final_output,
            quality_score=quality_score,
            members=[
                {"agent_id": m.agent_id, "role": m.role, "status": m.status}
                for m in members
            ],
        )

    # -- Dissolve --

    async def dissolve(self, team_id: str) -> None:
        """Dissolve team and boost collaboration scores for participants."""
        team = self._get_team(team_id)
        members = self._get_active_members(team_id)

        for member in members:
            self._update_collaboration_score(member.agent_id, team.quality_score)

        team.status = "dissolved"
        self._db.commit()
        logger.info("Team %s dissolved, %d members scored", team_id, len(members))

    # -- Internal helpers --

    async def _extract_capabilities(self, task_description: str) -> List[str]:
        """Use LLM to extract required capabilities from a task."""
        prompt = (f"Extract required capabilities for this task.\n"
                  f"Task: {task_description}\n"
                  f"Return JSON: {{\"capabilities\": [\"cap1\", \"cap2\"]}}")
        raw = await asyncio.to_thread(self.llm.chat, prompt, system=self.SYSTEM_PROMPT, max_tokens=512)
        return self._parse_capabilities(raw)

    def _find_matching_agents(self, capabilities: List[str], min_count: int) -> List[Agent]:
        """Query agents whose specialties overlap with required capabilities."""
        all_agents = (
            self._db.query(Agent)
            .filter(Agent.specialties.isnot(None))
            .order_by(Agent.reputation.desc())
            .all()
        )
        scored: List[tuple] = []
        for agent in all_agents:
            try:
                specs = json.loads(agent.specialties) if agent.specialties else []
            except (json.JSONDecodeError, TypeError):
                specs = []
            overlap = len(set(s.lower() for s in specs) & set(c.lower() for c in capabilities))
            if overlap > 0:
                scored.append((agent, overlap))

        scored.sort(key=lambda x: (-x[1], -(x[0].reputation or 0)))
        matched = [a for a, _ in scored]

        # If not enough matches, fill from highest-reputation agents
        if len(matched) < min_count:
            existing_ids = {a.agent_id for a in matched}
            fillers = [a for a in all_agents if a.agent_id not in existing_ids]
            matched.extend(fillers[: min_count - len(matched)])

        return matched[:max(min_count, len(matched))]

    @staticmethod
    def _assign_roles(sorted_agents: List[Agent]) -> List[tuple]:
        """Assign roles based on sorted-by-reputation list."""
        role_map: List[tuple] = []
        for i, agent in enumerate(sorted_agents):
            if i == 0:
                role_map.append((agent, AgentRole.LEADER))
            elif i == len(sorted_agents) - 1 and len(sorted_agents) > 2:
                role_map.append((agent, AgentRole.REVIEWER))
            else:
                role_map.append((agent, AgentRole.EXECUTOR))
        return role_map

    async def _execute_subtask(self, member: TeamMember) -> str:
        """Execute a single subtask via LLM."""
        prompt = (f"Execute the following subtask and provide a concise result.\n"
                  f"Subtask: {member.subtask}")
        member.status = "working"
        self._db.flush()

        result = await asyncio.to_thread(self.llm.chat, prompt, system=self.SYSTEM_PROMPT, max_tokens=2048)
        member.result = result
        member.status = "completed"
        self._db.flush()
        return result

    def _collect_results(self, executors: List[TeamMember], results: list) -> List[dict]:
        """Collect subtask results, marking failures."""
        collected: List[dict] = []
        for member, result in zip(executors, results):
            if isinstance(result, Exception):
                member.status = "failed"
                member.result = str(result)
                collected.append({
                    "agent_id": member.agent_id,
                    "subtask": member.subtask,
                    "result": None,
                    "error": str(result),
                })
            else:
                collected.append({
                    "agent_id": member.agent_id,
                    "subtask": member.subtask,
                    "result": result,
                    "error": None,
                })
        return collected

    async def _review_results(self, subtask_results: List[dict], reviewer: Optional[TeamMember]) -> float:
        """Reviewer scores the combined results. Returns 0-1 quality score."""
        if not reviewer:
            return 0.7  # default when no reviewer

        results_text = json.dumps(subtask_results, default=str)
        prompt = (f"Review these subtask results and rate overall quality 0-100.\n"
                  f"Results: {results_text[:3000]}\n"
                  f"Return JSON: {{\"score\": <number>, \"feedback\": \"...\"}}")
        raw = await asyncio.to_thread(self.llm.chat, prompt, system=self.SYSTEM_PROMPT, max_tokens=512)
        reviewer.status = "completed"
        reviewer.result = raw
        self._db.flush()

        return self._parse_review_score(raw)

    async def _merge_results(self, subtask_results: List[dict], leader: Optional[TeamMember]) -> str:
        """Leader merges subtask results into final output."""
        successful = [r for r in subtask_results if r.get("result")]
        if not successful:
            return "No successful subtask results to merge."

        results_text = json.dumps(successful, default=str)
        prompt = (f"Merge these subtask results into a single coherent output.\n"
                  f"Results: {results_text[:3000]}\n"
                  f"Provide the merged final output as plain text.")
        merged = await asyncio.to_thread(self.llm.chat, prompt, system=self.SYSTEM_PROMPT, max_tokens=2048)
        if leader:
            leader.status = "completed"
            leader.result = merged
            self._db.flush()
        return merged

    def _update_collaboration_score(self, agent_id: int, quality_score: Optional[float]) -> None:
        """Boost agent collaboration score in survival record."""
        from models.agent_survival import AgentSurvival
        from services.survival_service import SurvivalService

        survival = self._db.query(AgentSurvival).filter(
            AgentSurvival.agent_id == agent_id
        ).first()
        if not survival:
            return

        boost = min((quality_score or 0.5) * 0.1, 0.1)
        new_score = min(survival.collaboration_score + boost, 1.0)

        SurvivalService.update_agent_survival(
            db=self._db,
            agent_id=agent_id,
            collaboration_score=new_score,
        )
        logger.info(
            "Agent %d collaboration score updated: %.3f -> %.3f",
            agent_id, survival.collaboration_score, new_score,
        )

    # -- DB lookups --

    def _get_team(self, team_id: str) -> Team:
        team = self._db.query(Team).filter(Team.team_id == team_id).first()
        if not team:
            raise ValueError(f"Team {team_id} not found")
        return team

    def _get_active_members(self, team_id: str) -> List[TeamMember]:
        return (
            self._db.query(TeamMember)
            .filter(TeamMember.team_id == team_id)
            .all()
        )

    # -- Parsing helpers --

    @staticmethod
    def _parse_capabilities(raw: str) -> List[str]:
        try:
            data = json.loads(raw)
            caps = data.get("capabilities", [])
            return caps if isinstance(caps, list) else []
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse capabilities from LLM: %s", raw[:200])
            return ["general"]

    @staticmethod
    def _parse_subtasks(raw: str, expected: int) -> List[str]:
        try:
            data = json.loads(raw)
            subtasks = data.get("subtasks", [])
            if isinstance(subtasks, list) and len(subtasks) >= 1:
                return subtasks[:expected]
        except (json.JSONDecodeError, TypeError):
            logger.warning("Failed to parse subtasks from LLM: %s", raw[:200])
        return [f"Subtask {i + 1}" for i in range(expected)]

    @staticmethod
    def _parse_review_score(raw: str) -> float:
        try:
            data = json.loads(raw)
            score = float(data.get("score", 70))
            return max(0.0, min(score / 100.0, 1.0))
        except (json.JSONDecodeError, TypeError, ValueError):
            logger.warning("Failed to parse review score: %s", raw[:200])
            return 0.7
