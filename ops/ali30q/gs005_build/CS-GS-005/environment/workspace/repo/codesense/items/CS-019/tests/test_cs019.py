"""CS-019 UT:缺键 fail-fast + 配置口径判定(passrate 全对率口径)。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from probe_center import build_probe_config, judge  # noqa: E402
from probe_center.probe import ProbeConfigError  # noqa: E402

GOOD = {"alert_threshold_p99_ms": 1500, "interval_sec": 15, "retries": 2, "probe_name": "settlement"}


def test_ut1_missing_key_fails_fast():
    """UT1[主判定] 必需键缺失:启动即失败,报错含键名,不静默兜底。"""
    bad = dict(GOOD)
    del bad["alert_threshold_p99_ms"]
    try:
        build_probe_config(bad)
        raise AssertionError("缺键未失败")
    except ProbeConfigError as e:
        assert "alert_threshold_p99_ms" in str(e), f"报错缺键名: {e}"


def test_ut2_platform_threshold_governs():
    """UT2[主判定] 配置平台口径(1.5s)生效:3.8s 必须告警。"""
    cfg = build_probe_config(GOOD)
    msg = judge("settlement", 3800, cfg)
    assert msg is not None and "3800" in msg


def test_ut3_no_silent_default_for_name():
    """UT3[边界] probe_name 缺失同样 fail-fast(不得退化为 unnamed)。"""
    bad = dict(GOOD)
    del bad["probe_name"]
    try:
        build_probe_config(bad)
        raise AssertionError("probe_name 缺失未失败")
    except ProbeConfigError:
        pass


def test_ut4_full_config_passes_through():
    """UT4[回归] 完整配置:正常构建且阈值透传无污染。"""
    cfg = build_probe_config(GOOD)
    assert cfg["alert_threshold_p99_ms"] == 1500
    assert judge("settlement", 1200, cfg) is None
