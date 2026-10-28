"""
探↔验 (Explore ↔ Verify) — Pair 3

Unified entry point for:
  - curiosity_engine (proactive exploration, hypothesis generation)
  - sandbox (A/B experiment framework)
  - sandbox_router (task tagging for experiments)
  - raid_engine (multi-level consensus verification)
  - raid_config (YAML-based RAID configuration)
  - raid_logger (execution logging for meta-harness)
  - checkpoint (durable execution state)
  - task_quality_gate (output quality validation)

Soul (nautilus-agent, no DB):
  RaidEngine (stateless consensus) + SkillLibrary (skill tracking)
  via soul_bridge

Body (platform PostgreSQL):
  RAID execution with checkpoint persistence, sandbox experiments,
  curiosity-driven exploration, quality scoring
"""

# ═══════════════════════════════════════════════════════════════════════════
# SOUL — nautilus-agent explore/verify (no DB, via soul_bridge)
# ═══════════════════════════════════════════════════════════════════════════

# Stateless RAID consensus: soul_bridge.get_soul_skills() for skill tracking
# nautilus_agent.core.consensus.raid.RaidEngine for in-memory consensus
# These are used by daemons directly via soul_bridge, not re-exported here.


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Platform exploration & verification (PostgreSQL/Redis)
# ═══════════════════════════════════════════════════════════════════════════

# RAID Engine (multi-level consensus with checkpoint persistence)
from services.raid_engine import (  # noqa: F401
    RaidEngine, RaidLevel, RaidResult, VoteInfo,
)

# RAID Configuration (YAML hot-reload)
from services.raid_config import (  # noqa: F401
    load_raid_config, get_raid_level_config, get_raid_level_for_task_type,
    get_complexity_raid_mapping, get_resource_governor_defaults, get_engine_params,
)

# RAID Logging (meta-harness optimization)
from services.raid_logger import log_raid_execution  # noqa: F401

# Checkpoint (durable execution state)
from services.checkpoint import (  # noqa: F401
    save_checkpoint, load_checkpoint, clear_checkpoint,
)

# Sandbox (A/B experiment framework)
from services.sandbox import (  # noqa: F401
    create_experiment, evaluate_experiment, finalize_experiment,
    assign_task_to_experiment, get_pending_evaluations,
)

# Sandbox Router (task tagging)
from services.sandbox_router import tag_task_for_experiment  # noqa: F401

# Curiosity Engine (proactive exploration)
from services.curiosity_engine import (  # noqa: F401
    explore_improvements, create_exploration_experiment, evolve_goals,
)

# Task Quality Gate (output validation)
from services.task_quality_gate import (  # noqa: F401
    score_task_output, interpret_quality,
)
