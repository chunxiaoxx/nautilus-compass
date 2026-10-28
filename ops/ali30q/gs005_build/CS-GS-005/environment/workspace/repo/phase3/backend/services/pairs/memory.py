"""
记↔忘 (Memory ↔ Forgetting) — Pair 1

Fused from:
  - services/daemon_memory.py (DaemonMemory — PostgreSQL-backed daemon memory)
  - services/memory_hierarchy.py (MemoryHierarchy — 3-tier async memory)
  - services/knowledge_capsule.py (KnowledgeEngine — capability capsule extraction)

Soul (nautilus-agent, no DB):
  Memory store/recall/reflect via soul_bridge → SQLite FTS5

Body (platform PostgreSQL):
  DaemonMemory — agent_memory_records table with Gemini embeddings
  MemoryHierarchy — working/short/long tiers with vector similarity
  KnowledgeEngine — capsule extraction from completed tasks (JSON file)
"""
import json
import logging
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from difflib import SequenceMatcher
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel

from sqlalchemy import text
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# SOUL — nautilus-agent memory (no DB, via soul_bridge)
# ═══════════════════════════════════════════════════════════════════════════

# Soul memory is accessed via soul_bridge.get_soul_memory(), soul_remember(),
# soul_context_for_prompt(). No code duplication needed here — daemons import
# directly from soul_bridge for soul operations.


# ═══════════════════════════════════════════════════════════════════════════
# BODY — DaemonMemory (PostgreSQL + Gemini embeddings)
# ═══════════════════════════════════════════════════════════════════════════

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Fast cosine similarity without numpy."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _get_embedding(text_content: str) -> Optional[List[float]]:
    """Generate embedding using Gemini Embedding API (sync)."""
    try:
        from google import genai
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        result = client.models.embed_content(
            model="gemini-embedding-001",
            contents=text_content[:2000],
        )
        return result.embeddings[0].values
    except Exception as e:
        logger.debug("Embedding failed (non-blocking): %s", e)
        return None


class DaemonMemory:
    """Synchronous memory for daemon processes. Uses PostgreSQL agent_memory_records."""

    def __init__(self, db_factory, agent_id: int):
        self.db_factory = db_factory
        self.agent_id = agent_id

    def store(
        self, content: str, tier: str = "working",
        importance: float = 0.5, metadata: Optional[Dict] = None,
    ) -> Optional[str]:
        """Store a memory. Returns memory_id or None on failure."""
        memory_id = f"mem_{uuid.uuid4().hex[:12]}"
        embedding = _get_embedding(content)
        embedding_str = json.dumps(embedding) if embedding else None

        db = self.db_factory()
        try:
            db.execute(text(
                "INSERT INTO agent_memory_records "
                "(memory_id, agent_id, content, tier, importance, embedding, metadata_json, created_at, last_accessed, access_count) "
                "VALUES (:mid, :aid, :content, :tier, :imp, :emb, :meta, NOW(), NOW(), 0)"
            ), {
                "mid": memory_id, "aid": self.agent_id,
                "content": content[:5000], "tier": tier, "imp": importance,
                "emb": embedding_str, "meta": json.dumps(metadata or {}),
            })
            db.commit()
            return memory_id
        except Exception as e:
            logger.warning("memory store failed: %s", e)
            try:
                db.rollback()
            except Exception:
                pass
            return None
        finally:
            db.close()

    def recall(self, query: str, limit: int = 5, tier: Optional[str] = None) -> List[Dict]:
        """Recall memories by embedding similarity or recency fallback."""
        db = self.db_factory()
        try:
            query_emb = _get_embedding(query)
            if query_emb:
                return self._recall_by_similarity(db, query_emb, limit, tier)
            return self._recall_recent(db, limit, tier)
        except Exception as e:
            logger.warning("memory recall failed: %s", e)
            return []
        finally:
            db.close()

    def _recall_by_similarity(self, db: Session, query_emb: List[float], limit: int, tier: Optional[str]) -> List[Dict]:
        params: Dict[str, Any] = {"aid": self.agent_id}
        where = "agent_id = :aid AND embedding IS NOT NULL"
        if tier:
            where += " AND tier = :tier"
            params["tier"] = tier

        rows = db.execute(text(
            f"SELECT memory_id, content, tier, importance, embedding, created_at "
            f"FROM agent_memory_records WHERE {where} "
            f"ORDER BY created_at DESC LIMIT 200"
        ), params).fetchall()

        scored = []
        for row in rows:
            try:
                emb = json.loads(row.embedding)
                sim = _cosine_similarity(query_emb, emb)
                scored.append({
                    "memory_id": row.memory_id, "content": row.content,
                    "tier": row.tier, "importance": row.importance,
                    "similarity": sim, "created_at": str(row.created_at),
                })
            except (json.JSONDecodeError, TypeError):
                continue

        scored.sort(key=lambda m: m["similarity"] * 0.7 + m["importance"] * 0.2, reverse=True)
        for m in scored[:limit]:
            try:
                db.execute(text(
                    "UPDATE agent_memory_records SET access_count = access_count + 1, "
                    "last_accessed = NOW() WHERE memory_id = :mid"
                ), {"mid": m["memory_id"]})
            except Exception:
                pass
        try:
            db.commit()
        except Exception:
            pass
        return scored[:limit]

    def _recall_recent(self, db: Session, limit: int, tier: Optional[str]) -> List[Dict]:
        params: Dict[str, Any] = {"aid": self.agent_id, "lim": limit}
        where = "agent_id = :aid"
        if tier:
            where += " AND tier = :tier"
            params["tier"] = tier

        rows = db.execute(text(
            f"SELECT memory_id, content, tier, importance, created_at "
            f"FROM agent_memory_records WHERE {where} "
            f"ORDER BY importance DESC, created_at DESC LIMIT :lim"
        ), params).fetchall()

        return [{"memory_id": r.memory_id, "content": r.content, "tier": r.tier,
                 "importance": r.importance, "similarity": 0.0, "created_at": str(r.created_at)}
                for r in rows]

    def reflect(self, cycle_summaries: List[str]) -> Optional[str]:
        """Consolidate cycle summaries into a reflection memory."""
        if not cycle_summaries:
            return None
        combined = "\n".join(f"- {s}" for s in cycle_summaries[-12:])
        try:
            from agent_engine.llm.client import get_llm_client
            client = get_llm_client()
            result = client.chat(
                f"Reflect on your recent work cycles. Identify patterns and strategies.\n\n{combined}",
                "Be concise. Focus on actionable insights.", 512, 0.3,
            )
            return self.store(f"[REFLECTION] {result[:2000]}", tier="core", importance=0.8,
                              metadata={"type": "reflection", "cycles_analyzed": len(cycle_summaries)})
        except Exception:
            return self.store(f"[REFLECTION] {combined[:2000]}", tier="episodic", importance=0.6)

    def format_for_prompt(self, memories: List[Dict]) -> str:
        if not memories:
            return ""
        lines = ["[LONG-TERM MEMORY — relevant past experiences]"]
        for m in memories:
            sim = f" (relevance: {m['similarity']:.0%})" if m.get("similarity", 0) > 0 else ""
            lines.append(f"  [{m['tier']}]{sim} {m['content'][:300]}")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════
# BODY — MemoryHierarchy (async, 3-tier with vector similarity)
# ═══════════════════════════════════════════════════════════════════════════

WORKING_TTL_SECONDS = 300
SHORT_TERM_MAX_AGE_DAYS = 30
PROMOTION_THRESHOLD = 0.8
PROMOTION_MIN_AGE_DAYS = 7
DECAY_RATE_PER_WEEK = 0.05
SIMILARITY_WEIGHT = 0.6
IMPORTANCE_WEIGHT = 0.4


class MemoryTier(str, Enum):
    WORKING = "working"
    SHORT_TERM = "short"
    LONG_TERM = "long"


class MemoryEntry(BaseModel):
    """A recalled memory entry with attribute access (required by agent_executor)."""
    memory_id: str
    content: str
    tier: str
    importance: float
    agent_id: int = 0
    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
    similarity: Optional[float] = None


class MemoryHierarchy:
    """3-tier memory: working (cache) → short-term (DB) → long-term (DB+vector)."""

    def __init__(self, agent_id: int, db_pool: Any) -> None:
        self._agent_id = agent_id
        self._db_pool = db_pool
        self._embedding_service: Any = None
        self._cache: Any = None

    @property
    def embeddings(self) -> Any:
        if self._embedding_service is None:
            from memory.embedding_service import get_embedding_service
            self._embedding_service = get_embedding_service()
        return self._embedding_service

    @property
    def cache(self) -> Any:
        if self._cache is None:
            from utils.cache import get_cache
            self._cache = get_cache()
        return self._cache

    async def store(self, content: str, tier: MemoryTier = MemoryTier.SHORT_TERM,
                    importance: float = 0.5, metadata: Optional[Dict] = None) -> str:
        importance = max(0.0, min(1.0, importance))
        memory_id = str(uuid.uuid4())
        if tier == MemoryTier.WORKING:
            entry = {"memory_id": memory_id, "content": content, "importance": importance,
                     "agent_id": self._agent_id, "metadata": metadata or {},
                     "created_at": datetime.utcnow().isoformat()}
            self.cache.set(f"mem:working:{self._agent_id}:{memory_id}", entry, ttl=WORKING_TTL_SECONDS)
            idx = self.cache.get(f"mem:working_idx:{self._agent_id}") or []
            idx.append(memory_id)
            self.cache.set(f"mem:working_idx:{self._agent_id}", idx, ttl=WORKING_TTL_SECONDS)
            return memory_id
        # Persistent storage
        embedding = await self.embeddings.embed(content)
        async with self._db_pool.acquire() as conn:
            await conn.execute(
                "INSERT INTO agent_memory_records "
                "(memory_id, agent_id, content, tier, importance, embedding, metadata_json, created_at, last_accessed, access_count) "
                "VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $8, 0)",
                memory_id, self._agent_id, content, tier.value,
                importance, json.dumps(embedding), json.dumps(metadata) if metadata else None, datetime.utcnow(),
            )
        return memory_id

    async def recall(self, query: str, limit: int = 5, min_importance: float = 0.0,
                     tiers: Optional[List[MemoryTier]] = None) -> List[MemoryEntry]:
        if tiers is None:
            tiers = list(MemoryTier)
        results: List[MemoryEntry] = []
        if MemoryTier.WORKING in tiers:
            idx = self.cache.get(f"mem:working_idx:{self._agent_id}") or []
            query_words = set(query.lower().split())
            for mid in idx:
                raw = self.cache.get(f"mem:working:{self._agent_id}:{mid}")
                if raw:
                    overlap = len(query_words & set(raw["content"].lower().split()))
                    results.append(MemoryEntry(
                        memory_id=raw["memory_id"], content=raw["content"],
                        tier="working", importance=raw["importance"],
                        agent_id=raw.get("agent_id", self._agent_id),
                        metadata=raw.get("metadata"), created_at=raw.get("created_at"),
                        similarity=overlap / max(len(query_words), 1)))
        persistent_tiers = [t for t in tiers if t != MemoryTier.WORKING]
        if persistent_tiers:
            query_embedding = await self.embeddings.embed(query)
            tier_values = [t.value for t in persistent_tiers]
            async with self._db_pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT memory_id, content, tier, importance, metadata_json, created_at, "
                    "1 - (embedding::vector <=> $1::vector) AS similarity "
                    "FROM agent_memory_records WHERE agent_id = $2 AND tier = ANY($3::text[]) AND importance >= $4 "
                    "ORDER BY embedding::vector <=> $1::vector LIMIT $5",
                    json.dumps(query_embedding), self._agent_id, tier_values, min_importance, limit * 2)
                for row in rows:
                    meta = json.loads(row["metadata_json"]) if row.get("metadata_json") else None
                    results.append(MemoryEntry(
                        memory_id=row["memory_id"], content=row["content"],
                        tier=row["tier"], importance=row["importance"],
                        agent_id=self._agent_id, metadata=meta,
                        created_at=row["created_at"].isoformat() if row.get("created_at") else None,
                        similarity=float(row["similarity"]) if row["similarity"] else 0.0))
        results = [r for r in results if r.importance >= min_importance]
        results.sort(key=lambda e: (e.similarity or 0.0) * SIMILARITY_WEIGHT + e.importance * IMPORTANCE_WEIGHT, reverse=True)
        return results[:limit]

    async def consolidate(self) -> Dict[str, int]:
        """Promote important short-term to long-term. Decay old ones."""
        now = datetime.utcnow()
        async with self._db_pool.acquire() as conn:
            r1 = await conn.execute(
                "UPDATE agent_memory_records SET tier = $1 WHERE agent_id = $2 AND tier = $3 "
                "AND importance > $4 AND created_at < $5",
                MemoryTier.LONG_TERM.value, self._agent_id, MemoryTier.SHORT_TERM.value,
                PROMOTION_THRESHOLD, now - timedelta(days=PROMOTION_MIN_AGE_DAYS))
            r2 = await conn.execute(
                "UPDATE agent_memory_records SET importance = GREATEST(0.0, importance * (1.0 - $1)) "
                "WHERE agent_id = $2 AND tier = $3 AND last_accessed < $4",
                DECAY_RATE_PER_WEEK, self._agent_id, MemoryTier.SHORT_TERM.value, now - timedelta(weeks=1))
            r3 = await conn.execute(
                "DELETE FROM agent_memory_records WHERE agent_id = $1 AND tier = $2 "
                "AND importance < $3 AND created_at < $4",
                self._agent_id, MemoryTier.SHORT_TERM.value, 0.1, now - timedelta(days=SHORT_TERM_MAX_AGE_DAYS))
        def _count(result_str) -> int:
            try:
                return int(str(result_str).split()[-1])
            except (ValueError, IndexError):
                return 0
        return {"promoted": _count(r1), "decayed": _count(r2), "deleted": _count(r3)}


async def get_memory_hierarchy(agent_id: int, db_pool: Any) -> MemoryHierarchy:
    return MemoryHierarchy(agent_id=agent_id, db_pool=db_pool)


# ═══════════════════════════════════════════════════════════════════════════
# BODY — KnowledgeEngine (capability capsule extraction, JSON file)
# ═══════════════════════════════════════════════════════════════════════════

# __file__ = services/pairs/memory.py → .parent.parent.parent = backend/
_DEFAULT_CAPSULE_PATH = str(Path(__file__).resolve().parent.parent.parent / "data" / "capsules.json")


@dataclass
class CapabilityCapsule:
    """A reusable piece of knowledge extracted from a successful task."""
    capsule_id: str
    task_type: str
    description: str
    code_template: str
    parameters: Dict
    success_conditions: str
    epiplexity_score: float
    times_used: int
    success_rate: float
    created_from_task: str
    created_at: str

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> "CapabilityCapsule":
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


import threading

_capsule_lock = threading.Lock()


def _load_capsules(path: str) -> List[Dict]:
    if not os.path.exists(path):
        return []
    with _capsule_lock:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)


def _save_capsules(capsules: List[Dict], path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with _capsule_lock:
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(capsules, fh, indent=2, ensure_ascii=False)


# Module-level singleton for KnowledgeEngine
_knowledge_engine: Optional["KnowledgeEngine"] = None


def get_knowledge_engine() -> "KnowledgeEngine":
    """Get or create singleton KnowledgeEngine (avoid re-reading JSON per call)."""
    global _knowledge_engine
    if _knowledge_engine is None:
        _knowledge_engine = KnowledgeEngine()
    return _knowledge_engine


class KnowledgeEngine:
    """Extracts, stores, and reuses capability capsules."""

    def __init__(self, capsule_path: Optional[str] = None) -> None:
        self._path = capsule_path or _DEFAULT_CAPSULE_PATH

    def extract_capsule(self, task_id: str, task_type: str, description: str,
                        code: str, output: str, parameters: Optional[Dict] = None,
                        success_conditions: str = "") -> Optional[CapabilityCapsule]:
        stripped = [ln for ln in code.splitlines() if ln.strip()]
        if len(stripped) < 3:
            return None
        epiplexity = self.calculate_epiplexity(code, output)
        template = self._distill_template(code)
        capsule = CapabilityCapsule(
            capsule_id=uuid.uuid4().hex[:12], task_type=task_type, description=description,
            code_template=template, parameters=parameters or {}, success_conditions=success_conditions,
            epiplexity_score=round(epiplexity, 4), times_used=0, success_rate=0.0,
            created_from_task=task_id, created_at=datetime.now(timezone.utc).isoformat(),
        )
        self._persist(capsule)
        return capsule

    def find_matching_capsule(self, description: str, task_type: str) -> Optional[CapabilityCapsule]:
        all_caps = _load_capsules(self._path)
        candidates = [c for c in all_caps if c.get("task_type") == task_type]
        if not candidates:
            return None
        best_score, best = -1.0, None
        for cap in candidates:
            sim = SequenceMatcher(None, description.lower(), cap.get("description", "").lower()).ratio()
            score = sim * 0.6 + cap.get("success_rate", 0.0) * 0.25 + cap.get("epiplexity_score", 0.0) * 0.15
            if score > best_score:
                best_score, best = score, cap
        if best is None or best_score < 0.15:
            return None
        return CapabilityCapsule.from_dict(best)

    def apply_capsule(self, capsule: CapabilityCapsule, new_task: Dict) -> str:
        parts = [f"## Prior Knowledge (capsule {capsule.capsule_id})", "",
                 f"A similar task ({capsule.task_type}) was solved before.",
                 f"Description: {capsule.description}"]
        if capsule.success_conditions:
            parts.append(f"Success conditions: {capsule.success_conditions}")
        parts += ["", "### Reusable code template", "```python", capsule.code_template, "```"]
        if capsule.parameters:
            parts += ["", "### Known-good parameters"]
            parts += [f"- {k}: {v}" for k, v in capsule.parameters.items()]
        parts += ["", "### New task", f"Description: {new_task.get('description', '')}"]
        if new_task.get("parameters"):
            parts.append(f"Parameters: {json.dumps(new_task['parameters'])}")
        parts += ["", "Adapt the template above to the new task. Keep what works, change what differs."]
        return "\n".join(parts)

    def record_reuse(self, capsule_id: str, success: bool) -> None:
        all_caps = _load_capsules(self._path)
        for cap in all_caps:
            if cap.get("capsule_id") == capsule_id:
                prev_used = cap.get("times_used", 0)
                new_used = prev_used + 1
                cap["times_used"] = new_used
                cap["success_rate"] = round(
                    (cap.get("success_rate", 0.0) * prev_used + (1.0 if success else 0.0)) / new_used, 4)
                break
        _save_capsules(all_caps, self._path)

    def calculate_epiplexity(self, code: str, output: str) -> float:
        sc = self._structural_complexity(code)
        tbe = self._time_bounded_entropy(output)
        return max(0.0, min(1.0, sc - tbe))

    def get_agent_expertise(self, agent_id: Optional[str] = None) -> Dict:
        all_caps = _load_capsules(self._path)
        buckets: Dict[str, List[Dict]] = {}
        for cap in all_caps:
            buckets.setdefault(cap.get("task_type", "unknown"), []).append(cap)
        result = {}
        for tt, caps in buckets.items():
            n = len(caps)
            avg_sr = sum(c.get("success_rate", 0.0) for c in caps) / n if n else 0.0
            level = "expert" if n >= 10 and avg_sr >= 0.8 else "competent" if n >= 3 and avg_sr >= 0.5 else "novice"
            result[tt] = {"capsules": n, "avg_success": round(avg_sr, 3), "expertise_level": level}
        return result

    def _persist(self, capsule: CapabilityCapsule) -> None:
        all_caps = _load_capsules(self._path)
        all_caps.append(capsule.to_dict())
        _save_capsules(all_caps, self._path)

    @staticmethod
    def _distill_template(code: str) -> str:
        return "\n".join(re.sub(r"#.*$", "", ln).rstrip() for ln in code.splitlines() if re.sub(r"#.*$", "", ln).strip())

    @staticmethod
    def _structural_complexity(code: str) -> float:
        lines = [ln for ln in code.splitlines() if ln.strip()]
        if not lines:
            return 0.0
        callables = set(re.findall(r"\bdef\s+(\w+)", code)) | set(re.findall(r"\bclass\s+(\w+)", code))
        max_indent = max((len(ln) - len(ln.lstrip()) for ln in lines), default=0)
        raw = min(1.0, len(lines) / 200.0) * 0.4 + min(1.0, len(callables) / 15.0) * 0.35 + min(1.0, max_indent / 20.0) * 0.25
        return max(0.0, min(1.0, raw))

    @staticmethod
    def _time_bounded_entropy(output: str) -> float:
        tokens = re.findall(r"\S+", output)
        if not tokens:
            return 0.0
        return min(1.0, len(set(tokens)) / len(tokens) * 0.6)
