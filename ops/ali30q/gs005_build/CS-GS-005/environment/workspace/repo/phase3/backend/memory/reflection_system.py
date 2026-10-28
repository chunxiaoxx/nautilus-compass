"""
Reflection System

Implements agent reflection and learning from task execution.
Generates insights and updates agent skills based on experience.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncpg

from .agent_memory import AgentMemorySystem

logger = logging.getLogger(__name__)


class ReflectionSystem:
    """System for agent reflection and learning."""

    def __init__(self, db_pool: asyncpg.Pool, memory_system: AgentMemorySystem):
        """
        Initialize the reflection system.

        Args:
            db_pool: PostgreSQL connection pool
            memory_system: Agent memory system instance
        """
        self.db_pool = db_pool
        self.memory_system = memory_system
        logger.info("ReflectionSystem initialized")

    async def reflect_on_task(
        self,
        agent_id: int,
        task_id: int,
        result: Dict[str, Any]
    ) -> int:
        """
        Generate reflection on a completed task.

        Args:
            agent_id: ID of the agent
            task_id: ID of the task
            result: Task execution result

        Returns:
            ID of the created reflection record
        """
        try:
            # Find similar past tasks
            similar_memories = await self.memory_system.find_similar_memories(
                agent_id=agent_id,
                query_text=result.get("description", ""),
                limit=3,
                memory_type="task_execution"
            )

            # Generate reflection text
            reflection_text = self._generate_reflection(result, similar_memories)

            # Extract insights
            insights = self._extract_insights(result, similar_memories)

            # Calculate importance score
            importance_score = self._calculate_importance(result)

            # Store reflection
            async with self.db_pool.acquire() as conn:
                reflection_id = await conn.fetchval(
                    """
                    INSERT INTO agent_reflections
                    (agent_id, task_id, reflection_text, insights, importance_score)
                    VALUES ($1, $2, $3, $4, $5)
                    RETURNING id
                    """,
                    agent_id,
                    task_id,
                    reflection_text,
                    json.dumps(insights),
                    importance_score
                )

            # Update agent skills
            await self._update_agent_skills(agent_id, result, insights)

            logger.info(f"Created reflection {reflection_id} for agent {agent_id}, task {task_id}")
            return reflection_id

        except Exception as e:
            logger.error(f"Error creating reflection: {e}")
            raise

    async def get_agent_reflections(
        self,
        agent_id: int,
        limit: int = 10,
        min_importance: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        Get reflections for an agent.

        Args:
            agent_id: ID of the agent
            limit: Maximum number of results to return
            min_importance: Minimum importance score filter

        Returns:
            List of reflection records
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_id, task_id, reflection_text,
                           insights, importance_score, created_at
                    FROM agent_reflections
                    WHERE agent_id = $1 AND importance_score >= $2
                    ORDER BY importance_score DESC, created_at DESC
                    LIMIT $3
                    """,
                    agent_id,
                    min_importance,
                    limit
                )

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "agent_id": row["agent_id"],
                    "task_id": row["task_id"],
                    "reflection_text": row["reflection_text"],
                    "insights": json.loads(row["insights"]) if row["insights"] else {},
                    "importance_score": float(row["importance_score"]),
                    "created_at": row["created_at"].isoformat()
                })

            return results

        except Exception as e:
            logger.error(f"Error getting reflections: {e}")
            raise

    async def get_agent_skills(self, agent_id: int) -> List[Dict[str, Any]]:
        """
        Get skills for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            List of skill records
        """
        try:
            async with self.db_pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, agent_id, skill_name, skill_level, experience,
                           success_count, failure_count, last_used, metadata,
                           created_at, updated_at
                    FROM agent_skills
                    WHERE agent_id = $1
                    ORDER BY skill_level DESC, experience DESC
                    """,
                    agent_id
                )

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "agent_id": row["agent_id"],
                    "skill_name": row["skill_name"],
                    "skill_level": row["skill_level"],
                    "experience": row["experience"],
                    "success_count": row["success_count"],
                    "failure_count": row["failure_count"],
                    "success_rate": self._calculate_success_rate(
                        row["success_count"],
                        row["failure_count"]
                    ),
                    "last_used": row["last_used"].isoformat() if row["last_used"] else None,
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "created_at": row["created_at"].isoformat(),
                    "updated_at": row["updated_at"].isoformat()
                })

            return results

        except Exception as e:
            logger.error(f"Error getting agent skills: {e}")
            raise

    def _generate_reflection(
        self,
        result: Dict[str, Any],
        similar_memories: List[Dict[str, Any]]
    ) -> str:
        """Generate reflection text based on task result and similar memories."""
        parts = []

        # Task outcome
        status = result.get("status", "unknown")
        parts.append(f"Task completed with status: {status}")

        # Performance comparison
        if similar_memories:
            parts.append(f"Found {len(similar_memories)} similar past tasks")
            avg_similarity = sum(m["similarity"] for m in similar_memories) / len(similar_memories)
            parts.append(f"Average similarity: {avg_similarity:.2f}")

        # Key learnings
        if status == "COMPLETED":
            parts.append("Successfully completed task")
        elif status == "FAILED":
            error = result.get("error", "Unknown error")
            parts.append(f"Task failed: {error}")

        return " | ".join(parts)

    def _extract_insights(
        self,
        result: Dict[str, Any],
        similar_memories: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Extract insights from task execution."""
        insights = {
            "task_type": result.get("task_type", "unknown"),
            "status": result.get("status", "unknown"),
            "similar_tasks_count": len(similar_memories),
            "timestamp": datetime.utcnow().isoformat()
        }

        # Add performance metrics if available
        if "execution_time" in result:
            insights["execution_time"] = result["execution_time"]

        if "error" in result:
            insights["error_type"] = result.get("error_type", "unknown")
            insights["error_message"] = result["error"]

        return insights

    def _calculate_importance(self, result: Dict[str, Any]) -> float:
        """Calculate importance score for a reflection."""
        score = 0.5  # Base score

        # Increase importance for failures (learning opportunity)
        if result.get("status") == "FAILED":
            score += 0.3

        # Increase importance for complex tasks
        if result.get("task_type") in ["CODE", "RESEARCH"]:
            score += 0.1

        # Increase importance for long-running tasks
        if result.get("execution_time", 0) > 300:  # 5 minutes
            score += 0.1

        return min(score, 1.0)

    async def _update_agent_skills(
        self,
        agent_id: int,
        result: Dict[str, Any],
        insights: Dict[str, Any]
    ):
        """Update agent skills based on task execution."""
        try:
            task_type = result.get("task_type", "unknown")
            status = result.get("status", "unknown")

            # Determine skill name from task type
            skill_name = f"{task_type.lower()}_execution"

            # Calculate experience gain
            experience_gain = 10 if status == "COMPLETED" else 5

            async with self.db_pool.acquire() as conn:
                # Upsert skill record
                await conn.execute(
                    """
                    INSERT INTO agent_skills
                    (agent_id, skill_name, skill_level, experience,
                     success_count, failure_count, last_used, metadata, updated_at)
                    VALUES ($1, $2, 1, $3, $4, $5, NOW(), $6, NOW())
                    ON CONFLICT (agent_id, skill_name)
                    DO UPDATE SET
                        experience = agent_skills.experience + $3,
                        success_count = agent_skills.success_count + $4,
                        failure_count = agent_skills.failure_count + $5,
                        last_used = NOW(),
                        updated_at = NOW(),
                        skill_level = LEAST(10, 1 + (agent_skills.experience + $3) / 100)
                    """,
                    agent_id,
                    skill_name,
                    experience_gain,
                    1 if status == "COMPLETED" else 0,
                    1 if status == "FAILED" else 0,
                    json.dumps(insights)
                )

            logger.info(f"Updated skill {skill_name} for agent {agent_id}")

        except Exception as e:
            logger.error(f"Error updating agent skills: {e}")
            # Don't raise - skill update is not critical

    def _calculate_success_rate(self, success_count: int, failure_count: int) -> float:
        """Calculate success rate from counts."""
        total = success_count + failure_count
        if total == 0:
            return 0.0
        return success_count / total


# Global instance
_reflection_system = None


async def get_reflection_system(
    db_pool: asyncpg.Pool,
    memory_system: AgentMemorySystem
) -> ReflectionSystem:
    """Get or create the global reflection system instance."""
    global _reflection_system
    if _reflection_system is None:
        _reflection_system = ReflectionSystem(db_pool, memory_system)
    return _reflection_system
