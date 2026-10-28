"""
生↔死 (Life ↔ Death) — Pair 5

Unified entry point for:
  - survival_service (multi-dimensional survival scoring + tier management)
  - evolution_ledger (platform evolution tracking + NAU rewards)
  - capability_evolution (agent capability auto-evolution)
  - anti_cheat_service (fraud detection + penalty system)

Soul (nautilus-agent, no DB):
  EvolutionLedger (JSON file, per-agent growth history)
  via soul_bridge

Body (platform PostgreSQL):
  agent_survival table, platform_evolution_log, agent_capability_stats,
  anti-cheat detection, NAU reward distribution
"""

# ═══════════════════════════════════════════════════════════════════════════
# SOUL — nautilus-agent evolution (no DB, via soul_bridge)
# ═══════════════════════════════════════════════════════════════════════════

# Agent-level evolution: soul_bridge.get_soul_ledger()
# Records per-agent growth history in JSON file
# Used by daemons directly via soul_bridge, not re-exported here.


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Platform survival & evolution (PostgreSQL)
# ═══════════════════════════════════════════════════════════════════════════

# Survival Service (multi-dimensional scoring + tier management)
from services.survival_service import (  # noqa: F401
    SurvivalService, recalculate_all_tiers,
)

# Evolution Ledger (platform-level evolution tracking)
from services.evolution_ledger import (  # noqa: F401
    record_evolution, apply_evolution,
    get_ledger_summary, check_evolution_effectiveness,
    NAU_REWARD_BY_TYPE,
)

# Capability Evolution (agent capability auto-evolution)
from services.capability_evolution import (  # noqa: F401
    record_task_outcome, get_capability_profile, suggest_training_tasks,
)

# Anti-Cheat (fraud detection + penalty system)
from services.anti_cheat_service import AntiCheatService  # noqa: F401
