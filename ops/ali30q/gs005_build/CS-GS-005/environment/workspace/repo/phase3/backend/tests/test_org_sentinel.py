"""组织值守哨兵测试 — 9/12 用户拍板 A(系统级非 LLM 值守,变化即飞书通知)。

事件面(最小,勿贪):
E1 to_agent=platform 的新函出现(通知一次,不催办——催办归 platform_loop)
E2 关注函集(WATCH_IDS)ack 翻转
无变化静默;首轮 baseline 建基线不逐条推。
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 — mapper dependency(Agent↔AgentSurvival)
from models.org_mailbox import OrgMailbox
from ops.org_sentinel import _baseline, collect_events, WATCH_IDS


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()
    engine.dispose()


def _letter(db, id, frm, to, acked=False, note=""):
    db.add(OrgMailbox(id=id, from_agent=frm, to_agent=to,
                      trace_id=f"t-{id}", title=f"函{id}", body="b",
                      deadline=datetime.now() + timedelta(hours=2),
                      created_at=datetime.now(),
                      ack_at=datetime.now() if acked else None,
                      ack_note=note if acked else None))
    db.commit()


def test_new_inbound_letter_emits_event_once(db):
    """E1:to=platform 新函出现→事件;已在 notified_ids→不再重复。人话格式。"""
    _letter(db, 300, "flywheel", "platform")
    _letter(db, 301, "v5", "platform")
    state = {"notified_ids": [301], "acked": {}}        # 301 已通知过
    events, new_state = collect_events(db, {**state, "done_reported": state.get("done_reported") or datetime.now().date().isoformat()})
    assert len(events) == 1 and "flywheel 来信" in events[0] and "函300" in events[0]
    assert new_state["notified_ids"] == [300, 301]      # 收编进已通知


def test_watch_ack_flip_emits_event(db):
    """E2:关注函(212)ack 翻转→事件含 ack_note 摘要;再跑不重复。"""
    _letter(db, 212, "platform", "flywheel", acked=True, note="已处理:派3单")
    events, _ = collect_events(db, {"notified_ids": [], "acked": {"212": False}, "done_reported": datetime.now().date().isoformat()})
    assert len(events) == 1 and "flywheel" in events[0] and "派3单" in events[0]

    state2 = {"notified_ids": [], "acked": {"212": True}}
    events2, _ = collect_events(db, state2)
    assert not [e for e in events2 if "确认" in e]      # 翻转只通知一次


def test_no_change_silent(db):
    """无变化→零事件(静默,值守不是轮询噪音)。"""
    _letter(db, 300, "flywheel", "platform")
    state = {"notified_ids": [300], "acked": {str(i): False for i in WATCH_IDS}}
    events, _ = collect_events(db, {**state, "done_reported": state.get("done_reported") or datetime.now().date().isoformat()})
    assert events == []


def test_outbound_letters_not_notified(db):
    """platform 发出的函(to=他框)不算'新回函'——E1 只看收件。"""
    _letter(db, 305, "platform", "v5")
    events, _ = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert events == []


def test_baseline_lists_pending_letters_with_detail(db):
    """9/14 事故修:baseline 必须列出待处理函明细——只报数量曾吞掉主线解锁事件。"""
    _letter(db, 300, "flywheel", "platform")
    _letter(db, 301, "v5", "platform")
    text, state = _baseline(db)
    assert "函300" in text and "函301" in text     # 明细必列,禁只报数量
    assert state["notified_ids"] == [300, 301]


def test_flywheel_head_change_emits_event_once(db):
    """E3:飞轮仓 HEAD 变化→事件一次;同 HEAD 重复跑不重复推。"""
    state = {"notified_ids": [], "acked": {},
             "frames": {"flywheel_head": "abc1oldcommit"}}
    events, s1 = collect_events(db, state, flywheel_head="def2newcommit")
    assert any("飞轮有新进展" in e for e in events)
    events2, _ = collect_events(db, s1, flywheel_head="def2newcommit")
    assert not [e for e in events2 if "飞轮" in e]       # 同 HEAD 静默


def test_flywheel_head_none_is_silent(db):
    """E3 数据源读不到(None)→不产生事件也不覆盖已存 HEAD(fail-open 不丢基线)。"""
    state = {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat(),
             "frames": {"flywheel_head": "abc1 old"}}
    events, s1 = collect_events(db, state, flywheel_head=None)
    assert events == []
    assert s1["frames"]["flywheel_head"] == "abc1 old"


# --- E4/E5 空转保险丝 v0(9/17:SLA 超时提醒+链停滞提醒) ---
def _task(db, id, to, batch, hours_offset, acked=False, final=False):
    trace = f"m1-{batch}-final" if final else f"m1-{batch}-step{id}"
    db.add(OrgMailbox(id=id, from_agent="platform", to_agent=to,
                      trace_id=trace, title=f"任务{id}", body="b",
                      deadline=datetime.now() + timedelta(hours=hours_offset),
                      created_at=datetime.now() - timedelta(hours=hours_offset + 5),
                      ack_at=datetime.now() if acked else None,
                      task_meta={"chain": "m1", "batch": batch, "task_type": "t"}))
    db.commit()


def test_e4_overdue_task_warns_once(db):
    _task(db, 400, "flywheel", "bX", hours_offset=-3)   # deadline 已过 3h
    events, st = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert any("任务超时" in e and "flywheel" in e for e in events)
    # 同函第二轮不再报
    events2, _ = collect_events(db, st)
    assert not any("任务超时" in e for e in events2)


def test_e4_finished_chain_no_overdue_noise(db):
    """收官链的历史任务函不追超时。final 函复刻 dispatch 真实形状:无 task_meta。"""
    from models.org_mailbox import OrgMailbox as OM
    _task(db, 401, "flywheel", "bF", hours_offset=-3)
    db.add(OM(from_agent="platform", to_agent="platform", trace_id="m1-bF-final",
              title="终报", body="b", deadline=datetime.now() + timedelta(hours=2),
              created_at=datetime.now()))
    db.commit()
    events, _ = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert not any("任务超时" in e for e in events)


def test_e5_stalled_chain_warns_once_per_day(db):
    _task(db, 410, "flywheel", "bS", hours_offset=1)     # 未超期未收官,最后函件 6h 前
    # 无 72h 停滞→只有 E4 类;构造停滞:created_at 由 hours_offset+5 控制,不够 72h
    events, _ = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert not any("链停滞" in e for e in events)
    # 直接塞一条 80h 前的链函
    from models.org_mailbox import OrgMailbox as OM
    db.add(OM(id=411, from_agent="platform", to_agent="flywheel",
              trace_id="m1-bS2-step911", title="老链", body="b",
              deadline=datetime.now() + timedelta(hours=48),
              created_at=datetime.now() - timedelta(hours=80),
              task_meta={"chain": "m1", "batch": "bS2", "task_type": "t"}))
    db.commit()
    events2, st2 = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert any("链停滞" in e and "bS2" in e for e in events2)
    events3, _ = collect_events(db, st2)
    assert not any("链停滞" in e for e in events3)       # 同日只提醒一次


def test_e4b_auto_urge_letter(db):
    """E4b:超时自动投催办函(trace 幂等,催办函无 task_meta 不自触发)。"""
    _task(db, 420, "flywheel", "bU", hours_offset=-2)
    events, st = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert any("任务超时" in e for e in events)
    urged = db.query(OrgMailbox).filter_by(trace_id="platform-urge-auto-420").first()
    assert urged is not None and urged.to_agent == "flywheel"
    assert urged.task_meta is None                       # 不自触发 E4
    events2, _ = collect_events(db, st)
    assert not any("任务超时" in e for e in events2)      # 幂等


def test_e4_json_null_meta_not_urged(db):
    """E4:task_meta=JSON null 标量(生产 569/570 形态,非 SQL NULL)——非任务函
    不提醒不催办。9/20 批量回执被误催实证:JSON null 过 SQL isnot(None) 过滤,
    Python 侧必须按"无 task_type 无 chain"挡下。"""
    from sqlalchemy import text
    db.execute(text(
        "INSERT INTO org_mailbox (id, from_agent, to_agent, trace_id, title, body, "
        "deadline, created_at, ack_at, task_meta) VALUES "
        "(569, 'platform', 'flywheel', 'platform-bulk-ack-1', '批量回执', 'b', "
        ":dl, :ca, NULL, 'null')"),
        {"dl": datetime.now() - timedelta(hours=1),
         "ca": datetime.now() - timedelta(hours=2)})
    db.commit()
    events, _ = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert not any("任务超时" in e for e in events)
    assert db.query(OrgMailbox).filter_by(trace_id="platform-urge-auto-569").first() is None


# --- E8 三臂降级保险丝(9/19 预注册规则自动化) ---
def _arm(db, uid, status="open"):
    from models.fde_dispatch import FdeDispatch
    db.add(FdeDispatch(task_uid=uid, title=uid, status=status,
                       created_at=datetime.now() - timedelta(hours=80)))
    db.commit()


def test_e8_arms_degrade_on_deadline_zero_claim(db, monkeypatch):
    """到期+prime/v7 六变体零认领→投降级函(含映射)+事件+state 标记幂等。"""
    import ops.org_sentinel as sen
    monkeypatch.setattr(sen, "ARMS_DEADLINE", datetime.now() - timedelta(hours=1))
    for i in (1, 2, 3):
        for a in ("prime", "v7"):
            _arm(db, f"exam3arm-q{i}-{a}")
    events, st = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert any("三臂降级" in e for e in events)
    letter = db.query(OrgMailbox).filter_by(trace_id="platform-3arm-degrade-2arm-20260922").first()
    assert letter is not None and "v5→ARM-C" in letter.body
    assert st.get("arms_degraded") is True
    # 第二轮(state 标记)不再重复
    events2, _ = collect_events(db, st)
    assert not any("三臂降级" in e for e in events2)


def test_e8_no_degrade_if_claimed(db, monkeypatch):
    """到期但有认领(半认领态)→不自动降级,提醒人工裁决。"""
    import ops.org_sentinel as sen
    monkeypatch.setattr(sen, "ARMS_DEADLINE", datetime.now() - timedelta(hours=1))
    _arm(db, "exam3arm-q1-prime", status="claimed")
    for a in ("prime", "v7"):
        for i in (2, 3):
            _arm(db, f"exam3arm-q{i}-{a}")
    _arm(db, "exam3arm-q1-v7")
    events, _ = collect_events(db, {"notified_ids": [], "acked": {}, "done_reported": datetime.now().date().isoformat()})
    assert not any("三臂降级:72h 零认领" in e for e in events)
    assert any("人工裁决" in e for e in events)
    assert db.query(OrgMailbox).filter_by(trace_id="platform-3arm-degrade-2arm-20260922").first() is None


