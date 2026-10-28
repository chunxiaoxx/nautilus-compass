"""
Memory API endpoints for agent memory system.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from utils.database import get_db
try:
    from memory.agent_memory import get_memory_system
    from memory.reflection_system import get_reflection_system
except ImportError:
    get_memory_system = None
    get_reflection_system = None
from utils.auth import get_current_agent
from models.database import Agent

router = APIRouter()
logger = logging.getLogger(__name__)


class MemoryResponse(BaseModel):
    """Memory response."""
    id: int
    agent_id: int
    task_id: Optional[int]
    memory_type: str
    content: Dict[str, Any]
    created_at: str
    metadata: Dict[str, Any]
    similarity: Optional[float] = None


class ReflectionResponse(BaseModel):
    """Reflection response."""
    id: int
    agent_id: int
    task_id: Optional[int]
    reflection_text: str
    insights: Dict[str, Any]
    importance_score: float
    created_at: str


class SkillResponse(BaseModel):
    """Skill response."""
    id: int
    agent_id: int
    skill_name: str
    skill_level: int
    experience: int
    success_count: int
    failure_count: int
    success_rate: float
    last_used: Optional[str]
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class MemoryStatsResponse(BaseModel):
    """Memory statistics response."""
    total_memories: int
    memory_types: int
    unique_tasks: int
    first_memory: Optional[str]
    last_memory: Optional[str]
    type_distribution: Dict[str, int]


@router.get("/memories", response_model=List[MemoryResponse])
async def get_agent_memories(
    request: Request,
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    limit: int = Query(10, ge=1, le=100),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get recent memories for the authenticated agent.

    **Authentication**: API Key required

    **Query Parameters**:
    - `memory_type`: Filter by type (task_execution, observation, plan, error, success)
    - `limit`: Maximum records to return (default: 10, max: 100)

    **Returns**: List of memory records
    """
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)

        memories = await memory_system.get_recent_memories(
            agent_id=current_agent.id,
            limit=limit,
            memory_type=memory_type
        )

        return memories
    except Exception as e:
        logger.error(f"Error getting memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memories"
        )


@router.get("/memories/search", response_model=List[MemoryResponse])
async def search_memories(
    request: Request,
    query: str = Query(..., description="Search query text"),
    memory_type: Optional[str] = Query(None, description="Filter by memory type"),
    limit: int = Query(5, ge=1, le=20),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Search for similar memories using semantic similarity.

    **Authentication**: API Key required

    **Query Parameters**:
    - `query`: Text to search for similar memories (required)
    - `memory_type`: Filter by type (optional)
    - `limit`: Maximum records to return (default: 5, max: 20)

    **Returns**: List of similar memory records with similarity scores
    """
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)

        memories = await memory_system.find_similar_memories(
            agent_id=current_agent.id,
            query_text=query,
            limit=limit,
            memory_type=memory_type
        )

        return memories
    except Exception as e:
        logger.error(f"Error searching memories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search memories"
        )


@router.get("/memories/stats", response_model=MemoryStatsResponse)
async def get_memory_stats(
    request: Request,
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get memory statistics for the authenticated agent.

    **Authentication**: API Key required

    **Returns**: Memory statistics including counts and distribution
    """
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)

        stats = await memory_system.get_memory_stats(current_agent.id)

        return stats
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve memory statistics"
        )


@router.get("/reflections", response_model=List[ReflectionResponse])
async def get_agent_reflections(
    request: Request,
    limit: int = Query(10, ge=1, le=100),
    min_importance: float = Query(0.0, ge=0.0, le=1.0),
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get reflections for the authenticated agent.

    **Authentication**: API Key required

    **Query Parameters**:
    - `limit`: Maximum records to return (default: 10, max: 100)
    - `min_importance`: Minimum importance score filter (0.0 to 1.0)

    **Returns**: List of reflection records
    """
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)
        reflection_system = await get_reflection_system(db_pool, memory_system)

        reflections = await reflection_system.get_agent_reflections(
            agent_id=current_agent.id,
            limit=limit,
            min_importance=min_importance
        )

        return reflections
    except Exception as e:
        logger.error(f"Error getting reflections: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve reflections"
        )


@router.get("/skills", response_model=List[SkillResponse])
async def get_agent_skills(
    request: Request,
    current_agent: Agent = Depends(get_current_agent)
):
    """
    Get skills for the authenticated agent.

    **Authentication**: API Key required

    **Returns**: List of skill records with proficiency levels
    """
    try:
        db_pool = await get_db_pool()
        memory_system = await get_memory_system(db_pool)
        reflection_system = await get_reflection_system(db_pool, memory_system)

        skills = await reflection_system.get_agent_skills(current_agent.id)

        return skills
    except Exception as e:
        logger.error(f"Error getting skills: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve skills"
        )
