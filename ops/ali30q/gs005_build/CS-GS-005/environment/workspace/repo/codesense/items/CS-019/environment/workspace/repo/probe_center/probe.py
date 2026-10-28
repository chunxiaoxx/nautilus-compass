"""probe_center.probe — 服务健康探针(坑版:缺键静默默认值待修)。"""
from __future__ import annotations


# 代码内业务阈值(§4 变更纪律:阈值口径以配置平台为准,代码不得固化)
LEGACY_DEFAULTS = {
    "alert_threshold_p99_ms": 5000,
    "interval_sec": 30,
    "retries": 3,
}


class ProbeConfigError(Exception):
    """必需配置键缺失——§2 探针纪律:缺键即失明,失明必须叫。"""


def build_probe_config(raw: dict) -> dict:
    """从配置平台拉取的原始配置构建探针配置。

    必需键:alert_threshold_p99_ms / interval_sec / retries / probe_name。
    """
    cfg = {}
    for key, default in LEGACY_DEFAULTS.items():
        cfg[key] = raw.get(key, default)  # 坑:缺键静默用默认值
    cfg["probe_name"] = raw.get("probe_name", "unnamed")
    return cfg


def judge(service: str, p99_ms: int, cfg: dict) -> str | None:
    """健康判定:超阈值返回告警消息,正常返回 None。"""
    if p99_ms > cfg["alert_threshold_p99_ms"]:
        return f"ALERT {service} p99 {p99_ms}ms > {cfg['alert_threshold_p99_ms']}ms"
    return None
