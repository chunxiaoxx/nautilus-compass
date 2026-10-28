"""
Rehoboam — Thin compatibility wrapper.

All logic has moved to services.agent_executor.  This module re-exports the
public API so that existing callers (dashboard.py, academic_tasks.py,
telegram_bot.py, wechat_bot.py, scheduler.py, etc.) continue to work unchanged.
"""
from services.agent_executor import (          # noqa: F401  — re-exports
    AgentExecutor,
    AgentProfile,
    AgentRegistry,
    AgentRuntime,
    BrainResult,
    CustomerProfile,
    Message,
    OrderInfo,
    ParsedAction,
    build_system_prompt,
    get_executor,
    get_runtime,
    parse_actions,
    process_message,
)

# ---------------------------------------------------------------------------
# Backward-compatible aliases
# ---------------------------------------------------------------------------

# Many callers do: from services.rehoboam import get_rehoboam
# get_rehoboam() returns an object with .registry, .get_client(),
# .verify_task_result(), .autonomous_check(), .process_message().
# AgentExecutor has all of these.

Rehoboam = AgentExecutor  # type alias
get_rehoboam = get_executor
