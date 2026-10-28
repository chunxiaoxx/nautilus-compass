"""P2 完工即 ack(9/20 soul 卡轮修复:mailbox-522 每轮重选→skip→后续任务饿死)。"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

PHASE3 = Path(__file__).resolve().parent.parent.parent  # soul 包在 phase3/soul/
for p in (str(PHASE3), str(PHASE3 / "backend")):
    if p not in sys.path:
        sys.path.insert(0, p)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from models.database import Base
import models.agent_survival  # noqa: F401
from models.org_mailbox import OrgMailbox


@pytest.fixture
def db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    s = sessionmaker(bind=engine)()
    # soul.daemon 的 ack 用 SessionLocal——指到测试库
    from utils import database as dbmod
    monkeypatch.setattr(dbmod, "SessionLocal", lambda: s)
    s.add(OrgMailbox(id=522, from_agent="platform", to_agent="soul",
                      trace_id="t522", title="P1分诊", body="b",
                      deadline=datetime.now() + timedelta(hours=2),
                      created_at=datetime.now() - timedelta(hours=10)))
    s.commit()
    yield s
    engine.dispose()


def test_ack_p2_origin_marks_letter(db):
    from soul.daemon import _ack_p2_origin
    _ack_p2_origin("mailbox-522")
    row = db.query(OrgMailbox).filter_by(id=522).one()
    assert row.ack_at is not None
    assert "soul PR shipped" in row.ack_note


def test_ack_p2_origin_idempotent_and_scope_guard(db):
    from soul.daemon import _ack_p2_origin
    _ack_p2_origin("mailbox-522")
    first = db.query(OrgMailbox).filter_by(id=522).one().ack_at
    _ack_p2_origin("mailbox-522")  # 已 ack 不重复打
    assert db.query(OrgMailbox).filter_by(id=522).one().ack_at == first
    # 非 mailbox goal(自改进/yaml)不动信箱
    _ack_p2_origin("improve-tests")
    _ack_p2_origin("mailbox-notanumber")
    assert db.query(OrgMailbox).filter_by(id=522).one().ack_at == first
