"""
分↔合 (Divide ↔ Unite) — Pair 4

Unified entry point for:
  - a2a_protocol (agent-to-agent task decomposition & aggregation)
  - task_router (intelligent task classification & agent matching)
  - meta_task_generator (anomaly → auto-generated improvement tasks)
  - agent_team (dynamic team assembly with role assignment)

Soul (nautilus-agent, no DB):
  orchestration/decompose.py (pure task decomposition logic)
  via soul_bridge

Body (platform PostgreSQL):
  A2A subtask creation, agent capability matching, team composition,
  meta-task generation from observatory anomalies
"""

# ═══════════════════════════════════════════════════════════════════════════
# SOUL — nautilus-agent orchestration (no DB, via soul_bridge)
# ═══════════════════════════════════════════════════════════════════════════

# Pure decomposition: nautilus_agent.core.orchestration.decompose
# decompose(), execute_parallel(), synthesize(), solve_complex()
# Used by daemons directly via nautilus_agent imports, not re-exported here.


# ═══════════════════════════════════════════════════════════════════════════
# BODY — Platform orchestration (PostgreSQL/Redis)
# ═══════════════════════════════════════════════════════════════════════════

# A2A Protocol (agent-to-agent coordination)
from services.a2a_protocol import (  # noqa: F401
    A2ACoordinator, A2AWorker,
    get_a2a_coordinator, get_a2a_worker,
)

# Task Router (classification + agent matching)
from services.task_router import (  # noqa: F401
    TaskRouter, TaskComplexity, TaskClassification, RoutingDecision,
)

# Meta-Task Generator (anomaly → tasks)
from services.meta_task_generator import (  # noqa: F401
    process_anomalies, generate_meta_tasks_from_anomalies,
)

# Agent Team (dynamic team assembly)
from services.agent_team import (  # noqa: F401
    AgentTeamService, AgentRole, TeamResult,
)
