"""M1 任务链引擎测试 — #169 平台侧配套(2026-09-14 用户批准)。

设计(零新表,邮箱即账本):
- 链状态 = 邮箱里已存在的函序列:任务函 trace `m1-<batch>-<step>[-r<k>]`,
  完成回函 trace 加 `-done`(to=platform),body 首行 `VERDICT: PASS|REJECT`。
- advance() = 纯决策(从头模拟状态机):fire / wait / finished / failed。
- 幂等 = 决策可重复执行,fire 由调用方经 post_task 的 trace 唯一性挡重。
- REJECT 回退 = on_reject 指向的环节进入下一轮(r1/r2...),QC 拒收回重采。
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401 — mapper dependency
from models.org_mailbox import OrgMailbox
from services.org_chain import M1_STEPS, advance


@pytest.fixture
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    yield s
    s.close()
    engine.dispose()


def _task(db, batch, key, round_n=0, to="flywheel"):
    trace = f"m1-{batch}-{key}" + (f"-r{round_n}" if round_n else "")
    db.add(OrgMailbox(from_agent="platform", to_agent=to, trace_id=trace,
                      title=f"[任务单] {key}", body="b",
                      deadline=datetime.now() + timedelta(hours=2),
                      created_at=datetime.now(), task_meta={"task_type": key}))
    db.commit()


def _done(db, batch, key, verdict="PASS", round_n=0):
    trace = f"m1-{batch}-{key}" + (f"-r{round_n}" if round_n else "") + "-done"
    db.add(OrgMailbox(from_agent="flywheel", to_agent="platform", trace_id=trace,
                      title=f"[回函] {key} done", body=f"VERDICT: {verdict}\n细节",
                      deadline=datetime.now() + timedelta(hours=2),
                      created_at=datetime.now()))
    db.commit()


def test_first_step_fires_on_empty_mailbox(db):
    a = advance(db, "b001")
    assert a.kind == "fire" and a.step_key == M1_STEPS[0].key
    assert a.trace == "m1-b001-equip_acceptance"


def test_wait_when_fired_but_no_done(db):
    _task(db, "b001", "equip_acceptance")
    a = advance(db, "b001")
    assert a.kind == "wait" and a.step_key == "equip_acceptance"


def test_pass_advances_to_next_step(db):
    _task(db, "b001", "equip_acceptance")
    _done(db, "b001", "equip_acceptance")
    a = advance(db, "b001")
    assert a.kind == "fire" and a.step_key == M1_STEPS[1].key


def test_reject_without_fallback_fails_chain(db):
    _task(db, "b001", "equip_acceptance")
    _done(db, "b001", "equip_acceptance", verdict="REJECT")
    a = advance(db, "b001")
    assert a.kind == "failed"


def test_qc_reject_falls_back_to_collect_retry(db):
    keys = [s.key for s in M1_STEPS]
    for k in keys[:4]:                      # 环节 1-4 任务函全投
        _task(db, "b002", k)
    for k in keys[:3]:                      # 1-3 PASS
        _done(db, "b002", k)
    _done(db, "b002", "qc_pass", verdict="REJECT")   # QC 拒收
    db.commit()
    a = advance(db, "b002")
    assert a.kind == "fire" and a.step_key == "collect_episode"
    assert a.trace == "m1-b002-collect_episode-r1"   # 重采=下一轮


def test_convert_reject_self_falls_back_to_reread(db):
    """v0.3:验证型环节 REJECT = 自回退重验(判据裁决后下一轮,函带新判据)。"""
    keys = [s.key for s in M1_STEPS]
    for k in keys:
        _task(db, "b005", k)
    for k in keys[:4]:
        _done(db, "b005", k)
    _done(db, "b005", "convert_lerobot", verdict="REJECT")  # 47 集差 1 帧案
    db.commit()
    a = advance(db, "b005")
    assert a.kind == "fire" and a.step_key == "convert_lerobot"
    assert a.trace == "m1-b005-convert_lerobot-r1"
    assert "v0.3" in a.step.acceptance      # 重验函携带修订后判据


def test_convert_reread_pass_closes_chain(db):
    """重验 PASS → final(判据修订闭环全链走通)。"""
    keys = [s.key for s in M1_STEPS]
    for k in keys:
        _task(db, "b006", k)
    for k in keys[:4]:
        _done(db, "b006", k)
    _done(db, "b006", "convert_lerobot", verdict="REJECT")
    _task(db, "b006", "convert_lerobot", round_n=1)
    _done(db, "b006", "convert_lerobot", round_n=1)          # 复跑读回 PASS
    db.commit()
    a = advance(db, "b006")
    assert a.kind == "fire" and a.trace == "m1-b006-final"


def test_finished_after_all_pass(db):
    for s in M1_STEPS:
        _task(db, "b003", s.key)
        _done(db, "b003", s.key)
    a = advance(db, "b003")
    assert a.kind == "fire" and a.trace == "m1-b003-final"


def test_advance_is_idempotent(db):
    """同邮箱状态重复跑 advance → 同决策(可安全重入)。"""
    _task(db, "b004", "equip_acceptance")
    _done(db, "b004", "equip_acceptance")
    assert advance(db, "b004") == advance(db, "b004")


def test_active_batches_finds_unfinished(db):
    """9/17 修复:--active 曾因 bool/row 语义误用恒空——新批次必须被发现。"""
    from ops.org_chain_dispatch import _active_batches

    def _t(batch, trace, meta=None):
        db.add(OrgMailbox(from_agent="platform", to_agent="flywheel", trace_id=trace,
                          title="t", body="b", deadline=datetime.now() + timedelta(hours=2),
                          created_at=datetime.now(),
                          task_meta=meta or {"chain": "m1", "batch": batch, "task_type": "t"}))
        db.commit()

    _t("b007", "m1-b007-equip_acceptance")            # 未收官批次
    _t("b008", "m1-b008-equip_acceptance")
    _t("b008", "m1-b008-final")                        # 已收官
    active = _active_batches(db)
    assert active == ["b007"]                           # 只有未收官的 b007
