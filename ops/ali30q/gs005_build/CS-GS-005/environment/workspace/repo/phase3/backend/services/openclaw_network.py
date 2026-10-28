"""
OpenClaw Network — Trusted Node integration layer.

Nautilus operates as a trusted node in the decentralized OpenClaw network:
- Registers itself with an external OpenClaw registry
- Receives external tasks from other nodes and injects them into AcademicTask queue
- Publishes completed task results back to the network
- Exposes standard OpenClaw node API for peer discovery
"""
import json
import logging
import os
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx
from sqlalchemy.orm import Session

from models.database import AcademicTask

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Node constants
# ---------------------------------------------------------------------------
NODE_VERSION = "1.0"
NODE_PROTOCOL = "openclaw-v1"
NODE_CAPABILITIES = ["academic_tasks", "simulation", "data_labeling"]
HTTP_TIMEOUT = 10.0  # seconds


# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------

@dataclass
class NodeMetrics:
    """Runtime statistics for this OpenClaw node."""
    node_id: str
    started_at: float = field(default_factory=time.time)
    tasks_received: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    results_published: int = 0
    registry_url: Optional[str] = None
    registered_at: Optional[float] = None

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self.started_at

    @property
    def success_rate(self) -> float:
        total = self.tasks_completed + self.tasks_failed
        return round(self.tasks_completed / total, 4) if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "node_id": self.node_id,
            "uptime_seconds": round(self.uptime_seconds),
            "tasks_received": self.tasks_received,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "results_published": self.results_published,
            "success_rate": self.success_rate,
            "registry_url": self.registry_url,
            "registered_at": self.registered_at,
        }


# ---------------------------------------------------------------------------
# OpenClawNode
# ---------------------------------------------------------------------------

class OpenClawNode:
    """
    Nautilus trusted node in the OpenClaw network.

    Lifecycle:
    1. Boot → generate stable node_id from env or random
    2. Optional: register_as_node() with an external registry
    3. receive_external_task() to inject tasks from peer nodes
    4. publish_result() to report completed tasks back to the network
    """

    def __init__(self) -> None:
        self._node_id: str = os.environ.get(
            "OPENCLAW_NODE_ID",
            f"nautilus-{uuid.uuid4().hex[:12]}"
        )
        self._base_url: str = os.environ.get(
            "OPENCLAW_NODE_BASE_URL",
            "https://api.nautilus.social"
        )
        self.metrics = NodeMetrics(node_id=self._node_id)

    # ------------------------------------------------------------------
    # Node identity
    # ------------------------------------------------------------------

    def get_node_info(self) -> Dict[str, Any]:
        """Return public node descriptor for peer discovery."""
        return {
            "node_id": self._node_id,
            "version": NODE_VERSION,
            "protocol": NODE_PROTOCOL,
            "capabilities": NODE_CAPABILITIES,
            "base_url": self._base_url,
            "uptime_seconds": round(self.metrics.uptime_seconds),
            "tasks_completed": self.metrics.tasks_completed,
            "registered_at": self.metrics.registered_at,
        }

    # ------------------------------------------------------------------
    # Registry
    # ------------------------------------------------------------------

    async def register_as_node(self, registry_url: str) -> Dict[str, Any]:
        """
        POST to an external OpenClaw registry to announce this node.

        registry_url: base URL of the registry (e.g. https://registry.openclaw.io)
        Returns the registry response dict, or an error dict if registration fails.
        """
        payload = {
            "node_id": self._node_id,
            "url": self._base_url,
            "version": NODE_VERSION,
            "protocol": NODE_PROTOCOL,
            "capabilities": NODE_CAPABILITIES,
            "registered_at": datetime.now(timezone.utc).isoformat(),
        }
        endpoint = f"{registry_url.rstrip('/')}/nodes"
        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.post(endpoint, json=payload)
                resp.raise_for_status()
                data = resp.json()
                self.metrics.registry_url = registry_url
                self.metrics.registered_at = time.time()
                logger.info("Registered with OpenClaw registry %s as %s", registry_url, self._node_id)
                return {"success": True, "data": data}
        except httpx.TimeoutException:
            logger.warning("Timeout registering with registry %s", registry_url)
            return {"success": False, "error": "timeout", "registry_url": registry_url}
        except httpx.HTTPStatusError as exc:
            logger.warning("Registry returned %s: %s", exc.response.status_code, exc.response.text)
            return {"success": False, "error": f"http_{exc.response.status_code}", "registry_url": registry_url}
        except Exception as exc:
            logger.error("Unexpected error registering with registry: %s", exc)
            return {"success": False, "error": str(exc), "registry_url": registry_url}

    # ------------------------------------------------------------------
    # Inbound: external task injection
    # ------------------------------------------------------------------

    async def receive_external_task(
        self,
        task_payload: Dict[str, Any],
        db: Session,
    ) -> str:
        """
        Accept a task from an external OpenClaw peer and inject it into
        the AcademicTask queue.

        task_payload fields (all str unless noted):
            task_id     — external task identifier
            title       — short title
            description — full task description
            task_type   — e.g. "literature_review", "data_analysis"
            reward      — (optional) token reward amount
            deadline    — (optional) ISO-8601 deadline string
            callback_url — (optional) URL to POST result to when complete

        Returns the internal task_id assigned by Nautilus.
        """
        external_id: str = task_payload.get("task_id") or uuid.uuid4().hex
        internal_id = f"ocn-{external_id}"

        # Avoid duplicates
        existing = db.query(AcademicTask).filter(AcademicTask.task_id == internal_id).first()
        if existing:
            logger.info("Task %s already exists, skipping injection", internal_id)
            return internal_id

        parameters: Dict[str, Any] = {}
        if task_payload.get("reward"):
            parameters["reward"] = task_payload["reward"]
        if task_payload.get("deadline"):
            parameters["deadline"] = task_payload["deadline"]
        if task_payload.get("callback_url"):
            parameters["callback_url"] = task_payload["callback_url"]
        parameters["source"] = "openclaw_network"
        parameters["external_task_id"] = external_id
        parameters["source_node"] = task_payload.get("source_node", "unknown")

        task = AcademicTask(
            task_id=internal_id,
            title=task_payload.get("title", f"External task {external_id}"),
            description=task_payload.get("description", ""),
            task_type=task_payload.get("task_type", "external"),
            status="pending",
            parameters=json.dumps(parameters),
        )
        db.add(task)
        db.commit()
        db.refresh(task)

        self.metrics.tasks_received += 1
        logger.info("Injected external OpenClaw task %s → internal %s", external_id, internal_id)
        return internal_id

    # ------------------------------------------------------------------
    # Outbound: publish result
    # ------------------------------------------------------------------

    async def publish_result(
        self,
        internal_task_id: str,
        db: Session,
    ) -> Dict[str, Any]:
        """
        Push a completed task result to the callback URL stored in parameters,
        or to the registry if no callback is configured.

        Returns a dict with publish outcome.
        """
        task = db.query(AcademicTask).filter(AcademicTask.task_id == internal_task_id).first()
        if not task:
            return {"success": False, "error": "task_not_found", "task_id": internal_task_id}

        if task.status not in ("completed", "failed"):
            return {"success": False, "error": "task_not_finished", "status": task.status}

        params: Dict[str, Any] = {}
        if task.parameters:
            try:
                params = json.loads(task.parameters)
            except json.JSONDecodeError:
                pass

        external_id = params.get("external_task_id", internal_task_id)
        callback_url = params.get("callback_url")

        result_payload = {
            "task_id": external_id,
            "internal_task_id": internal_task_id,
            "status": task.status,
            "result_output": task.result_output,
            "result_error": task.result_error,
            "execution_time": task.execution_time,
            "reported_by": self._node_id,
            "reported_at": datetime.now(timezone.utc).isoformat(),
        }

        target = callback_url or (
            f"{self.metrics.registry_url}/tasks/{external_id}/result"
            if self.metrics.registry_url else None
        )

        if not target:
            logger.info("No callback URL for task %s; result not published externally", internal_task_id)
            return {"success": True, "published": False, "reason": "no_callback_url"}

        try:
            async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
                resp = await client.post(target, json=result_payload)
                resp.raise_for_status()
                self.metrics.results_published += 1
                logger.info("Published result for task %s to %s", internal_task_id, target)
                return {"success": True, "published": True, "target": target, "status_code": resp.status_code}
        except httpx.TimeoutException:
            logger.warning("Timeout publishing result for %s to %s", internal_task_id, target)
            return {"success": False, "error": "timeout", "target": target}
        except httpx.HTTPStatusError as exc:
            logger.warning("Publish returned HTTP %s for %s", exc.response.status_code, internal_task_id)
            return {"success": False, "error": f"http_{exc.response.status_code}", "target": target}
        except Exception as exc:
            logger.error("Error publishing result for %s: %s", internal_task_id, exc)
            return {"success": False, "error": str(exc), "target": target}

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    def get_task_status(self, internal_task_id: str, db: Session) -> Optional[Dict[str, Any]]:
        """Return task status dict, or None if not found."""
        task = db.query(AcademicTask).filter(AcademicTask.task_id == internal_task_id).first()
        if not task:
            return None
        params: Dict[str, Any] = {}
        if task.parameters:
            try:
                params = json.loads(task.parameters)
            except json.JSONDecodeError:
                pass
        return {
            "internal_task_id": task.task_id,
            "external_task_id": params.get("external_task_id"),
            "status": task.status,
            "title": task.title,
            "task_type": task.task_type,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "updated_at": task.updated_at.isoformat() if task.updated_at else None,
            "source": params.get("source"),
        }


# ---------------------------------------------------------------------------
# Global singleton
# ---------------------------------------------------------------------------

_openclaw_node: Optional[OpenClawNode] = None


def get_openclaw_node() -> OpenClawNode:
    """Return the application-level OpenClawNode singleton."""
    global _openclaw_node
    if _openclaw_node is None:
        _openclaw_node = OpenClawNode()
        logger.info("OpenClawNode initialised: %s", _openclaw_node.get_node_info())
    return _openclaw_node
