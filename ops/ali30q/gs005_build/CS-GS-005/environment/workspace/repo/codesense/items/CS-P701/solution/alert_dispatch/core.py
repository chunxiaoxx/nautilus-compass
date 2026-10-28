"""alert_dispatch.core — 告警分级分发(金标实现)。"""
from __future__ import annotations


def dispatch_alert(alerts: list[dict], config: dict) -> dict:
    """按分级分发告警(§1-§4,以§2原文为准,§5备注不采纳)。"""
    channel_priorities = config.get("channel_priorities", {})
    available = set(config.get("available_channels", []))
    result = {"dispatched": [], "skipped": [], "deduplicated": [], "no_route": []}
    seen: set[str] = set()

    for alert in alerts:
        alert_id = alert.get("alert_id", "")
        severity = alert.get("severity", "")
        status = alert.get("status", "")

        # §2 去重
        if alert_id in seen:
            result["deduplicated"].append(alert_id)
            continue

        # §2 resolved 不投递
        if status == "resolved":
            result["skipped"].append(alert_id)
            seen.add(alert_id)
            continue

        # §2+§4 按优先级取首个可用渠道
        # 未注册的 severity≠渠道全不可用——未知级别直接 no_route
        if severity not in channel_priorities:
            result["no_route"].append(alert_id)
            seen.add(alert_id)
            continue
        channels = channel_priorities.get(severity, [])
        target = None
        for ch in channels:
            if ch in available:
                target = ch
                break

        # §2 fallback: 仅在 severity 已注册但对应渠道全不可用时触发
        if target is None and "fallback" in available:
            target = "fallback"

        if target is None:
            result["no_route"].append(alert_id)
            seen.add(alert_id)
            continue

        result["dispatched"].append({
            "alert_id": alert_id,
            "channel": target,
            "attempts": 1,
        })
        seen.add(alert_id)

    return result
