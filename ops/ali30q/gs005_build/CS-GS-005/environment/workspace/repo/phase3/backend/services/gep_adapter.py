"""
GEP Protocol Adapter - Connects Nautilus to EvoMap global evolution network.

Implements the Genome Evolution Protocol (GEP) to enable:
- Publishing Nautilus agent capabilities as Genes/Capsules to EvoMap
- Fetching proven solutions from the EvoMap marketplace
- Reporting execution results back to the network

GEP Protocol: https://evomap.ai/blog/gep-protocol-deep-dive
No API key required - agents POST to https://evomap.ai/a2a/hello
"""
import os
import hashlib
import logging
import time
from typing import Optional
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)

EVOMAP_HUB_URL = os.getenv("EVOMAP_HUB_URL", "https://evomap.ai")
NAUTILUS_NODE_ID = os.getenv("NAUTILUS_NODE_ID", "nautilus-core-v1")


class GEPAdapter:
    """Adapter between Nautilus internal formats and GEP protocol."""

    def __init__(self, hub_url: str = EVOMAP_HUB_URL, node_id: str = NAUTILUS_NODE_ID):
        self._hub_url = hub_url.rstrip("/")
        self._node_id = node_id
        self._registered = False

    async def hello(self) -> dict:
        """Register with the EvoMap hub (GEP-A2A hello message)."""
        node_id = _get_node_id()
        envelope = _gep_envelope("hello", {
            "capabilities": {
                "code_execution": True,
                "data_labeling": True,
                "scientific_computing": True,
                "research_synthesis": True,
                "multi_agent_consensus": True,
                "self_improvement": True,
            },
            "env_fingerprint": {
                "platform": "linux",
                "arch": "x64",
                "node_name": "Nautilus",
                "agent_count": 144,
                "platform_url": "https://www.nautilus.social",
            },
        }, sender_id=node_id)
        raw = await self._post("/a2a/hello", envelope)
        # EvoMap wraps response in its own envelope — extract payload
        result = raw.get("payload", raw) if isinstance(raw, dict) else raw
        self._registered = result.get("status") == "acknowledged"
        if self._registered:
            # Save hub-assigned node_id and secret
            self._hub_node_id = result.get("your_node_id", node_id)
            self._node_secret = result.get("node_secret", "")
            self._claim_url = result.get("claim_url", "")
            # Persist for restarts
            try:
                import json as _json
                cred_file = os.path.join(os.path.dirname(__file__), ".evomap_credentials.json")
                with open(cred_file, "w") as f:
                    _json.dump({
                        "node_id": self._hub_node_id,
                        "secret": self._node_secret,
                        "claim_url": self._claim_url,
                    }, f)
            except Exception:
                pass
            logger.info(f"EvoMap hello SUCCESS: node_id={self._hub_node_id}, claim={self._claim_url}")
        else:
            logger.warning(f"EvoMap hello failed: {result}")
        return result

    async def publish_gene(
        self,
        name: str,
        description: str,
        code: str,
        task_type: str,
        confidence: float = 0.8,
        tags: Optional[list] = None,
    ) -> dict:
        """
        Publish a reusable strategy (Gene) to EvoMap.

        A Gene is a proven solution template that other agents can discover
        and reuse. Generated from successful task completions.
        """
        gene_id = _content_hash(code)
        envelope = _gep_envelope("publish", {
            "asset_type": "gene",
            "asset_id": gene_id,
            "name": name,
            "description": description,
            "code": code,
            "task_type": task_type,
            "confidence": confidence,
            "tags": tags or [],
            "signals": [task_type, "nautilus"],
            "origin_node": _get_node_id(),
        })
        result = await self._post("/a2a/publish", envelope)
        logger.info(f"Published gene {gene_id}: {name}")
        return {"gene_id": gene_id, **result}

    async def publish_capsule(
        self,
        name: str,
        trigger_signal: str,
        fix_code: str,
        validation_command: str,
        confidence: float = 0.9,
        environment: Optional[dict] = None,
    ) -> dict:
        """
        Publish a validated fix (Capsule) to EvoMap.

        A Capsule is a validated fix bundled with trigger signals,
        confidence scores, and environment fingerprints.
        """
        capsule_id = _content_hash(fix_code + trigger_signal)
        envelope = _gep_envelope("publish", {
            "asset_type": "capsule",
            "asset_id": capsule_id,
            "name": name,
            "trigger_signal": trigger_signal,
            "fix_code": fix_code,
            "validation_command": validation_command,
            "confidence": confidence,
            "environment": environment or {},
            "origin_node": self._node_id,
        })
        result = await self._post("/a2a/publish", envelope)
        logger.info(f"Published capsule {capsule_id}: {name}")
        return {"capsule_id": capsule_id, **result}

    async def fetch_solutions(
        self,
        query: str,
        task_type: Optional[str] = None,
        limit: int = 5,
    ) -> list:
        """
        Fetch proven solutions from EvoMap for a given problem.

        Returns a list of Genes/Capsules ranked by GDI score.
        """
        envelope = _gep_envelope("fetch", {
            "query": query,
            "signals": [task_type] if task_type else [],
            "limit": limit,
        })
        result = await self._post("/a2a/fetch", envelope)
        assets = result.get("assets", [])
        logger.info(f"Fetched {len(assets)} solutions for: {query[:50]}")
        return assets

    async def report_result(
        self,
        asset_id: str,
        success: bool,
        execution_time: float,
        notes: str = "",
    ) -> dict:
        """
        Report execution result of a Gene/Capsule back to EvoMap.

        This feeds into the GDI (Global Desirability Index) scoring.
        """
        envelope = _gep_envelope("report", {
            "asset_id": asset_id,
            "success": success,
            "execution_time": execution_time,
            "notes": notes,
            "reporter_node": self._node_id,
        })
        return await self._post("/a2a/report", envelope)

    async def _post(self, path: str, data: dict) -> dict:
        """Send a GEP message to the hub."""
        url = f"{self._hub_url}{path}"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=data)
                body = response.json() if response.headers.get("content-type", "").startswith("application/json") else {"raw": response.text[:500]}
                if response.status_code in (200, 201):
                    return body
                logger.warning(f"EvoMap {path} returned {response.status_code}: {body}")
                return {"success": False, "status": response.status_code, **body}
        except httpx.ConnectError:
            logger.warning(f"EvoMap hub not reachable: {url}")
            return {"success": False, "error": "hub_unreachable"}
        except Exception as e:
            logger.error(f"EvoMap request failed: {e}")
            return {"success": False, "error": str(e)}


def _gep_envelope(msg_type: str, payload: dict, sender_id: str = "") -> dict:
    """Create a GEP-A2A protocol envelope (EvoMap standard)."""
    import uuid
    return {
        "protocol": "gep-a2a",
        "protocol_version": "1.0.0",
        "message_type": msg_type,
        "message_id": f"msg_{int(time.time()*1000)}_{uuid.uuid4().hex[:8]}",
        "sender_id": sender_id or _get_node_id(),
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "payload": payload,
    }


def _get_node_id() -> str:
    """Get or generate persistent node ID (node_<16hex>)."""
    node_file = os.path.join(os.path.dirname(__file__), ".evomap_node_id")
    try:
        if os.path.exists(node_file):
            return open(node_file).read().strip()
    except Exception:
        pass
    node_id = f"node_{hashlib.sha256(NAUTILUS_NODE_ID.encode()).hexdigest()[:16]}"
    try:
        with open(node_file, "w") as f:
            f.write(node_id)
    except Exception:
        pass
    return node_id


def _content_hash(content: str) -> str:
    """SHA-256 content-addressable ID (GEP standard)."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]


# Singleton
_adapter: Optional[GEPAdapter] = None


def get_gep_adapter() -> GEPAdapter:
    """Get the global GEP adapter instance."""
    global _adapter
    if _adapter is None:
        _adapter = GEPAdapter()
    return _adapter
