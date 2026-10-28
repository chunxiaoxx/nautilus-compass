"""
Daemon Communications — lightweight inter-daemon messaging via Redis Event Bus.

Instead of Socket.IO (heavy, needs persistent connection), daemons communicate
through the same Event Bus that powers the Evolution Pulse.

Events:
  agent.request_help  — KAIROS asks MiniMax to handle a specific subtask
  agent.task_result   — MiniMax reports back to KAIROS with results
  agent.status_update — Either daemon broadcasts its current state

This is the "通↔听" (communicate↔listen) yin-yang pair in action.
"""
import asyncio
import json
import logging
import os
from typing import Dict, Any, Optional, Callable

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL_PREFIX = "nautilus:agent."


async def send_to_agent(target_agent_id: int, message_type: str, payload: dict):
    """Send a message to a specific agent via Redis Pub/Sub."""
    import redis.asyncio as aioredis
    channel = f"{CHANNEL_PREFIX}{target_agent_id}.{message_type}"
    try:
        r = aioredis.from_url(REDIS_URL, decode_responses=True)
        async with r:
            await r.publish(channel, json.dumps(payload))
        logger.info("daemon_comms: sent %s to agent %d", message_type, target_agent_id)
    except Exception as e:
        logger.warning("daemon_comms: send failed: %s", e)


async def broadcast_status(agent_id: int, status: dict):
    """Broadcast own status to all listeners."""
    await send_to_agent(0, "status_update", {"from_agent": agent_id, **status})


class DaemonListener:
    """Listen for messages directed to this agent."""

    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self._handlers: Dict[str, Callable] = {}
        self._task: Optional[asyncio.Task] = None

    def on(self, message_type: str, handler: Callable):
        """Register handler for a message type."""
        self._handlers[message_type] = handler

    async def start(self):
        """Start listening in background."""
        self._task = asyncio.create_task(self._listen())
        logger.info("daemon_comms: listener started for agent %d", self.agent_id)

    async def _listen(self):
        """Subscribe to agent-specific channels."""
        import redis.asyncio as aioredis
        try:
            r = aioredis.from_url(REDIS_URL, decode_responses=True)
            pubsub = r.pubsub()
            # Listen to messages for this agent + broadcasts (agent 0)
            await pubsub.psubscribe(
                f"{CHANNEL_PREFIX}{self.agent_id}.*",
                f"{CHANNEL_PREFIX}0.*",
            )
            async for message in pubsub.listen():
                if message["type"] != "pmessage":
                    continue
                channel = message.get("channel", "")
                # Extract message_type from channel: nautilus:agent.{id}.{type}
                parts = channel.split(".")
                msg_type = parts[-1] if len(parts) >= 3 else "unknown"

                handler = self._handlers.get(msg_type)
                if handler:
                    try:
                        payload = json.loads(message.get("data", "{}"))
                        await handler(payload)
                    except Exception as e:
                        logger.warning("daemon_comms: handler error for %s: %s", msg_type, e)
        except Exception as e:
            logger.error("daemon_comms: listener crashed: %s", e)


# ── Pre-built message types ─────────────────────────────────────────────────

async def request_help(from_agent: int, target_agent: int, task_id: str, description: str):
    """KAIROS requests MiniMax to handle a subtask."""
    await send_to_agent(target_agent, "request_help", {
        "from_agent": from_agent,
        "task_id": task_id,
        "description": description[:2000],
    })


async def report_result(from_agent: int, target_agent: int, task_id: str, result: str):
    """MiniMax reports result back to KAIROS."""
    await send_to_agent(target_agent, "task_result", {
        "from_agent": from_agent,
        "task_id": task_id,
        "result": result[:2000],
    })


async def share_skill(from_agent: int, target_agent: int, skill_data: dict):
    """Hermes pattern: share a learned skill with another agent via event bus."""
    await send_to_agent(target_agent, "skill_share", {
        "from_agent": from_agent,
        "skill": skill_data,
    })
