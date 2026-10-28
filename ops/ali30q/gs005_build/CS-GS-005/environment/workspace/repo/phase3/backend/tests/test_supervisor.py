"""supervisor 状态机测试 — dogfood 组件①(转移线①·设计 §3 预注册状态机)。"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "ops"))

from supervisor import classify, build_report  # noqa: E402


def test_active_when_evidence_fresh():
    assert classify("ACTIVE", has_evidence=True) == "ACTIVE"
    assert classify("ZERO", has_evidence=True) == "ACTIVE"  # 恢复即回 ACTIVE
    assert classify("CLAIM_ONLY", has_evidence=True) == "ACTIVE"


def test_claim_only_first_round():
    """有声明无实物 → 容忍 1 轮(PoC 时滞)。"""
    assert classify("ACTIVE", has_evidence=False) == "CLAIM_ONLY"
    assert classify("CLAIM_ONLY", has_evidence=False) == "ZERO"


def test_zero_persists_then_resets_on_evidence():
    assert classify("ZERO", has_evidence=False) == "ZERO"
    assert classify("ZERO", has_evidence=True) == "ACTIVE"


def test_zero_triggers_notify_flag():
    out = classify("CLAIM_ONLY", has_evidence=False, want_notify=True)
    assert out == "ZERO"


def test_report_jsonl_has_heartbeat_and_state(tmp_path):
    obs = {"sources": {"convergence": {"ok": True}, "git": {"ok": False}},
           "has_evidence": False}
    line = build_report(run_id="r1", state="CLAIM_ONLY", obs=obs)
    d = json.loads(line)
    assert d["schema"] == "supervisor-report-v1"
    assert d["state"] == "CLAIM_ONLY"
    assert d["heartbeat"] is True
    assert d["run_id"] == "r1"
    assert "ts" in d

# --- P0.5 mailbox 牙齿(2026-08-28 · org/bootstrap 设计 §3)---
def _mailbox_session(rows):
    import sqlalchemy as sa
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    import models.agent_survival  # noqa: F401  (mapper chain)
    from models.database import Base
    import models.org_mailbox as om
    eng = sa.create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(eng, tables=[om.OrgMailbox.__table__])
    s = sessionmaker(bind=eng)()
    from datetime import datetime, timedelta, timezone
    now = datetime.utcnow()
    for i, (title, dl_hours, acked, notified) in enumerate(rows, 1):
        s.add(om.OrgMailbox(
            id=i, from_agent="platform", to_agent="v5", trace_id=f"t-{i}",
            title=title, body="", deadline=now + timedelta(hours=dl_hours),
            ack_at=now if acked else None, notified_at=now if notified else None))
    s.commit()
    return s


def test_check_mailbox_notifies_only_due_unacked_unnotified(monkeypatch):
    import supervisor as sup
    import utils.database as dbm
    s = _mailbox_session([
        ("due-soon", 6, False, False),     # 应提醒
        ("far-away", 72, False, False),    # 未到期不提醒
        ("already-acked", 6, True, False), # 已回执不提醒
        ("already-notified", 6, False, True),  # 已提醒过不重发
    ])
    monkeypatch.setattr(dbm, "SessionLocal", lambda: s)
    sent = []
    monkeypatch.setattr(sup, "_send_telegram", lambda msg: sent.append(msg) or True)
    n = sup.check_mailbox()
    assert n == 1 and len(sent) == 1 and "due-soon" in sent[0]
    row = s.query(dbm_org_mailbox()).filter_by(title="due-soon").first()
    assert row.notified_at is not None


def dbm_org_mailbox():
    from models.org_mailbox import OrgMailbox
    return OrgMailbox


def test_check_mailbox_failsoft_when_db_down(monkeypatch):
    import supervisor as sup
    import utils.database as dbm
    def _boom():
        raise RuntimeError("db down")
    monkeypatch.setattr(dbm, "SessionLocal", _boom)
    monkeypatch.setattr(sup, "_send_telegram", lambda msg: True)
    assert sup.check_mailbox() == 0  # fail-soft 不抛
