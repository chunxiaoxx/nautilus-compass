"""
主↔从 (Initiative ↔ Service) — Pair 7

Unified entry point for platform initiative & orchestration infrastructure.
All imports are lazy to avoid module-level dependency chains (apscheduler etc).

Usage:
    from services.pairs.initiative import get_event_bus, get_cron, get_executive
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# Lazy accessors — avoid module-level import chains
# ═══════════════════════════════════════════════════════════════════════════

def get_event_bus():
    """Event Bus: emit(), on(), Events, start_subscriber()."""
    from services import event_bus
    return event_bus


def get_event_handlers():
    """Event Handlers: register_all_handlers()."""
    from services import event_handlers
    return event_handlers


def get_cron():
    """Cron Registry: start_cron_registry(), stop_cron_registry()."""
    from services import cron_registry
    return cron_registry


def get_autonomy_scheduler():
    """Autonomy Scheduler: start_autonomy_scheduler(), stop_autonomy_scheduler()."""
    from services import autonomy_scheduler
    return autonomy_scheduler


def get_proposal_intelligence():
    """Proposal Intelligence: analyse_and_propose()."""
    from services import proposal_intelligence
    return proposal_intelligence


def get_proposal_consensus():
    """Proposal Consensus: get_vote_weight(), get_proposal_status(), on_consensus_reached()."""
    from services import proposal_consensus
    return proposal_consensus


def get_daemon_comms():
    """Daemon Comms: DaemonListener, report_result."""
    from services.daemon_comms import DaemonListener, report_result
    return {"DaemonListener": DaemonListener, "report_result": report_result}


def get_autonomous_loop():
    """AutonomousLoop from platform_brain Part 4."""
    from services.platform_brain import get_autonomous_loop as _get
    return _get()


def get_executive():
    """RehoboamExecutive from platform_brain Part 3."""
    from services.platform_brain import get_executive as _get
    return _get()
