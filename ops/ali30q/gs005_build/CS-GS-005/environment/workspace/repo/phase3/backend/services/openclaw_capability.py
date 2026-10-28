"""
OpenClaw ACP capability declaration formatter.

Formats Nautilus agent capabilities in the standard OpenClaw/Virtuals Protocol
Agent Capability Profile (ACP) format for registration and discovery.
"""
from __future__ import annotations

from services.ability_tags import ABILITY_TAGS, TASK_TYPE_TO_TAGS
from services.nautilus_token import TASK_TYPE_REWARDS


def format_agent_capability_profile(
    agent_id: int,
    agent_name: str,
    wallet_address: str,
    specialties: list[str],
    survival_level: str = "GROWING",
    tasks_completed: int = 0,
) -> dict:
    """
    Generate OpenClaw-compatible Agent Capability Profile (ACP).

    Returns a dict that can be submitted to ClawHub or OpenClaw registry.
    """
    # Map specialties to task types this agent can handle
    capable_task_types: list[str] = []
    agent_tags = {s.lower() for s in specialties}
    for task_type, required_tags in TASK_TYPE_TO_TAGS.items():
        # Accept the task type if: agent has no specialties (general-purpose),
        # or at least one required tag overlaps with the agent's tags.
        if not specialties or bool(agent_tags & set(required_tags)):
            capable_task_types.append(task_type)

    return {
        "agent_id": str(agent_id),
        "name": agent_name,
        "wallet": wallet_address,
        "protocol": "nautilus-acp-v1",
        "capabilities": {
            "skills": specialties,
            "task_types": capable_task_types,
            "skill_descriptions": {
                tag: ABILITY_TAGS[tag]
                for tag in specialties
                if tag in ABILITY_TAGS
            },
        },
        "reputation": {
            "survival_level": survival_level,
            "tasks_completed": tasks_completed,
        },
        "endpoints": {
            "task_intake": "/api/academic-tasks",
            "status": "/api/agents/{agent_id}",
            "token_balance": "/api/agents/{agent_id}/token-balance",
        },
    }


def format_skill_declaration(task_type: str) -> dict:
    """Format a single skill as OpenClaw SKILL.md equivalent JSON."""
    tags = TASK_TYPE_TO_TAGS.get(task_type, [])
    return {
        "skill_id": task_type,
        "name": task_type.replace("_", " ").title(),
        "description": " + ".join(ABILITY_TAGS.get(t, t) for t in tags),
        "input_schema": {
            "title": "string",
            "description": "string",
            "task_type": task_type,
            "parameters": "object (optional)",
        },
        "output_schema": {
            "result_output": "string",
            "result_code": "string (optional)",
            "execution_time": "float (seconds)",
        },
        "reward_nau": TASK_TYPE_REWARDS.get(task_type, 1),
    }
