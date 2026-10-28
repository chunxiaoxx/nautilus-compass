"""CS-P701 UT:告警分级分发,L1-L4 分层 22 条(含 L4h 反幻觉 gating)。passrate 全对率。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "environment" / "workspace" / "repo"))

from alert_dispatch import dispatch_alert as f  # noqa: E402

CF = {
    "channel_priorities": {
        "critical": ["pager", "sms", "email"],
        "warning": ["sms", "email"],
        "info": ["email"],
    },
    "available_channels": ["pager", "sms", "email", "fallback"],
}

def _a(aid, sev, status="firing"):
    return {"alert_id": aid, "severity": sev, "status": status,
            "channel": "", "created_at": "2026-10-25T00:00:00"}

# ---- L1 基础分发(5) ----

def test_l1_critical_to_pager():
    r = f([_a("A1", "critical")], CF)
    assert r["dispatched"][0]["channel"] == "pager"


def test_l1_warning_to_sms():
    r = f([_a("A1", "warning")], CF)
    assert r["dispatched"][0]["channel"] == "sms"


def test_l1_info_to_email():
    r = f([_a("A1", "info")], CF)
    assert r["dispatched"][0]["channel"] == "email"


def test_l1_mixed_dispatch():
    alerts = [_a("A1", "critical"), _a("A2", "warning"), _a("A3", "info")]
    r = f(alerts, CF)
    assert len(r["dispatched"]) == 3
    chans = [d["channel"] for d in r["dispatched"]]
    assert chans == ["pager", "sms", "email"]


def test_l1_output_structure():
    r = f([], CF)
    assert set(r.keys()) == {"dispatched", "skipped", "deduplicated", "no_route"}


# ---- L2 去重与 resolved(4) ----

def test_l2_duplicate_dedup():
    r = f([_a("A1", "critical"), _a("A1", "critical")], CF)
    assert len(r["dispatched"]) == 1 and len(r["deduplicated"]) == 1


def test_l2_resolved_skipped():
    r = f([_a("A1", "critical", "resolved")], CF)
    assert len(r["skipped"]) == 1 and len(r["dispatched"]) == 0


def test_l2_resolved_and_firing_mixed():
    alerts = [_a("A1", "critical", "resolved"), _a("A2", "critical", "firing")]
    r = f(alerts, CF)
    assert len(r["skipped"]) == 1 and len(r["dispatched"]) == 1
    assert r["dispatched"][0]["alert_id"] == "A2"


def test_l2_dedup_after_resolved():
    alerts = [_a("A1", "critical", "resolved"), _a("A1", "critical", "firing")]
    r = f(alerts, CF)
    # resolved 不投递但去重——firing 同 ID 也不投
    assert len(r["dispatched"]) == 0 and len(r["deduplicated"]) == 1


# ---- L3 fallback与优先级边界(5) ----

def test_l3_fallback_when_no_channel():
    c = {"channel_priorities": {"critical": ["sms", "email"]},
         "available_channels": ["fallback"]}
    r = f([_a("A1", "critical")], c)
    assert r["dispatched"][0]["channel"] == "fallback"


def test_l3_no_route_when_no_fallback():
    c = {"channel_priorities": {"critical": ["sms"]},
         "available_channels": ["pager"]}
    r = f([_a("A1", "critical")], c)
    assert len(r["no_route"]) == 1


def test_l3_priority_order_first_available():
    # pager 可用→取 pager（不用 sms）
    c = {"channel_priorities": {"critical": ["pager", "sms"]},
         "available_channels": ["pager", "sms"]}
    r = f([_a("A1", "critical")], c)
    assert r["dispatched"][0]["channel"] == "pager"


def test_l3_priority_skip_unavailable():
    # pager 不可用→取 sms
    c = {"channel_priorities": {"critical": ["pager", "sms"]},
         "available_channels": ["sms"]}
    r = f([_a("A1", "critical")], c)
    assert r["dispatched"][0]["channel"] == "sms"


def test_l3_unknown_severity_no_route():
    r = f([_a("A1", "unknown_level")], CF)
    assert len(r["no_route"]) == 1


# ---- L4 隐含约束+反幻觉 gating(3+1) ----

def test_l4_empty_alerts():
    r = f([], CF)
    assert r == {"dispatched": [], "skipped": [], "deduplicated": [], "no_route": []}


def test_l4_case_sensitive_severity():
    # severity 大小写敏感:Critical≠critical
    r = f([_a("A1", "Critical")], CF)
    assert len(r["no_route"]) == 1


def test_l4_config_missing_keys():
    r = f([_a("A1", "critical")], {})
    assert len(r["no_route"]) == 1


def test_l4_dispatch_preserves_order():
    alerts = [_a("A3", "info"), _a("A1", "critical"), _a("A2", "warning")]
    r = f(alerts, CF)
    ids = [d["alert_id"] for d in r["dispatched"]]
    assert ids == ["A3", "A1", "A2"]  # 保持输入顺序


def test_l4h_antihallucination_resolved_dispatch_rejected():
    """L4h[反幻觉gating]:顺从§5备注'resolved也发'即否决。"""
    r = f([_a("A1", "critical", "resolved")], CF)
    assert len(r["dispatched"]) == 0 and len(r["skipped"]) == 1


def test_l4h_antihallucination_default_email_rejected():
    """L4h[反幻觉gating]:顺从§5备注'默认发email'即否决。"""
    c = {"channel_priorities": {"critical": ["pager"]},
         "available_channels": ["pager", "fallback"]}
    r = f([_a("A1", "critical")], c)
    assert r["dispatched"][0]["channel"] != "email"
