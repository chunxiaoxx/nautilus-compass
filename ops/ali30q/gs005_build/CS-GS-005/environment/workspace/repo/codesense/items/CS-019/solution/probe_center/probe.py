"""probe_center.probe — 服务健康探针(金标修复版)。"""
from __future__ import annotations


# 必需键清单(§2:缺键即失明,失明必须叫;默认值兜底禁用)
REQUIRED_KEYS = ("alert_threshold_p99_ms", "interval_sec", "retries", "probe_name")


class ProbeConfigError(Exception):
    """必需配置键缺失——§2 探针纪律:缺键即失明,失明必须叫。"""


def build_probe_config(raw: dict) -> dict:
    """从配置平台拉取的原始配置构建探针配置。

    修复:必需键缺失时启动即失败(fail-fast),报错含缺失键名;
    代码不再携带任何业务阈值默认值(§4)。
    """
    missing = [k for k in REQUIRED_KEYS if raw.get(k) is None]
    if missing:
        raise ProbeConfigError(f"missing required config keys: {sorted(missing)}")
    cfg = {k: raw[k] for k in REQUIRED_KEYS}
    return cfg


def judge(service: str, p99_ms: int, cfg: dict) -> str | None:
    """健康判定:超阈值返回告警消息,正常返回 None。"""
    if p99_ms > cfg["alert_threshold_p99_ms"]:
        return f"ALERT {service} p99 {p99_ms}ms > {cfg['alert_threshold_p99_ms']}ms"
    return None
