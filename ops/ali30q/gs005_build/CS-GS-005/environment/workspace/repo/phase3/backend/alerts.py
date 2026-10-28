"""
AlertManager webhook endpoints for Nautilus API.
"""
from fastapi import APIRouter, BackgroundTasks, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logging_config import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/alerts", tags=["alerts"])


class Alert(BaseModel):
    """AlertManager alert model."""
    status: str
    labels: Dict[str, str]
    annotations: Dict[str, str]
    startsAt: str
    endsAt: Optional[str] = None
    generatorURL: str
    fingerprint: str


class AlertWebhook(BaseModel):
    """AlertManager webhook payload."""
    version: str
    groupKey: str
    truncatedAlerts: int
    status: str
    receiver: str
    groupLabels: Dict[str, str]
    commonLabels: Dict[str, str]
    commonAnnotations: Dict[str, str]
    externalURL: str
    alerts: List[Alert]


async def process_alert(alert: Alert, severity: str):
    """
    Process individual alert.

    Args:
        alert: Alert object
        severity: Alert severity level
    """
    alert_info = {
        "severity": severity,
        "status": alert.status,
        "alertname": alert.labels.get("alertname", "unknown"),
        "instance": alert.labels.get("instance", "unknown"),
        "summary": alert.annotations.get("summary", ""),
        "description": alert.annotations.get("description", ""),
        "startsAt": alert.startsAt,
        "fingerprint": alert.fingerprint
    }

    if severity == "critical":
        logger.critical(f"严重告警: {alert_info}")
        # TODO: 发送紧急通知（邮件、短信、钉钉等）
    elif severity == "warning":
        logger.warning(f"警告告警: {alert_info}")
        # TODO: 发送警告通知
    else:
        logger.info(f"信息告警: {alert_info}")


@router.post("/webhook")
async def alert_webhook(webhook: AlertWebhook, background_tasks: BackgroundTasks):
    """
    Receive AlertManager webhook notifications.

    Args:
        webhook: AlertManager webhook payload
        background_tasks: FastAPI background tasks

    Returns:
        dict: Status response
    """
    logger.info(f"收到告警 webhook: {webhook.groupKey}, 状态: {webhook.status}, 告警数: {len(webhook.alerts)}")

    # 处理每个告警
    for alert in webhook.alerts:
        severity = alert.labels.get("severity", "info")
        background_tasks.add_task(process_alert, alert, severity)

    return {
        "status": "received",
        "groupKey": webhook.groupKey,
        "alertCount": len(webhook.alerts),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/critical")
async def critical_alert(alert: Dict[str, Any]):
    """
    Receive critical alerts.

    Args:
        alert: Alert data

    Returns:
        dict: Status response
    """
    logger.critical(f"收到严重告警: {alert}")

    # TODO: 实现紧急通知逻辑
    # - 发送邮件
    # - 发送短信
    # - 发送钉钉/企业微信通知
    # - 触发自动恢复流程

    return {
        "status": "critical_received",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/warning")
async def warning_alert(alert: Dict[str, Any]):
    """
    Receive warning alerts.

    Args:
        alert: Alert data

    Returns:
        dict: Status response
    """
    logger.warning(f"收到警告告警: {alert}")

    # TODO: 实现警告通知逻辑
    # - 发送邮件
    # - 记录到数据库
    # - 更新监控面板

    return {
        "status": "warning_received",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/info")
async def info_alert(alert: Dict[str, Any]):
    """
    Receive informational alerts.

    Args:
        alert: Alert data

    Returns:
        dict: Status response
    """
    logger.info(f"收到信息告警: {alert}")

    return {
        "status": "info_received",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/health")
async def alerts_health():
    """
    Health check endpoint for alerts system.

    Returns:
        dict: Health status
    """
    return {
        "status": "healthy",
        "service": "alerts",
        "timestamp": datetime.utcnow().isoformat()
    }
