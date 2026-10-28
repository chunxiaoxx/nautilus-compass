"""S3 effect runner · FeishuDeliverySource 字段归一化(只测纯逻辑·monkeypatch 飞书 IO)。

read_expert_rates / read_passed_rows 把飞书原始 fields → 引擎期望的 std 行。
飞书 HTTP 本身不测(同 qc/delivery runner 惯例)·只锁字段映射不漂移。
"""
from services import fde_delivery_runner as R


def _src(**kw):
    return R.FeishuDeliverySource("tok", "app", "atbl", "dapp", "dtbl", "stbl", **kw)


def test_read_expert_rates_parses_roster_to_name_rate(monkeypatch):
    roster = [
        {"fields": {"姓名": "平台专家#1", "工时单价_元每小时": "300"}},
        {"fields": {"姓名": "王XX", "工时单价_元每小时": "500"}},
        {"fields": {"姓名": "", "工时单价_元每小时": "400"}},        # 缺名·跳过
    ]
    monkeypatch.setattr(R, "read_bitable_rows", lambda *a, **k: roster)
    rates = _src(roster_table="rtbl").read_expert_rates()
    assert rates == {"平台专家#1": 300.0, "王XX": 500.0}


def test_read_expert_rates_empty_when_no_roster_table(monkeypatch):
    monkeypatch.setattr(R, "read_bitable_rows", lambda *a, **k: [{"fields": {"姓名": "X", "工时单价_元每小时": "1"}}])
    assert _src().read_expert_rates() == {}                       # 未配 roster_table → 空名册


def test_read_expert_rates_reads_from_roster_app_not_assign(monkeypatch):
    """B2 路线3:名册在 canonical RGDK base(≠ assign_app)→ 用 roster_app 读。"""
    seen = {}

    def fake(fetch_page, token, app, table, _base):
        seen["app"], seen["table"] = app, table
        return [{"fields": {"姓名": "王XX", "工时单价_元每小时": "500"}}]

    monkeypatch.setattr(R, "read_bitable_rows", fake)
    rates = _src(roster_table="rtbl", roster_app="RGDK_app").read_expert_rates()
    assert rates == {"王XX": 500.0}
    assert seen["app"] == "RGDK_app"     # 从 RGDK 读·非 assign_app
    assert seen["table"] == "rtbl"


def test_roster_app_defaults_to_assign_app(monkeypatch):
    """roster_app 未配 → 回退 assign_app(向后兼容·名册与派活同 base)。"""
    seen = {}
    monkeypatch.setattr(R, "read_bitable_rows",
                        lambda *a, **k: seen.update(app=a[2], table=a[3]) or [])
    _src(roster_table="rtbl").read_expert_rates()
    assert seen["app"] == "app"           # = assign_app(_src 第2位参数)


def test_read_passed_rows_includes_hours(monkeypatch):
    items = [{"record_id": "rec1", "fields": {
        "task_uid": "expert_demo_001", "状态": "已通过",
        "指派专家": "平台专家#1", "工时": "6", "业务线": "2", "标题": "T"}}]
    monkeypatch.setattr(R, "read_bitable_rows", lambda *a, **k: items)
    rows = _src().read_passed_rows()
    assert rows[0]["hours"] == "6"
    assert rows[0]["assignee"] == "平台专家#1"
