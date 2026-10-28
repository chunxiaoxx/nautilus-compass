"""
EvoMap Integration Service — Lightweight stub.

The full evomap learning pipeline (8 sub-services) has been consolidated.
This stub preserves the API contract so callers don't break.
When the evomap DB tables are ready, the full pipeline can be restored.
"""
import logging
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class EvomapIntegrationService:
    """Lightweight EvoMap stub — logs learning cycles without heavy sub-services."""

    def __init__(self, db=None):
        self.db = db

    async def execute_learning_cycle(
        self,
        task_id: int,
        agent_id: int,
        task_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Record that a learning cycle happened. Full pipeline deferred."""
        logger.info(
            "EvoMap learning cycle (stub): task=%s agent=%s type=%s",
            task_id, agent_id, task_result.get("context", "?"),
        )
        return {
            "reflection": {"status": "stub"},
            "knowledge_nodes": [],
            "capsules_created": [],
            "emergent_patterns": [],
            "learning_progress": {},
            "specialization_update": {},
            "next_recommendations": [],
            "cycle_completed_at": datetime.utcnow().isoformat(),
        }
