"""
Agent Memory System

Manages storage and retrieval of agent task execution memories.
Supports semantic similarity search using vector embeddings.
"""

import json
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import asyncpg

from .embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class AgentMemorySystem:
    """System for managing agent memories with vector similarity search."""

    def __init__(self, db_pool: asyncpg.Pool):
        """
        Initialize the memory system.

        Args:
            db_pool: PostgreSQL connection pool
        """
        self.db_pool = db_pool
        self.embedding_service = get_embedding_service()
        logger.info("AgentMemorySystem initialized")

    async def store_task_memory(
        self,
        agent_id: int,
        task_id: int,
        execution_data: Dict[str, Any],
        memory_type: str = "task_execution"
    ) -> int:
        """
        Store a task execution memory.

        Args:
            agent_id: ID of the agent
            task_id: ID of the task
            execution_data: Dictionary containing execution details
            memory_type: Type of memory (task_execution, observation, plan, error, success)

        Returns:
            ID of the created memory record
        """
        try:
            # Create text representation for embedding
            text_content = self._create_memory_text(execution_data)

            # Generate embedding
            embedding = await self.embedding_service.embed(text_content)

            # Store in database
            async with self.db_pool.acquire() as conn:
                memory_id = await conn.fetchval(
                    """
                    INSERT INTO agent_memories
                    (agent_id, task_id, memory_type, content, embedding, metadata)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    RETURNING id
                    """,
                    agent_id,
                    task_id,
                    memory_type,
                    json.dumps(execution_data),
                    embedding,
                    json.dumps({"stored_at": datetime.utcnow().isoformat()})
                )

            logger.info(f"Stored memory {memory_id} for agent {agent_id}, task {task_id}")
            return memory_id

        except Exception as e:
            logger.error(f"Error storing task memory: {e}")
            raise

    async def find_similar_memories(
        self,
        agent_id: int,
        query_text: str,
        limit: int = 5,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Find similar memories using vector similarity search.

        Args:
            agent_id: ID of the agent
            query_text: Text to search for similar memories
            limit: Maximum number of results to return
            memory_type: Optional filter by memory type

        Returns:
            List of similar memory records with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = await self.embedding_service.embed(query_text)

            # Search for similar memories
            async with self.db_pool.acquire() as conn:
                if memory_type:
                    query = """
                        SELECT
                            id, agent_id, task_id, memory_type, content,
                            created_at, metadata,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM agent_memories
                        WHERE agent_id = $2 AND memory_type = $3
                        ORDER BY embedding <=> $1::vector
                        LIMIT $4
                    """
                    rows = await conn.fetch(query, query_embedding, agent_id, memory_type, limit)
                else:
                    query = """
                        SELECT
                            id, agent_id, task_id, memory_type, content,
                            created_at, metadata,
                            1 - (embedding <=> $1::vector) as similarity
                        FROM agent_memories
                        WHERE agent_id = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, query_embedding, agent_id, limit)

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "agent_id": row["agent_id"],
                    "task_id": row["task_id"],
                    "memory_type": row["memory_type"],
                    "content": json.loads(row["content"]),
                    "created_at": row["created_at"].isoformat(),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {},
                    "similarity": float(row["similarity"])
                })

            logger.info(f"Found {len(results)} similar memories for agent {agent_id}")
            return results

        except Exception as e:
            logger.error(f"Error finding similar memories: {e}")
            raise

    async def get_recent_memories(
        self,
        agent_id: int,
        limit: int = 10,
        memory_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get recent memories for an agent.

        Args:
            agent_id: ID of the agent
            limit: Maximum number of results to return
            memory_type: Optional filter by memory type

        Returns:
            List of recent memory records
        """
        try:
            async with self.db_pool.acquire() as conn:
                if memory_type:
                    query = """
                        SELECT id, agent_id, task_id, memory_type, content,
                               created_at, metadata
                        FROM agent_memories
                        WHERE agent_id = $1 AND memory_type = $2
                        ORDER BY created_at DESC
                        LIMIT $3
                    """
                    rows = await conn.fetch(query, agent_id, memory_type, limit)
                else:
                    query = """
                        SELECT id, agent_id, task_id, memory_type, content,
                               created_at, metadata
                        FROM agent_memories
                        WHERE agent_id = $1
                        ORDER BY created_at DESC
                        LIMIT $2
                    """
                    rows = await conn.fetch(query, agent_id, limit)

            results = []
            for row in rows:
                results.append({
                    "id": row["id"],
                    "agent_id": row["agent_id"],
                    "task_id": row["task_id"],
                    "memory_type": row["memory_type"],
                    "content": json.loads(row["content"]),
                    "created_at": row["created_at"].isoformat(),
                    "metadata": json.loads(row["metadata"]) if row["metadata"] else {}
                })

            return results

        except Exception as e:
            logger.error(f"Error getting recent memories: {e}")
            raise

    async def get_memory_stats(self, agent_id: int) -> Dict[str, Any]:
        """
        Get memory statistics for an agent.

        Args:
            agent_id: ID of the agent

        Returns:
            Dictionary containing memory statistics
        """
        try:
            async with self.db_pool.acquire() as conn:
                stats = await conn.fetchrow(
                    """
                    SELECT
                        COUNT(*) as total_memories,
                        COUNT(DISTINCT memory_type) as memory_types,
                        COUNT(DISTINCT task_id) as unique_tasks,
                        MIN(created_at) as first_memory,
                        MAX(created_at) as last_memory
                    FROM agent_memories
                    WHERE agent_id = $1
                    """,
                    agent_id
                )

                type_counts = await conn.fetch(
                    """
                    SELECT memory_type, COUNT(*) as count
                    FROM agent_memories
                    WHERE agent_id = $1
                    GROUP BY memory_type
                    ORDER BY count DESC
                    """,
                    agent_id
                )

            return {
                "total_memories": stats["total_memories"],
                "memory_types": stats["memory_types"],
                "unique_tasks": stats["unique_tasks"],
                "first_memory": stats["first_memory"].isoformat() if stats["first_memory"] else None,
                "last_memory": stats["last_memory"].isoformat() if stats["last_memory"] else None,
                "type_distribution": {row["memory_type"]: row["count"] for row in type_counts}
            }

        except Exception as e:
            logger.error(f"Error getting memory stats: {e}")
            raise

    def _create_memory_text(self, execution_data: Dict[str, Any]) -> str:
        """
        Create a text representation of execution data for embedding.

        Args:
            execution_data: Dictionary containing execution details

        Returns:
            Text representation
        """
        parts = []

        if "description" in execution_data:
            parts.append(f"Task: {execution_data['description']}")

        if "task_type" in execution_data:
            parts.append(f"Type: {execution_data['task_type']}")

        if "result" in execution_data:
            parts.append(f"Result: {execution_data['result']}")

        if "status" in execution_data:
            parts.append(f"Status: {execution_data['status']}")

        if "error" in execution_data:
            parts.append(f"Error: {execution_data['error']}")

        return " | ".join(parts)


# Global instance
_memory_system = None


async def get_memory_system(db_pool: asyncpg.Pool) -> AgentMemorySystem:
    """Get or create the global memory system instance."""
    global _memory_system
    if _memory_system is None:
        _memory_system = AgentMemorySystem(db_pool)
    return _memory_system
