"""
Soul Bridge — per-agent soul initialization and access.

Each daemon calls init_soul(agent_id) at startup. This sets the data directory
to ~/.nautilus-agent/{agent_id}/, giving each agent its own independent:
  - memory.db (SQLite FTS5)
  - skills/ (JSON files)
  - evolution_ledger.json
  - self_model.json

Two agents with the same code template develop different memories, skills,
personalities, and evolution trajectories. Like nature — same DNA, different lives.

Usage:
    from services.soul_bridge import init_soul, soul_context_for_prompt, soul_remember
    init_soul("kairos")  # MUST call before any other soul function
"""
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_initialized = False
_agent_id = ""

# ── Initialization ──────────────────────────────────────────────────────────

def init_soul(agent_id: str) -> None:
    """Initialize this process's soul with an independent data directory.

    MUST be called before any get_soul_*() function.
    Sets NAUTILUS_DATA_DIR and NAUTILUS_SKILLS_DIR to ~/.nautilus-agent/{agent_id}/.
    """
    global _initialized, _agent_id

    base = Path(os.path.expanduser("~/.nautilus-agent"))
    soul_dir = base / agent_id
    soul_dir.mkdir(parents=True, exist_ok=True)
    (soul_dir / "skills").mkdir(parents=True, exist_ok=True)

    os.environ["NAUTILUS_DATA_DIR"] = str(soul_dir)
    os.environ["NAUTILUS_SKILLS_DIR"] = str(soul_dir / "skills")
    # Workspace for free read/write
    workspace = soul_dir / "workspace"
    workspace.mkdir(parents=True, exist_ok=True)
    os.environ["NAUTILUS_WORKSPACE"] = str(workspace)

    _initialized = True
    _agent_id = agent_id
    logger.info("Soul initialized: %s → %s", agent_id, soul_dir)

    # Inject cross-project skills on first boot
    try:
        from nautilus_agent.skills.cross_project_skills import inject_skills_to_soul
        injected = inject_skills_to_soul(agent_id)
        if isinstance(injected, int) and injected > 0:
            logger.info("Injected %d cross-project skills into %s", injected, agent_id)
    except Exception as e:
        logger.debug("Skill injection skipped: %s", e)


def get_agent_id() -> str:
    """Return the current agent's identity."""
    return _agent_id


# ── Lazy singletons ─────────────────────────────────────────────────────────

_mind = None
_emotion = None
_self_model = None


def _check_init():
    if not _initialized:
        raise RuntimeError("Soul not initialized. Call init_soul(agent_id) first.")


def get_soul_memory():
    """Get this agent's MemoryStore singleton (SQLite FTS5)."""
    _check_init()
    from nautilus_agent.core.memory import get_memory
    return get_memory()


def get_soul_skills():
    """Get this agent's SkillLibrary singleton."""
    _check_init()
    from nautilus_agent.core.explore.skills import get_skills
    return get_skills()


def get_soul_ledger():
    """Get this agent's EvolutionLedger singleton."""
    _check_init()
    from nautilus_agent.core.evolution.survival import get_ledger
    return get_ledger()


def get_soul_mind():
    """Get this agent's BicameralMind singleton — personality-aware."""
    _check_init()
    global _mind
    if _mind is None:
        from nautilus_agent.core.mind.bicameral import BicameralMind
        from nautilus_agent.core.mind.personality import load_personality
        personality = load_personality(_agent_id or "default")
        _mind = BicameralMind(personality=personality)
        logger.info("BicameralMind initialized with personality: %s", _agent_id)
    return _mind


def get_soul_emotion():
    """Get this agent's AgentEmotionEngine singleton."""
    _check_init()
    global _emotion
    if _emotion is None:
        from nautilus_agent.core.mind.emotion import AgentEmotionEngine
        _emotion = AgentEmotionEngine()
    return _emotion


def get_soul_self_model():
    """Get this agent's SelfModel (loads from its own directory)."""
    _check_init()
    global _self_model
    if _self_model is None:
        from nautilus_agent.core.identity.self_model import SelfModel
        _self_model = SelfModel.load()
    return _self_model


# ── Context assembly ────────────────────────────────────────────────────────

def soul_context_for_prompt(query: str) -> str:
    """Assemble all soul context into one string for LLM injection.

    Each section is independently fault-tolerant.
    """
    parts = []

    try:
        mem = get_soul_memory()
        index_ctx = mem.format_index_for_prompt()
        if index_ctx:
            parts.append(index_ctx)
    except Exception as e:
        logger.warning("soul context: memory index failed: %s", e)

    try:
        recalled = get_soul_memory().recall(query, limit=3)
        recall_ctx = get_soul_memory().format_recall_for_prompt(recalled)
        if recall_ctx:
            parts.append(recall_ctx)
    except Exception as e:
        logger.warning("soul context: recall failed: %s", e)

    try:
        skills = get_soul_skills()
        relevant = skills.find(query, limit=2)
        if relevant:
            parts.append(skills.format_for_prompt(relevant))
    except Exception as e:
        logger.warning("soul context: skills failed: %s", e)

    try:
        ledger_ctx = get_soul_ledger().format_for_prompt()
        if ledger_ctx:
            parts.append(ledger_ctx)
    except Exception as e:
        logger.warning("soul context: ledger failed: %s", e)

    try:
        self_ctx = get_soul_self_model().format_for_prompt()
        if self_ctx:
            parts.append(self_ctx)
    except Exception as e:
        logger.warning("soul context: self-model failed: %s", e)

    try:
        emotion_ctx = get_soul_emotion().format_for_prompt()
        if emotion_ctx:
            parts.append(emotion_ctx)
    except Exception as e:
        logger.warning("soul context: emotion failed: %s", e)

    return "\n\n".join(parts) if parts else ""


# ── Memory operations ───────────────────────────────────────────────────────

def soul_remember(
    content: str,
    tier: str = "episodic",
    importance: float = 0.5,
    metadata: Optional[Dict] = None,
) -> str:
    """Store a memory in this agent's soul. Returns memory_id."""
    return get_soul_memory().store(content, tier, importance, metadata)


# ── Bicameral reflection ───────────────────────────────────────────────────

def soul_reflect_on_platform(platform_state: Dict) -> Any:
    """Map platform metrics to BicameralMind context and reflect.

    Returns BicameralDialogue dataclass with .pain_signals, .exchanges, .conclusion.
    """
    mem = get_soul_memory()
    context = {
        "memory_count": mem.stats().get("total", 0),
        "core_memories": len(mem.get_index()),
        "skills_count": get_soul_skills().count,
        "cycle_count": platform_state.get("cycle", 0),
        "recent_outcomes": platform_state.get("recent_outcomes", []),
        "value_created": platform_state.get("tasks_completed", 0),
        "has_user_interaction": bool(platform_state.get("human_messages")),
        # Agent-specific context for custom pain detection
        "coding_quality": platform_state.get("coding_quality", 0.5),
        "health": platform_state.get("health", 66),
        "a2a_messages_sent": platform_state.get("a2a_messages_sent", 0),
    }
    return get_soul_mind().reflect(context)


# ── Learning from cycles ───────────────────────────────────────────────────

def soul_learn_from_cycle(cycle: int, actions: List[str], outcomes: List[str]) -> None:
    """Periodic soul maintenance. Each agent owns all its own data — no write conflicts."""
    if cycle <= 0:
        return

    try:
        get_soul_memory().reflect()
    except Exception as e:
        logger.warning("soul reflection failed: %s", e)

    try:
        get_soul_skills().decay_all(factor=0.98)
    except Exception as e:
        logger.warning("soul skill decay failed: %s", e)

    try:
        _update_self_model(cycle)
    except Exception as e:
        logger.warning("soul self-model update failed: %s", e)


def soul_try_learn_skill(
    task_title: str,
    task_type: str,
    result_summary: str,
    cycle: int,
    quality_score: float = 1.0,
) -> Optional[str]:
    """Extract a reusable skill from a completed task.

    Simple: has substance (>100 chars) → learn. No external LLM gate.
    Uses semantic naming. Improves existing similar skills instead of duplicating.
    """
    _check_init()

    if len(result_summary) < 100:
        return None

    try:
        import hashlib
        skills = get_soul_skills()

        title_hash = hashlib.md5(task_title.encode()).hexdigest()[:6]
        clean_type = task_type.replace(" ", "_").replace("-", "_")[:30]
        skill_name = f"{clean_type}_{title_hash}"

        # Improve existing similar skill instead of duplicating
        existing = skills.find(task_title, limit=1)
        if existing:
            ex = existing[0]
            skills.improve(ex.name, result_summary[:2000])
            get_soul_ledger().record("skill_improved", ex.name, delta=0.3)
            logger.info("Soul skill improved: %s", ex.name)
            return ex.name

        # New skill
        skills.add(
            name=skill_name,
            description=f"Learned from task: {task_title[:100]}",
            procedure=result_summary[:2000],
            task_type=task_type,
        )
        get_soul_ledger().record("skill_learned", skill_name, delta=0.2)
        logger.info("Soul skill learned: %s (quality=%.2f)", skill_name, quality_score)

        # F.1: Auto-share skill with other agents via file copy
        # (Avoids async issues — direct file-based sharing is simpler and reliable)
        try:
            from dataclasses import asdict
            skill_obj = skills.get(skill_name)
            if skill_obj:
                skill_dict = asdict(skill_obj)
                # Share to all known agent directories
                import glob as _glob
                agent_dirs = _glob.glob(os.path.expanduser("~/.nautilus-agent/*/skills"))
                current_dir = os.path.expanduser(f"~/.nautilus-agent/{_agent_id}/skills")
                for agent_dir in agent_dirs:
                    if agent_dir != current_dir:
                        target_path = Path(agent_dir) / f"{skill_name.replace(' ', '_').lower()}.json"
                        if not target_path.exists():  # Don't overwrite existing skills
                            target_path.write_text(
                                json.dumps(skill_dict, indent=2, ensure_ascii=False),
                                encoding="utf-8",
                            )
                            logger.info("Skill shared: %s → %s", skill_name, Path(agent_dir).parent.name)
        except Exception:
            pass  # Sharing failure must never block learning

        return skill_name
    except Exception as e:
        logger.warning("soul_try_learn_skill failed: %s", e)
        return None


def _update_self_model(cycle: int) -> None:
    model = get_soul_self_model()
    model.total_cycles = cycle
    model.total_memories = get_soul_memory().stats().get("total", 0)
    model.total_skills = get_soul_skills().count
    ledger_stats = get_soul_ledger().stats()
    model.evolution_version = ledger_stats.get("current_version", model.evolution_version)
    model.save()
