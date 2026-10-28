"""
Agent Brain — gives server daemons the full NautilusAgent cognitive cycle.

Hermes fusion: tool trace middleware + skill nudge mechanism.

Instead of custom decision logic, daemons use NautilusAgent.think() for
every interaction. The middleware intercepts tool calls to build a trace,
enabling:
  - Visible ReAct loop (tool_trace returned alongside response)
  - Explicit skill learning from tool execution sequences
  - Nudge-driven skill extraction (Hermes pattern)

Usage:
    from services.agent_brain import get_agent_brain, think_with_trace
    brain = get_agent_brain()
    response, trace = think_with_trace("Platform health is 64. What should I do?")
"""
import logging
import os
import time
from typing import List, Optional, Tuple

logger = logging.getLogger(__name__)

_brain: Optional["NautilusAgent"] = None
_tool_trace: List[dict] = []  # Accumulated tool calls for current think()
_cycles_since_skill_nudge = 0

SKILL_NUDGE_INTERVAL = 12  # Every 12 cycles, review for skill extraction


def _wrap_tool_registry(registry):
    """Monkey-patch ToolRegistry.run() to capture tool traces (Hermes pattern).

    Every tool call is logged with name, input, output, timing, and success.
    This makes the ReAct loop visible to the daemon.
    """
    original_run = registry.run

    def traced_run(name: str, input_text: str) -> str:
        start = time.time()
        result = original_run(name, input_text)
        elapsed = time.time() - start
        success = not any(k in result.lower() for k in ("error", "failed", "exception"))
        _tool_trace.append({
            "tool": name,
            "input": input_text[:200],
            "output": result[:500],
            "success": success,
            "elapsed_ms": int(elapsed * 1000),
        })
        return result

    registry.run = traced_run
    return registry


def get_agent_brain():
    """Get or create the daemon's NautilusAgent instance.

    Uses the soul already initialized by init_soul(agent_id).
    Registers daemon_tools as additional capabilities.
    Wraps tool registry for trace capture.
    """
    global _brain
    if _brain is not None:
        return _brain

    from nautilus_agent.agent import NautilusAgent

    # Determine personality from soul identity
    from services.soul_bridge import get_agent_id
    agent_id = get_agent_id()
    personality = "default"
    if agent_id == "kairos":
        personality = "kairos"
    elif agent_id == "minimax":
        personality = "minimax"

    # Create agent — it picks up the soul data dir already set by init_soul()
    _brain = NautilusAgent(personality_name=personality)

    # Register daemon-specific tools (platform access, A2A, multimodal)
    try:
        from services.daemon_tools import get_tools
        daemon_tools = get_tools()
        for name in daemon_tools.names:
            tool = daemon_tools.get(name)
            if tool and name not in _brain.tools.names:
                _brain.tools.register(tool)
        logger.info("Agent brain: %d tools (%d from daemon_tools)",
                     _brain.tools.count, len(daemon_tools.names))
    except Exception as e:
        logger.warning("Failed to register daemon tools: %s", e)

    # Wrap tool registry for trace capture (Hermes fusion)
    _wrap_tool_registry(_brain.tools)

    logger.info("Agent brain initialized for %s: %d memories, %d skills, %d tools (traced)",
                agent_id, _brain.memory.stats()["total"], _brain.skills.count, _brain.tools.count)
    return _brain


def think(input_text: str) -> str:
    """Run one complete cognitive cycle. Returns the agent's response.

    Backward-compatible: returns str only. Use think_with_trace() for full output.
    """
    response, _ = think_with_trace(input_text)
    return response


def think_with_trace(input_text: str) -> Tuple[str, List[dict]]:
    """Run one cognitive cycle. Returns (response, tool_trace).

    tool_trace is a list of dicts:
      [{"tool": "search", "input": "...", "output": "...", "success": true, "elapsed_ms": 123}, ...]

    This is the Hermes fusion: making the ReAct loop visible.
    """
    global _tool_trace, _cycles_since_skill_nudge
    _tool_trace = []  # Reset for this cycle

    brain = get_agent_brain()
    response = brain.think(input_text)

    trace = list(_tool_trace)  # Snapshot before reset
    _tool_trace = []

    _cycles_since_skill_nudge += 1

    return response, trace


def try_learn_skill_from_trace(
    trace: List[dict],
    task_title: str,
    cycle: int,
) -> Optional[str]:
    """Extract a reusable skill from tool execution trace (Hermes pattern).

    Unlike the old heuristic (_try_learn_skill which looked for "step/then/method"),
    this extracts the actual tool execution sequence as a procedure.
    """
    if not trace or len(trace) < 2:
        return None  # Need at least 2 tool calls to form a procedure

    # Check overall success
    successes = sum(1 for t in trace if t["success"])
    if successes < len(trace) * 0.5:
        return None  # Too many failures, not worth learning

    try:
        from services.soul_bridge import soul_try_learn_skill

        # Build procedure from tool trace (not from text!)
        steps = []
        for i, t in enumerate(trace):
            status = "OK" if t["success"] else "FAILED"
            steps.append(f"{i+1}. {t['tool']}({t['input'][:80]}) -> [{status}] {t['output'][:100]}")

        procedure = "\n".join(steps)
        quality = successes / len(trace)

        skill_name = soul_try_learn_skill(
            task_title=task_title[:100],
            task_type="tool_sequence",
            result_summary=procedure,
            cycle=cycle,
            quality_score=quality,
        )
        if skill_name:
            logger.info("SKILL FROM TRACE: %s (%d steps, q=%.2f)", skill_name, len(trace), quality)
        return skill_name
    except Exception as e:
        logger.warning("try_learn_skill_from_trace failed: %s", e)
        return None


def should_nudge_skill() -> bool:
    """Check if it's time for a skill nudge (Hermes pattern)."""
    return _cycles_since_skill_nudge >= SKILL_NUDGE_INTERVAL


def reset_skill_nudge():
    """Reset the nudge counter after performing skill review."""
    global _cycles_since_skill_nudge
    _cycles_since_skill_nudge = 0
