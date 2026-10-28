"""
Partner webhook service - notify partners when tasks complete/fail.

Fires HTTP POST to partner's webhook_url or per-task callback_url.
All payloads are brand-neutral.
"""
import logging
import json
from datetime import datetime
from typing import Optional

import httpx

from models.partner import Partner, PartnerTask
from models.database import AcademicTask
from utils.database import get_db_context

logger = logging.getLogger(__name__)

WEBHOOK_TIMEOUT = 10  # seconds
MAX_RETRIES = 2


async def notify_partner_task_complete(task_id: str) -> None:
    """
    Check if a completed/failed task belongs to a partner.
    If so, fire the webhook callback.
    """
    try:
        with get_db_context() as db:
            pt = db.query(PartnerTask).filter(
                PartnerTask.internal_task_id == task_id,
            ).first()
            if not pt:
                return  # Not a partner task

            partner = db.query(Partner).filter(
                Partner.partner_id == pt.partner_id,
            ).first()
            if not partner:
                return

            task = db.query(AcademicTask).filter(
                AcademicTask.task_id == task_id,
            ).first()
            if not task:
                return

            webhook_url = partner.webhook_url
            if not webhook_url:
                return

            # Build brand-neutral payload
            payload = {
                "event": "task.completed" if task.status == "completed" else "task.failed",
                "task_id": task.task_id,
                "external_ref": pt.external_ref,
                "type": task.task_type,
                "status": task.status,
                "timestamp": datetime.utcnow().isoformat(),
            }

            if task.status == "completed":
                payload["result"] = {
                    "code": task.result_code,
                    "output": task.result_output,
                    "plots": json.loads(task.result_plots) if task.result_plots else [],
                    "execution_time": task.execution_time,
                }
            elif task.status == "failed":
                payload["error"] = task.result_error

        # Send webhook (outside DB session)
        await _send_webhook(webhook_url, payload, task_id)

    except Exception as e:
        logger.error("Webhook notification failed for task %s: %s", task_id, e)


async def _send_webhook(url: str, payload: dict, task_id: str) -> None:
    """Send webhook with retry."""
    for attempt in range(MAX_RETRIES + 1):
        try:
            async with httpx.AsyncClient(timeout=WEBHOOK_TIMEOUT) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )
                if resp.status_code < 300:
                    logger.info(
                        "Webhook sent for task %s → %s (status=%d)",
                        task_id, url, resp.status_code,
                    )
                    return
                else:
                    logger.warning(
                        "Webhook for task %s returned %d (attempt %d/%d)",
                        task_id, resp.status_code, attempt + 1, MAX_RETRIES + 1,
                    )
        except Exception as e:
            logger.warning(
                "Webhook for task %s attempt %d failed: %s",
                task_id, attempt + 1, e,
            )

    logger.error("Webhook for task %s exhausted all retries", task_id)


async def refund_partner_on_failure(task_id: str) -> None:
    """
    If a partner task fails, refund the cost back to partner balance.
    """
    try:
        with get_db_context() as db:
            pt = db.query(PartnerTask).filter(
                PartnerTask.internal_task_id == task_id,
            ).first()
            if not pt:
                return

            partner = db.query(Partner).filter(
                Partner.partner_id == pt.partner_id,
            ).first()
            if not partner:
                return

            task = db.query(AcademicTask).filter(
                AcademicTask.task_id == task_id,
            ).first()
            if not task or task.status != "failed":
                return

            # Refund
            refund_amount = pt.cost_to_partner
            partner.balance += refund_amount
            partner.total_spent -= refund_amount
            db.commit()

            logger.info(
                "Refunded %.2f RMB to partner %s for failed task %s",
                refund_amount, partner.partner_id, task_id,
            )
    except Exception as e:
        logger.error("Refund failed for task %s: %s", task_id, e)
