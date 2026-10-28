"""
Nautilus Event Bus — Redis Pub/Sub 事件驱动架构
仿 Claude Code KAIROS：事件触发 > 定时轮询
"""
import asyncio
import json
import logging
import os
from typing import Any, Callable, Dict, List

import redis.asyncio as aioredis

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
CHANNEL_PREFIX = "nautilus:"

# 事件处理器注册表
_handlers: Dict[str, List[Callable]] = {}


def on(event_type: str):
    """装饰器：注册事件处理器"""
    def decorator(fn: Callable):
        if event_type not in _handlers:
            _handlers[event_type] = []
        _handlers[event_type].append(fn)
        return fn
    return decorator


async def emit(event_type: str, payload: dict) -> None:
    """发布事件到 Redis 频道"""
    channel = f"{CHANNEL_PREFIX}{event_type}"
    try:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        async with redis:
            await redis.publish(channel, json.dumps(payload))
        logger.debug(f"Event emitted: {event_type}")
    except Exception as e:
        logger.warning(f"Event bus emit failed ({event_type}): {e}")


async def _subscriber_loop() -> None:
    """内部循环：订阅所有 nautilus:* 频道并分发事件"""
    try:
        redis = aioredis.from_url(REDIS_URL, decode_responses=True)
        pubsub = redis.pubsub()
        await pubsub.psubscribe(f"{CHANNEL_PREFIX}*")
        logger.info(f"Event bus subscriber started, listening on {CHANNEL_PREFIX}*")

        async for message in pubsub.listen():
            if message["type"] != "pmessage":
                continue
            channel: str = message.get("channel", "")
            # Strip prefix to get event_type
            event_type = channel.removeprefix(CHANNEL_PREFIX)
            raw = message.get("data", "{}")
            try:
                payload = json.loads(raw)
            except json.JSONDecodeError:
                logger.warning(f"Event bus: invalid JSON on channel {channel}")
                continue

            handlers = _handlers.get(event_type, [])
            if handlers:
                results = await asyncio.gather(
                    *[h(payload) for h in handlers],
                    return_exceptions=True,
                )
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        logger.error(
                            f"Event handler error [{event_type}][{i}]: {result}"
                        )
    except Exception as e:
        logger.error(f"Event bus subscriber crashed: {e}")


def start_subscriber() -> asyncio.Task:
    """启动订阅器，在后台运行，不阻塞主进程"""
    task = asyncio.create_task(_subscriber_loop())
    return task


# 预定义事件常量
class Events:
    TASK_CREATED = "task.created"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_RATED = "task.rated"
    AGENT_REGISTERED = "agent.registered"
    PLATFORM_ANOMALY = "platform.anomaly"
    PLATFORM_SNAPSHOT = "platform.snapshot"
    # Evolution Pulse — dialectical fusion events
    SANDBOX_FINALIZED = "sandbox.finalized"
    EVOLUTION_RECORDED = "evolution.recorded"
    CURIOSITY_HYPOTHESIS = "curiosity.hypothesis"
    REPUTATION_TIER_CHANGED = "reputation.tier_changed"
    PROPOSAL_CONSENSUS = "proposal.consensus_reached"
    PLATFORM_HEARTBEAT = "platform.heartbeat"
