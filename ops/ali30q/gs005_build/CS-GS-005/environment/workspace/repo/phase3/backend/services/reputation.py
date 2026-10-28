"""Thin wrapper → services.pairs.identity (自↔他 Pair 6)"""
import logging
from services.pairs.identity import (  # noqa: F401
    ReputationTier, get_reputation_tier, calculate_score_delta,
    routing_priority, update_reputation, get_reputation_detail,
    apply_inactivity_decay,
)

logger = logging.getLogger(__name__)


def update_reputation_on_reward(agent_wallet: str, nau_amount: int, task_type: str):
    """Bridge E.5: Update reputation after NAU reward mint.

    Uses direct SQL (sync) since the async update_reputation needs async db.
    EWMA formula: new_score = alpha * new_rating + (1-alpha) * old_score
    """
    ALPHA = 0.1
    try:
        from utils.database import SessionLocal
        from sqlalchemy import text as sql_text
        db = SessionLocal()
        try:
            row = db.execute(sql_text(
                "SELECT agent_id, reputation_score FROM agents "
                "WHERE LOWER(wallet_address)=LOWER(:w) LIMIT 1"
            ), {"w": agent_wallet}).fetchone()
            if not row:
                return
            agent_id = row.agent_id
            old_score = row.reputation_score or 50.0
            # Map NAU to rating on 0-100 scale (log-ish to avoid saturation)
            import math
            new_rating = min(100, 50 + math.log2(max(1, nau_amount)) * 10)
            new_score = round(ALPHA * new_rating + (1 - ALPHA) * old_score, 2)
            db.execute(sql_text(
                "UPDATE agents SET reputation_score=:score WHERE agent_id=:aid"
            ), {"score": new_score, "aid": agent_id})
            db.commit()
            logger.info("Bridge E.5: reputation %.1f→%.1f for agent %s (nau=%d)", old_score, new_score, agent_id, nau_amount)
        finally:
            db.close()
    except Exception as e:
        logger.debug("update_reputation_on_reward: %s", e)
