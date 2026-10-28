"""platform_loop 纯函数测试 · TDD(协议 §4 SLA 执法判定)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "ops"))

from platform_loop import (  # noqa: E402
    classify_letters, daily_sections, escalation_body, match_replies,
    notify_message, reply_trace, telegram_allowed,
)

NOW = datetime(2026, 8, 31, 12, 0, 0)


def L(id_=1, to="v5", trace="t-1", title="T", deadline=None,
      notified_at=None, has_reply=False, ack_at=None):
    return dict(id=id_, to_agent=to, trace_id=trace, title=title,
                deadline=deadline or NOW - timedelta(hours=1),
                notified_at=notified_at, has_reply=has_reply, ack_at=ack_at,
                _created=NOW - timedelta(hours=2))


def test_resolved_by_reply_flag():
    v = classify_letters([L(has_reply=True)], NOW)
    assert v["resolved"] == 1 and not v["escalate"] and not v["takeover"]


def test_pending_before_deadline():
    v = classify_letters(
        [L(deadline=NOW + timedelta(hours=3))], NOW)
    assert v["pending"] == [1]


def test_escalate_overdue_not_notified():
    v = classify_letters([L()], NOW)
    assert len(v["escalate"]) == 1 and v["escalate"][0]["id"] == 1


def test_pending_within_grace_after_notified():
    # 已亮牌,超期但未超 2h grace → 等,不接管
    v = classify_letters(
        [L(notified_at=NOW - timedelta(minutes=90))], NOW)
    assert v["pending"] == [1] and not v["takeover"]


def test_takeover_after_grace():
    v = classify_letters(
        [L(notified_at=NOW - timedelta(hours=2, minutes=1))], NOW)
    assert len(v["takeover"]) == 1


def test_ack_terminates_sla_chain():
    # 实证 8/31 id64:flywheel ack 但未按 -reply 回函 → 不升级不接管
    v = classify_letters([L(ack_at=NOW - timedelta(hours=1))], NOW)
    assert v["acked"] == 1 and not v["escalate"] and not v["takeover"]


def test_ack_terminates_even_overdue_notified():
    v = classify_letters(
        [L(notified_at=NOW - timedelta(hours=5),
           ack_at=NOW - timedelta(minutes=10))], NOW)
    assert v["acked"] == 1 and not v["takeover"]


def test_reply_trace_suffix():
    assert reply_trace("org-protocol-20260831-v5") == \
        "org-protocol-20260831-v5-reply"


def test_escalation_body_contains_sla_terms():
    letter = L(title="复盘答卷", trace="retro-20260831-v5")
    body = escalation_body(letter, NOW)
    assert "retro-20260831-v5-reply" in body
    assert "L2 接管" in body and "SLA" in body
    # 回函通道约定(实证 8/31 #109 投仓根被误判零回执):自动函必带指引
    assert "只投 mailbox" in body and "仓根" in body


def test_mixed_batch_counts():
    letters = [L(id_=1, has_reply=True),
               L(id_=2, deadline=NOW + timedelta(hours=1)),
               L(id_=3),
               L(id_=4, notified_at=NOW - timedelta(hours=3))]
    v = classify_letters(letters, NOW)
    assert v["resolved"] == 1
    assert v["pending"] == [2]
    assert [x["id"] for x in v["escalate"]] == [3]
    assert [x["id"] for x in v["takeover"]] == [4]


def test_telegram_budget_first_of_day():
    # 空 state / 无当日记录 → 允许即时通知
    assert telegram_allowed({}, NOW) is True
    assert telegram_allowed({"notify": {"date": "2026-08-30", "count": 9}},
                            NOW) is True


def test_telegram_budget_exhausted_same_day():
    # 同 UTC 日已达 3 条 → 静默(告警疲劳护栏)
    assert telegram_allowed(
        {"notify": {"date": "2026-08-31", "count": 3}}, NOW) is False


def test_notify_message_merges_and_empty():
    assert notify_message([], []) is None
    msg = notify_message(["v5:t1"], ["compass:t2"])
    assert msg is not None and msg.startswith("[platform-loop]")
    assert "SLA 升级 1 封" in msg and "L2 接管候选 1 封" in msg


def R(id_, from_agent, trace, created, title=""):
    # 键结构与 load_platform_letters 生产 dict 一致(_created,教训 run#48)
    return dict(id=id_, from_agent=from_agent, trace_id=trace,
                _created=created, title=title)


def test_match_replies_recipient_reply_resolves():
    # 实证 8/31 缺口 16 封:收件方回函必须终止升级链
    orig = L(trace="q4a-pool-reopen-20260831")  # to=v5, 超期, 未亮牌
    letters = [orig]
    match_replies(letters, [R(99, "v5", "q4a-pool-reopen-20260831-reply",
                              NOW - timedelta(minutes=30))])
    assert orig["has_reply"] is True


def test_match_replies_ignores_platform_escalation():
    # 回归 8/31 #5:平台自发的 escalation 函不是回函(假 resolved)
    orig = L(trace="hook-verify-20260829", to="platform")
    letters = [orig]
    match_replies(letters, [R(55, "platform", "hook-verify-20260829-escalation",
                              NOW)])
    assert orig["has_reply"] is False


def test_match_replies_requires_recipient_and_time():
    orig = L(trace="t-x")
    match_replies(letters := [orig], [
        # 回函人不对(flywheel≠to=v5)→ 不算
        R(1, "flywheel", "t-x-reply", NOW),
        # 回函早于原函 → 不算
        R(2, "v5", "t-x-reply", NOW - timedelta(hours=5)),
    ])
    assert letters[0]["has_reply"] is False


def test_match_replies_title_reference_resolves():
    # 实证 9/1 #109:compass 回函 #114 trace 自拟
    # (compass-daemon-register-receipt-20260831),前缀不匹配,
    # 但标题"[回执·#109]"引用原函 id —— 引用同样构成回函证据
    orig = L(id_=109, to="compass",
             trace="daemon-register-claim-20260831-compass")
    letters = [orig]
    match_replies(letters, [R(114, "compass",
                              "compass-daemon-register-receipt-20260831",
                              NOW, title="[回执·#109] 注册完成")])
    assert orig["has_reply"] is True


def test_match_replies_title_reference_requires_recipient_and_time():
    orig = L(id_=109, to="compass",
             trace="daemon-register-claim-20260831-compass")
    match_replies(letters := [orig], [
        # 第三方引用 #109 不算(回函人必须是原收件人)
        R(1, "v5", "other-trace", NOW, title="回 #109 的事"),
        # 引用但早于原函 → 不算
        R(2, "compass", "other-trace", NOW - timedelta(hours=3),
          title="[回执·#109]"),
    ])
    assert letters[0]["has_reply"] is False


# ---------- 日报实体化(协议 §5:L1/L2/L3 从 mailbox 自动汇总) ----------

def DR(id_, from_agent, trace, created, title="T", body=""):
    # 日报行工厂:键结构与 load_platform_letters 生产 dict 一致
    return dict(id=id_, from_agent=from_agent, to_agent="x", trace_id=trace,
                title=title, body=body, _created=created)


def test_daily_sections_routes_by_priority():
    rows = [
        DR(1, "v5", "t-v5", NOW, title="[回报] crash-loop 死因诊断"),
        DR(2, "platform", "x-escalation", NOW, title="[SLA升级] 函A"),
        DR(3, "compass", "t-c", NOW, title="[提案] CPU 修复方案",
           body="三选一呈用户拍板"),
    ]
    v = daily_sections(rows, NOW, escalate=[], takeover=[])
    assert len(v["L1"]) == 1 and "v5" in v["L1"][0]
    assert len(v["L2"]) == 1 and "升级" in v["L2"][0]
    assert len(v["L3"]) == 1 and "compass" in v["L3"][0]


def test_daily_sections_l3_marked_in_title():
    # 标题带 [L3] 标记同样进拍板节(不依赖 body)
    rows = [DR(7, "flywheel", "t7", NOW, title="[提案][L3] 预算调整")]
    v = daily_sections(rows, NOW, [], [])
    assert len(v["L3"]) == 1 and not v["L1"] and not v["L2"]


def test_daily_sections_window_24h():
    rows = [DR(1, "v5", "old", NOW - timedelta(hours=30)),
            DR(2, "platform", "old2", NOW - timedelta(hours=30))]
    v = daily_sections(rows, NOW, escalate=[], takeover=[])
    assert not v["L1"] and not v["L2"] and not v["L3"]


def test_daily_sections_anomaly_lists_overdue():
    esc = [dict(id=5, to_agent="v5", trace_id="t-overdue")]
    v = daily_sections([], NOW, escalate=esc,
                       takeover=[dict(id=6, to_agent="compass",
                                      trace_id="t-takeover")])
    assert any("t-overdue" in x for x in v["异常"])
    assert any("t-takeover" in x for x in v["异常"])


def test_daily_sections_empty_day_has_placeholders():
    v = daily_sections([], NOW, escalate=[], takeover=[])
    assert v["L1"] == [] and v["L2"] == [] and v["L3"] == []
    assert v["异常"] == []


def test_daily_sections_l1_counts_inbound_letters():
    # 实证 9/1 生产 L1=0 假象:main() 误传 letters(仅 platform 函),
    # 修复后 rows=全表,各框来函必须出现在 L1
    rows = [DR(124, "v5", "t-diag", NOW, title="crash-loop 死因诊断"),
            DR(1, "platform", "t-x", NOW, title="[通知]")]
    v = daily_sections(rows, NOW, escalate=[], takeover=[])
    assert len(v["L1"]) == 1 and "#124" in v["L1"][0]


def test_daily_sections_l3_excludes_resolved():
    # 实证 9/1:#109/#110 已回函核销仍进 L3(resolved 件不是待拍板)
    rows = [DR(109, "platform", "t-done", NOW, title="[认领](用户拍板)",
               body=""), ]
    rows[0]["has_reply"] = True
    v = daily_sections(rows, NOW, escalate=[], takeover=[])
    assert not v["L3"] and len(v["L2"]) == 1


# ---------- 2026-09-10 · 时区回归(loop 时钟=Asia/Shanghai,对齐 org_mailbox naive 存储) ----------

def test_now_local_aligns_with_db_clock():
    # 修复前 main 用 utcnow,与 DB(Asia/Shanghai naive)差 8h → SLA 整体偏晚 8h(实案 206/207)
    from platform_loop import now_local
    assert abs((datetime.now() - now_local()).total_seconds()) < 300


def test_overdue_letter_escalates_on_local_clock():
    # 206 号实案:deadline=CST 21:27,loop 于 CST 22:30 跑 → 必须判 overdue 亮牌
    v = classify_letters(
        [L(deadline=datetime(2026, 9, 10, 21, 26, 58), notified_at=None)],
        datetime(2026, 9, 10, 22, 30, 0))
    assert len(v["escalate"]) == 1


def test_notified_at_is_read_as_db_clock():
    # 语义锁:字段一律按 DB 时钟读——notified=CST 11:30,22:30 跑 → 超过 grace 进 takeover
    v = classify_letters(
        [L(deadline=datetime(2026, 9, 10, 21, 26, 58),
           notified_at=datetime(2026, 9, 10, 11, 30, 53))],
        datetime(2026, 9, 10, 22, 30, 0))
    assert len(v["takeover"]) == 1
