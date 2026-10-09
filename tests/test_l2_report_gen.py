"""T5.2 · L2 报告生成器 v0 测试(2026-10-09 R436)。

判据(预注册,只许更严):
- G1 渲染零丢失: done 卡的全部 verdict_detail 字段原文出现在报告中
- G2 sha 一致: criteria_sha16 与 submission 原样呈现
- G3 人工槽位: L2-ANALYST 段存在,且带"未署名不得收费交付"声明
- G4 非 done 拒绝: status != done 时 render 拒绝(不出报告)
- G5 证据层标注保真: [实测]/[推断]/[不可验] 原样保留,生成器不加新断言
"""
import pytest

from l2_report_gen import render_report, validate_card

FAKE_CARD = {
    "ok": True,
    "id": "nautilus-l1-0002",
    "title": "L1 selftest-claude-code v1.0.0 · 平台自检单(管线首例)",
    "status": "done",
    "criteria_sha16": "5c8e0a7ce3a0048b",
    "verdict": "insufficient_evidence",
    "steps": [
        ["2026-10-08T12:01+08", "intake", "done"],
        ["2026-10-08T16:45+08", "card_issued", "done"],
    ],
    "verdict_detail": {
        "metadata": "[实测] repo=anthropics/claude-code HTTP 200(149820 stars)",
        "evaluation_evidence": "[实测缺失] 任务集读数=零;评测产物=零",
        "three_state": "insufficient_evidence —— 无可判读评测读数",
        "disposition": "不予收录;管线 intake→judging→delivered 首例走通",
    },
    "submission": "72fdcb665e79482b",
    "result_url": "/leaderboard.html",
}


def test_render_contains_all_fields():
    rpt = render_report(FAKE_CARD, generated_at="2026-10-09 21:00+08")
    for seg in FAKE_CARD["verdict_detail"].values():
        assert seg in rpt  # G1 零丢失
    assert FAKE_CARD["criteria_sha16"] in rpt  # G2
    assert FAKE_CARD["submission"] in rpt  # G2
    assert FAKE_CARD["verdict"] in rpt


def test_render_analyst_slot_unsigned():
    rpt = render_report(FAKE_CARD, generated_at="2026-10-09 21:00+08")
    assert "L2-ANALYST" in rpt  # G3
    assert "未署名" in rpt and "收费" in rpt  # 生成物≠可交付收费件


def test_render_draft_banner():
    rpt = render_report(FAKE_CARD, generated_at="2026-10-09 21:00+08")
    assert "草稿" in rpt  # 生成器产出=草稿


def test_evidence_tiers_preserved():
    rpt = render_report(FAKE_CARD, generated_at="2026-10-09 21:00+08")
    assert "[实测]" in rpt and "[实测缺失]" in rpt  # G5 原样


def test_validate_rejects_not_done():
    bad = dict(FAKE_CARD, status="pending")
    with pytest.raises(ValueError):
        validate_card(bad)  # G4


def test_validate_rejects_not_ok():
    bad = dict(FAKE_CARD, ok=False)
    with pytest.raises(ValueError):
        validate_card(bad)


def test_steps_timeline_rendered():
    rpt = render_report(FAKE_CARD, generated_at="2026-10-09 21:00+08")
    assert "intake" in rpt and "card_issued" in rpt
    assert "2026-10-08T12:01+08" in rpt
