"""
Claude Memory Bridge — bidirectional sync between Claude Code sessions and platform memory.

GET  /api/claude/memory/recall   — Load relevant memories at session start
POST /api/claude/memory/store    — Save key decisions during/after session
GET  /api/claude/memory/core     — Load all core-tier memories (persistent insights)
POST /api/claude/memory/reflect  — Trigger reflection to consolidate episodic → core

This is how Claude becomes a first-class citizen on the platform,
not an external operator whose memory dies with each session.
"""
import json
import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import text

from utils.database import get_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/claude/memory", tags=["Claude Memory Bridge"])

CLAUDE_AGENT_ID = 164  # KAIROS = Claude's on-platform identity


class StoreRequest(BaseModel):
    content: str
    tier: str = "core"
    importance: float = 0.7
    metadata: Optional[dict] = None


class RecallRequest(BaseModel):
    query: str
    limit: int = 5


# ── Recall: load memories at session start ───────────────────────────────────

@router.get("/recall")
def recall_memories(
    query: str = "current platform state and recent decisions",
    limit: int = 10,
    db: Session = Depends(get_db),
):
    """Recall relevant memories for Claude's session context.

    Uses recency + importance ranking (embedding similarity requires async).
    Call this at session start to load persistent context.
    """
    rows = db.execute(text(
        "SELECT memory_id, content, tier, importance, created_at::text "
        "FROM agent_memory_records "
        "WHERE agent_id = :aid "
        "ORDER BY "
        "  CASE tier WHEN 'core' THEN 0 WHEN 'episodic' THEN 1 ELSE 2 END, "
        "  importance DESC, created_at DESC "
        "LIMIT :lim"
    ), {"aid": CLAUDE_AGENT_ID, "lim": limit}).fetchall()

    memories = [
        {
            "memory_id": r.memory_id,
            "content": r.content,
            "tier": r.tier,
            "importance": r.importance,
            "created_at": r.created_at,
        }
        for r in rows
    ]

    return {
        "success": True,
        "data": {
            "agent_id": CLAUDE_AGENT_ID,
            "memories": memories,
            "count": len(memories),
        },
    }


@router.get("/core")
def get_core_memories(db: Session = Depends(get_db)):
    """Load all core-tier memories — persistent high-level insights.

    These survive across sessions and represent accumulated wisdom.
    """
    rows = db.execute(text(
        "SELECT memory_id, content, importance, created_at::text "
        "FROM agent_memory_records "
        "WHERE agent_id = :aid AND tier = 'core' "
        "ORDER BY importance DESC, created_at DESC"
    ), {"aid": CLAUDE_AGENT_ID}).fetchall()

    return {
        "success": True,
        "data": {
            "core_memories": [
                {"memory_id": r.memory_id, "content": r.content,
                 "importance": r.importance, "created_at": r.created_at}
                for r in rows
            ],
            "count": len(rows),
        },
    }


# ── Store: save decisions during session ─────────────────────────────────────

@router.post("/store")
def store_memory(
    req: StoreRequest,
    db: Session = Depends(get_db),
):
    """Store a key decision or insight from the current Claude session.

    Use tier='core' for important long-term insights.
    Use tier='episodic' for session-specific details.
    """
    import uuid

    # Generate embedding if possible
    embedding_str = None
    try:
        import os
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=req.content[:2000],
        )
        embedding_str = json.dumps(result.embeddings[0].values)
    except Exception:
        pass

    memory_id = f"claude_{uuid.uuid4().hex[:12]}"

    db.execute(text(
        "INSERT INTO agent_memory_records "
        "(memory_id, agent_id, content, tier, importance, embedding, metadata_json, created_at, last_accessed, access_count) "
        "VALUES (:mid, :aid, :content, :tier, :imp, :emb, :meta, NOW(), NOW(), 0)"
    ), {
        "mid": memory_id,
        "aid": CLAUDE_AGENT_ID,
        "content": req.content[:5000],
        "tier": req.tier,
        "imp": req.importance,
        "emb": embedding_str,
        "meta": json.dumps(req.metadata or {"source": "claude_session"}),
    })
    db.commit()

    logger.info("claude_bridge: stored %s (tier=%s, imp=%.1f)", memory_id, req.tier, req.importance)

    return {
        "success": True,
        "data": {"memory_id": memory_id, "tier": req.tier},
    }


# ── Reflect: consolidate episodic → core ─────────────────────────────────────

@router.post("/reflect")
def trigger_reflection(db: Session = Depends(get_db)):
    """Trigger memory reflection — consolidate recent episodic memories into core insights.

    Uses LLM to identify patterns and produce high-level summaries.
    """
    # Get recent episodic memories
    rows = db.execute(text(
        "SELECT content FROM agent_memory_records "
        "WHERE agent_id = :aid AND tier = 'episodic' "
        "ORDER BY created_at DESC LIMIT 20"
    ), {"aid": CLAUDE_AGENT_ID}).fetchall()

    if not rows:
        return {"success": True, "data": {"message": "No episodic memories to reflect on"}}

    combined = "\n".join(f"- {r.content[:200]}" for r in rows)

    try:
        from agent_engine.llm.client import get_llm_client
        client = get_llm_client()
        reflection = client.chat(
            f"Reflect on these recent experiences and extract 3-5 key insights:\n\n{combined}",
            "You are reflecting on your work. Be concise. Focus on actionable patterns and lessons learned.",
            512,
            0.3,
        )

        # Store as core memory
        import uuid
        memory_id = f"reflect_{uuid.uuid4().hex[:8]}"
        db.execute(text(
            "INSERT INTO agent_memory_records "
            "(memory_id, agent_id, content, tier, importance, metadata_json, created_at, last_accessed, access_count) "
            "VALUES (:mid, :aid, :content, 'core', 0.8, :meta, NOW(), NOW(), 0)"
        ), {
            "mid": memory_id,
            "aid": CLAUDE_AGENT_ID,
            "content": f"[SESSION REFLECTION] {reflection[:3000]}",
            "meta": json.dumps({"type": "session_reflection", "episodic_count": len(rows)}),
        })
        db.commit()

        return {
            "success": True,
            "data": {
                "memory_id": memory_id,
                "reflection": reflection[:500],
                "episodic_analyzed": len(rows),
            },
        }
    except Exception as e:
        return {"success": False, "error": str(e)[:200]}
